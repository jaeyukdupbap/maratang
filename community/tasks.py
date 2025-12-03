"""
AI 인증 및 포인트 지급 로직

- Gemini(GenAI)를 우선 사용해 이미지 비교를 시도합니다(설정 필요).
- Gemini 호출이 불가능하거나 실패하면 Pillow 기반의 히스토그램 비교로 폴백합니다.
- 유사도 임계값(기본 0.8) 이상이면 자동 승인(`ai_pass`), 그렇지 않으면 `pending` 상태로 두고
  관리자에게 알림을 보냅니다. 관리자는 Django admin에서 직접 승인할 수 있습니다.
"""
import os
import io
import logging
import math
import base64

from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import MeetingSubmission, SubmissionMedia
from growth.models import PointsHistory, UserPet
from notification.models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()

try:
    from PIL import Image
except Exception:
    Image = None


def process_ai_verification(submission_id):
    """Process AI verification for a MeetingSubmission.

    Flow:
    1) Load scene photo and selfies attached to the submission.
    2) For each selfie, compute similarity against the scene image using
       Gemini (if enabled) or a local histogram fallback.
    3) If any selfie reaches the threshold (default 0.8) -> mark `ai_pass`,
       grant points and notify host.
       Otherwise -> set `pending`, notify host and admins for manual review.
    """
    try:
        submission = MeetingSubmission.objects.get(submission_id=submission_id)
    except MeetingSubmission.DoesNotExist:
        logger.exception('Submission not found: %s', submission_id)
        return

    # retrieve media
    scene = SubmissionMedia.objects.filter(submission_id=submission, media_type='scene_photo').first()
    selfies = SubmissionMedia.objects.filter(submission_id=submission, media_type='selfie')

    if not scene:
        logger.warning('No scene photo for submission %s', submission_id)
        submission.status = 'pending'
        submission.save()
        return

    scene_bytes = _read_filefield_bytes(scene.file)
    if scene_bytes is None:
        logger.warning('Unable to read scene photo for submission %s', submission_id)
        submission.status = 'pending'
        submission.save()
        return

    threshold = float(os.environ.get('AI_APPROVAL_THRESHOLD', 0.8))
    best_score = 0.0
    approved = False

    for selfie in selfies:
        selfie_bytes = _read_filefield_bytes(selfie.file)
        if selfie_bytes is None:
            continue

        try:
            score = analyze_images_similarity(scene_bytes, selfie_bytes)
        except Exception:
            logger.exception('Image similarity check failed for submission %s selfie %s', submission_id, selfie.media_id)
            score = 0.0

        best_score = max(best_score, score)
        if score >= threshold:
            approved = True
            break

    if approved:
        submission.status = 'ai_pass'
        submission.save()

        # 포인트 지급
        grant_points_for_meeting(submission.meeting_id)

        # 알림: 호스트
        Notification.objects.create(
            user_id=submission.host_id,
            notification_type='ai_approved',
            title='인증 자동 승인',
            message=f"'{submission.meeting_id.title}' 모임 인증이 자동 승인되었습니다. (유사도 {best_score:.2f})"
        )
    else:
        # 관리자 검토 필요
        submission.status = 'pending'
        submission.save()

        Notification.objects.create(
            user_id=submission.host_id,
            notification_type='admin_review',
            title='관리자 검토 대기',
            message=f"'{submission.meeting_id.title}' 모임 인증이 자동 검증에서 불일치했습니다. 관리자 검토가 필요합니다. (최고 유사도 {best_score:.2f})",
            related_meeting_id=submission.meeting_id
        )

        # notify admins
        try:
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    user_id=admin,
                    notification_type='admin_review_required',
                    title='모임 인증 검토 필요',
                    message=f"사용자 '{submission.host_id.username}'의 '{submission.meeting_id.title}' 인증이 자동 검증에서 불일치했습니다. 확인 후 승인해주세요.",
                    related_meeting_id=submission.meeting_id
                )
        except Exception:
            logger.exception('Failed to notify admins for submission %s', submission_id)


def _read_filefield_bytes(filefield):
    """Read bytes from a Django FileField (works for local and some storages).

    Returns bytes or None on failure.
    """
    try:
        filefield.open()
        data = filefield.read()
        filefield.close()
        return data
    except Exception:
        # fallback: try path-based read if available
        try:
            path = getattr(filefield, 'path', None)
            if path:
                with open(path, 'rb') as fh:
                    return fh.read()
        except Exception:
            return None
    return None


def analyze_images_similarity(img_bytes_a, img_bytes_b):
    """Return similarity score in [0.0, 1.0] between two images.

    Behavior:
    - If `USE_GEMINI` env var is set (true-like) and Google GenAI client is importable,
      attempt to call the model to compare images. The code makes a best-effort call
      shape; if the installed SDK differs it will fall back to the local method.
    - Fallback: use Pillow histogram RMS-based similarity (requires Pillow).
    """
    use_gemini = os.environ.get('USE_GEMINI', '').lower() in ('1', 'true', 'yes')

    if use_gemini:
        try:
            # Use the user's snippet-style Gemini/GenAI call shape.
            from google import genai
            from google.genai import types

            api_key = os.environ.get('GOOGLE_API_KEY')
            # prefer environment API key; if absent, rely on default auth
            client = genai.Client(api_key) if api_key else genai.Client()

            # Prepare contents: two image parts + instruction to return similarity
            parts = [
                types.Part.from_bytes(data=img_bytes_a, mime_type='image/jpeg'),
                types.Part.from_bytes(data=img_bytes_b, mime_type='image/jpeg'),
                'Compare the two images and return only a number between 0.0 and 1.0 representing similarity.'
            ]

            resp = client.models.generate_content(
                model=os.environ.get('GEMINI_MODEL', 'gemini-2.5-pro'),
                contents=parts
            )

            # Extract text from response; SDK formats vary so try common attrs
            text = getattr(resp, 'text', None) or getattr(resp, 'response', None) or str(resp)
            import re
            # match a decimal number like 0.85 or 1 or 0
            m = re.search(r"(1(?:\.0+)?|0(?:\.\d+)?|0?\.\d+)", text)
            if m:
                try:
                    val = float(m.group(1))
                    return max(0.0, min(1.0, val))
                except Exception:
                    pass
        except Exception:
            logger.exception('Gemini/GenAI call failed or not available; falling back to local compare')

    # Fallback method: Pillow histogram RMS difference -> similarity
    if Image is None:
        raise RuntimeError('Pillow is required for local image comparison fallback. Install pillow or enable Gemini.')

    a = Image.open(io.BytesIO(img_bytes_a)).convert('RGB').resize((256, 256))
    b = Image.open(io.BytesIO(img_bytes_b)).convert('RGB').resize((256, 256))

    ha = a.histogram()
    hb = b.histogram()

    sum_sq = 0.0
    for x, y in zip(ha, hb):
        d = x - y
        sum_sq += d * d

    rms = math.sqrt(sum_sq / len(ha))
    similarity = max(0.0, 1.0 - (rms / 255.0))
    return float(similarity)


def simulate_ai_verification(submission):
    """Legacy simulation fallback kept for tests (not used in production flow)."""
    import random
    approved = random.random() > 0.2
    return {'approved': approved, 'confidence': random.uniform(0.7, 0.95) if approved else random.uniform(0.3, 0.6)}


def grant_points_for_meeting(meeting):
    """모임 완료 시 포인트 지급 (기존 로직 그대로 유지)"""
    from community.models import MeetingParticipant

    participants = MeetingParticipant.objects.filter(meeting_id=meeting)
    points_per_person = 100

    # 호스트 포인트 지급
    host = meeting.host_id
    PointsHistory.objects.create(
        user_id=host,
        meeting_id=meeting,
        points_change=points_per_person,
        reason='admin_approval'
    )
    host.total_points += points_per_person
    host.save()

    # 참여자 포인트 지급
    for participant in participants:
        user = participant.user_id
        PointsHistory.objects.create(
            user_id=user,
            meeting_id=meeting,
            points_change=points_per_person,
            reason='meeting_participation'
        )
        user.total_points += points_per_person
        user.save()

        update_user_pet_xp(user, points_per_person)

        Notification.objects.create(
            user_id=user,
            notification_type='points_earned',
            title='포인트 지급',
            message=f"'{meeting.title}' 모임 활동으로 {points_per_person} 포인트가 지급되었습니다.",
            related_meeting_id=meeting
        )

    update_donation_pool(points_per_person * (participants.count() + 1))


def update_user_pet_xp(user, points):
    try:
        user_pet = UserPet.objects.get(user_id=user)
        user_pet.current_xp += points
        xp_needed = user_pet.current_level * 100
        while user_pet.current_xp >= xp_needed:
            user_pet.current_xp -= xp_needed
            user_pet.current_level += 1
            xp_needed = user_pet.current_level * 100
        user_pet.save()
    except UserPet.DoesNotExist:
        UserPet.objects.create(
            user_id=user,
            pet_type='otter',
            current_level=1,
            current_xp=points
        )


def update_donation_pool(points):
    from donation.models import DonationPool

    active_pools = DonationPool.objects.filter(status='open')
    for pool in active_pools:
        pool.current_points += points
        pool.save()
        if pool.current_points >= pool.goal_points:
            pool.status = 'completed'
            pool.completed_at = timezone.now()
            pool.save()
            create_donation_history(pool)


def create_donation_history(pool):
    from donation.models import DonationHistory
    from growth.models import PointsHistory
    from django.db import models
    from account.models import User

    for user in User.objects.all():
        contributed = PointsHistory.objects.filter(
            user_id=user,
            points_change__gt=0,
            created_at__gte=pool.created_at
        ).aggregate(total=models.Sum('points_change'))['total'] or 0

        if contributed > 0:
            DonationHistory.objects.get_or_create(
                pool_id=pool,
                user_id=user,
                defaults={'contributed_points': contributed}
            )

            Notification.objects.create(
                user_id=user,
                notification_type='donation_completed',
                title='기부 목표 달성',
                message=f"'{pool.title}' 기부 목표가 달성되었습니다! 명예의 전당을 확인하세요.",
                related_pool_id=pool
            )