import os
import logging
import json
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
# 1. Community Models
from community.models import (
    MeetingSubmission, SubmissionMedia, MeetingParticipant
)
# 2. Donation Models
from donation.models import DonationPool, DonationHistory
# 3. Growth Models
from growth.models import PointsHistory, UserPet
# Notification Model
from notification.models import Notification

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
User = get_user_model()

# ==========================================
# 1. Utility Functions
# ==========================================

def _read_filefield_bytes(filefield):
    """FileField에서 바이트 데이터를 안전하게 읽어옵니다."""
    try:
        with filefield.open('rb') as f:
            return f.read()
    except Exception:
        try:
            path = getattr(filefield, 'path', None)
            if path:
                with open(path, 'rb') as fh:
                    return fh.read()
        except Exception:
            pass
    return None

def notify_admins_for_review(submission, reason):
    """관리자 검토 요청 알림"""
    try:
        admins = User.objects.filter(is_staff=True)
        notifications = [
            Notification(
                user_id=admin,
                notification_type='admin_review_required',
                title='⚠ 모임 인증 검토 필요',
                message=f"'{submission.meeting_id.title}' 인증 건 확인이 필요합니다. 사유: {reason}",
                related_meeting_id=submission.meeting_id 
            ) for admin in admins
        ]
        Notification.objects.bulk_create(notifications)
    except Exception:
        logger.exception('Failed to notify admins')


# ==========================================
# 2. AI & Image Analysis
# ==========================================

def analyze_images_similarity(img_bytes_a, img_bytes_b):
    """Gemini 3.0 Pro를 이용한 이미지 유사도 분석"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY is missing.")
        raise ValueError("API Key not found")

    client = genai.Client(api_key=api_key)
    
    prompt = (
        "Compare these two images. "
        "Are they taken at the same location or context? "
        "Ignore minor differences in lighting or angles. "
        "Return only a single float number between 0.0 (different) and 1.0 (same). "
        "Strictly return JSON format: {\"similarity\": 0.85}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.0-pro",
            contents=[
                types.Part.from_bytes(data=img_bytes_a, mime_type='image/jpeg'),
                types.Part.from_bytes(data=img_bytes_b, mime_type='image/jpeg'),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        import json
        result = json.loads(response.text)
        score = float(result.get("similarity", 0.0))
        return max(0.0, min(1.0, score))

    except Exception as e:
        logger.exception(f"Gemini API Call Failed: {e}")
        raise e


# ==========================================
# 3. Points & Pet & Donation Logic
# ==========================================

def grant_points_for_meeting(meeting):
    """
    모임 완료 후 포인트 지급 및 관련 데이터(펫, 기부) 업데이트
    """
    points_per_person = 100
    
    participants = list(MeetingParticipant.objects.filter(meeting_id=meeting).select_related('user_id'))
    
    target_users = [p.user_id for p in participants]
    target_users.append(meeting.host_id)
    target_users = list(set(target_users))

    total_points_generated = 0

    with transaction.atomic():
        for user in target_users:
            PointsHistory.objects.create(
                user_id=user,
                meeting_id=meeting,
                points_change=points_per_person,
                reason='meeting_participation' if user != meeting.host_id else 'admin_approval'
            )
            
            User.objects.filter(id=user.id).update(total_points=F('total_points') + points_per_person)
            update_user_pet_xp(user, points_per_person)

            Notification.objects.create(
                user_id=user,
                notification_type='points_earned',
                title='포인트 지급',
                message=f"'{meeting.title}' 모임 완료! {points_per_person}P가 지급되었습니다.",
                # [수정] meeting.meeting_id (숫자) -> meeting (객체)
                related_meeting_id=meeting 
            )
            
            total_points_generated += points_per_person

        update_donation_pool(total_points_generated)


def update_user_pet_xp(user, points):
    """펫 경험치 증가 및 레벨업 로직"""
    # 펫이 없으면 기본 'otter' 생성
    user_pet, created = UserPet.objects.get_or_create(
        user_id=user,
        defaults={'pet_type': 'otter', 'current_level': 1, 'current_xp': 0}
    )
    
    user_pet.current_xp += points
    
    # max_xp는 프로퍼티이므로 계산식 직접 사용: (level + 1) * 100
    xp_needed = (user_pet.current_level + 1) * 100
    
    level_up = False
    while user_pet.current_xp >= xp_needed:
        user_pet.current_xp -= xp_needed
        user_pet.current_level += 1
        level_up = True
        xp_needed = (user_pet.current_level + 1) * 100
    
    user_pet.save()

    if level_up:
        Notification.objects.create(
            user_id=user,
            notification_type='pet_levelup',
            title='레벨 업!',
            message=f"내 펫이 Lv.{user_pet.current_level}로 성장했습니다!"
        )


def update_donation_pool(points):
    """기부 풀 게이지 증가"""
    active_pool = DonationPool.objects.filter(status='open').first()
    if not active_pool:
        return

    # F객체로 안전하게 업데이트
    DonationPool.objects.filter(pool_id=active_pool.pool_id).update(
        current_points=F('current_points') + points
    )
    
    # 완료 여부 체크를 위해 다시 조회
    active_pool.refresh_from_db()
    
    if active_pool.current_points >= active_pool.goal_points:
        active_pool.status = 'completed'
        active_pool.completed_at = timezone.now()
        active_pool.save()
        create_donation_archive(active_pool)


def create_donation_archive(pool):
    """기부 완료 시 기여자 명단(DonationHistory) 박제"""
    # 이 풀이 열린 기간 동안 포인트를 획득한 모든 유저의 총합 계산
    # (단순화를 위해 created_at 이후 획득한 모든 포인트를 기여도로 산정)
    contributors = (
        PointsHistory.objects
        .filter(created_at__gte=pool.created_at, points_change__gt=0)
        .values('user_id')
        .annotate(total_contribution=models.Sum('points_change'))
    )

    history_entries = []
    notifications = []

    for entry in contributors:
        user_id = entry['user_id']
        amount = entry['total_contribution']
        
        history_entries.append(DonationHistory(
            pool_id=pool,
            user_id_id=user_id,
            contributed_points=amount
        ))
        
        notifications.append(Notification(
            user_id_id=user_id,
            notification_type='donation_completed',
            title='기부 목표 달성!',
            message=f"'{pool.title}' 목표 달성! 명예의 전당에 등록되었습니다."
        ))

    if history_entries:
        DonationHistory.objects.bulk_create(history_entries)
    if notifications:
        Notification.objects.bulk_create(notifications)


# ==========================================
# 4. Main Process Entrypoint
# ==========================================

def process_ai_verification(submission_id):
    """AI 검증 메인 함수"""
    try:
        submission = MeetingSubmission.objects.get(submission_id=submission_id)
    except MeetingSubmission.DoesNotExist:
        logger.exception('Submission not found: %s', submission_id)
        return

    scene = SubmissionMedia.objects.filter(submission_id=submission, media_type='scene_photo').first()
    selfie = SubmissionMedia.objects.filter(submission_id=submission, media_type='selfie').first()

    if not scene or not selfie:
        submission.status = 'pending'
        submission.save()
        return

    # Bytes 읽기
    scene_bytes = _read_filefield_bytes(scene.file)
    selfie_bytes = _read_filefield_bytes(selfie.file)

    if not scene_bytes or not selfie_bytes:
        submission.status = 'pending'
        submission.save()
        return

    # AI 분석
    try:
        score = analyze_images_similarity(scene_bytes, selfie_bytes)
    except Exception:
        # 에러 시 Pending
        submission.status = 'pending'
        submission.save()
        notify_admins_for_review(submission, reason="AI Service Error")
        return

    threshold = float(os.environ.get('AI_APPROVAL_THRESHOLD', 0.8))
    
    if score >= threshold:
        # 승인 및 포인트 지급
        with transaction.atomic():
            submission.status = 'ai_pass'
            submission.save()
            grant_points_for_meeting(submission.meeting_id)
    else:
        # 보류
        submission.status = 'pending'
        submission.save()
        notify_admins_for_review(submission, reason=f"Low Score: {score:.2f}")