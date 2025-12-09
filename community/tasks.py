"""
@Project : Mood Garden (Community & Donation Platform)
@File    : community/tasks.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-11-26 ~ 2025-11-30
@Description : AI 기반 모임 인증 검증 및 포인트 처리 로직. 이미지 유사도 분석, 자동 승인/거부, 포인트 분배 등을 담당합니다.
"""

import os
import logging
import json
from dotenv import load_dotenv
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from django.conf import settings

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

logger = logging.getLogger(__name__)
User = get_user_model()

# ==========================================
# 1. Utility Functions
# ==========================================

def _read_filefield_bytes(filefield):
    """
    FileField에서 바이트 데이터를 안전하게 읽어옵니다.
    
    Args:
        filefield (FileField): Django FileField 객체
        
    Returns:
        bytes: 파일 바이트 데이터, 실패 시 None
    """
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
    """
    관리자 검토 요청 알림 생성
    
    AI 검증 실패 시 관리자에게 알림을 전송합니다.
    
    Args:
        submission (MeetingSubmission): 검증 제출 객체
        reason (str): 검토 필요 사유
    """
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
    """
    Gemini AI를 이용한 이미지 유사도 분석
    
    장소 사진(Context/Location)과 셀카(Person) 이미지를 비교하여
    실제로 같은 장소에서 찍은 인증인지 검증합니다.
    
    Args:
        img_bytes_a (bytes): 장소 사진 바이트 데이터
        img_bytes_b (bytes): 셀카 바이트 데이터
        
    Returns:
        float: 유사도 점수 (0.0 ~ 1.0, 1.0이 완벽한 일치)
        
    Raises:
        RuntimeError: Google Genai 라이브러리 미설치
        ValueError: GEMINI_API_KEY 미설정
        json.JSONDecodeError: API 응답 파싱 실패
        Exception: AI 모델 호출 실패
    """
    load_dotenv()
    try:
        from google import genai
        from google.genai import types
    except ImportError as import_error:
        error_msg = "Google Genai 라이브러리 설치 필요: pip install google-genai"
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg) from import_error
    
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY 설정이 필요합니다.")
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Compare these two images carefully. "
            "1. Scene Photo (Context/Location) vs 2. Selfie (Person). "
            "Check if the selfie was taken at the same location/context as the scene photo. "
            "Ignore minor lighting differences. "
            "Return JSON: {\"similarity\": 0.85} where 1.0 is a perfect match."
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=[
                types.Part.from_bytes(data=img_bytes_a, mime_type='image/jpeg'),
                types.Part.from_bytes(data=img_bytes_b, mime_type='image/jpeg'),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # 응답 파싱
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)
        score = float(result.get("similarity", 0.0))
        return max(0.0, min(1.0, score))

    except Exception as e:
        logger.error(f"AI Analysis Failed: {e}")
        raise e


# ==========================================
# 3. Points & Logic (기존과 동일)
# ==========================================

def grant_points_for_meeting(meeting):
    """
    모임 참여자 및 호스트에게 포인트 지급
    
    모임이 완료되고 인증이 승인되면, 모든 참여자와 호스트에게 100포인트씩 지급합니다.
    동시에 포인트 히스토리 기록, 펫 경험치 증가, 알림 전송, 기부 풀 업데이트를 수행합니다.
    
    Args:
        meeting (CommunityMeeting): 완료된 모임 객체
        
    Returns:
        int: 생성된 총 포인트
    """
    points_per_person = 100
    total_points_generated = 0
    
    # 호스트와 모든 참여자 조회
    target_users = list(MeetingParticipant.objects.filter(meeting_id=meeting).values_list('user_id', flat=True))
    if meeting.host_id and meeting.host_id not in target_users:
        target_users.append(meeting.host_id)
    
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
            related_meeting_id=meeting 
        )
        total_points_generated += points_per_person
    update_donation_pool(total_points_generated)

def update_user_pet_xp(user, points):
    """
    사용자 펫 경험치 업데이트
    
    포인트 획득 시 펫의 경험치를 증가시킵니다.
    펫이 없으면 새로 생성합니다.
    
    Args:
        user (User): 사용자 객체
        points (int): 추가할 경험치
    """
    user_pet, created = UserPet.objects.get_or_create(
        user_id=user, defaults={'pet_type': 'otter', 'current_level': 1, 'current_xp': 0}
    )
    user_pet.current_xp += points
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
            user_id=user, notification_type='pet_levelup', title='레벨 업!',
            message=f"내 펫이 Lv.{user_pet.current_level}로 성장했습니다!"
        )

def update_donation_pool(points):
    """
    기부 풀 포인트 업데이트 및 자동 완료
    
    전체 포인트가 목표에 도달하면 기부 풀을 완료 상태로 변경합니다.
    
    Args:
        points (int): 추가할 포인트
    """
    active_pool = DonationPool.objects.filter(status='open').first()
    if not active_pool: return
    DonationPool.objects.filter(pool_id=active_pool.pool_id).update(current_points=F('current_points') + points)
    active_pool.refresh_from_db()
    if active_pool.current_points >= active_pool.goal_points:
        active_pool.status = 'completed'
        active_pool.completed_at = timezone.now()
        active_pool.save()
        create_donation_archive(active_pool)

def create_donation_archive(pool):
    """
    기부 완료 후 기부자 명예의 전당 생성
    
    기부 풀이 완료되면 참여한 모든 사용자의 기여도를 DonationHistory에 저장합니다.
    
    Args:
        pool (DonationPool): 완료된 기부 풀 객체
    """
    contributors = PointsHistory.objects.filter(created_at__gte=pool.created_at, points_change__gt=0)\
        .values('user_id').annotate(total_contribution=models.Sum('points_change'))
    history_entries = [DonationHistory(pool_id=pool, user_id_id=e['user_id'], contributed_points=e['total_contribution']) for e in contributors]
    if history_entries: DonationHistory.objects.bulk_create(history_entries)


# ==========================================
# 4. Main Process (핵심 수정 부분)
# ==========================================

def process_ai_verification(submission_id):
    """
    AI 기반 모임 인증 검증 메인 프로세스
    
    제출된 장소 사진과 셀카들을 Google Gemini AI로 분석하여 동일 장소 여부를 검증합니다.
    평균 유사도 점수가 80% 이상이면 자동 승인, 미만이면 관리자 검토 요청합니다.
    
    처리 과정:
    1. 제출 및 미디어 파일 조회
    2. 장소 사진 바이트 로드
    3. 각 셀카별 개별 AI 분석 수행
    4. 평균 점수 계산 및 최종 결과 판정
    5. 승인 시 포인트 지급, 거부 시 관리자 알림
    
    Args:
        submission_id (int): 검증할 MeetingSubmission ID
        
    Side Effects:
        - SubmissionMedia 테이블 업데이트 (ai_verification_score, ai_verification_status 등)
        - MeetingSubmission 테이블 업데이트 (status)
        - User 테이블 업데이트 (total_points)
        - PointsHistory, Notification 생성
        - DonationPool 업데이트 (필요 시)
    """
    
    try:
        submission = MeetingSubmission.objects.get(submission_id=submission_id)
    except MeetingSubmission.DoesNotExist:
        logger.error(f'Submission {submission_id} not found')
        return

    # 1. 파일 조회 (전체 가져오기)
    scene = SubmissionMedia.objects.filter(submission_id=submission, media_type='scene_photo').first()
    # [수정] .first() -> .all() 로 변경하여 모든 셀카 가져오기
    selfies = SubmissionMedia.objects.filter(submission_id=submission, media_type='selfie').all()

    if not scene or not selfies:
        print("❌ [ERROR] 필수 파일 부족 (장소 사진 또는 셀카 없음)")
        notify_admins_for_review(submission, reason="파일 부족")
        return

    print(f"✅ 장소 사진: 1장")
    print(f"✅ 셀카 사진: {len(selfies)}장 발견")

    # 2. 장소 사진 바이트 로드 (한 번만 수행)
    scene_bytes = _read_filefield_bytes(scene.file)
    if not scene_bytes:
        print("❌ [ERROR] 장소 사진 읽기 실패")
        notify_admins_for_review(submission, reason="장소 사진 오류")
        return

    # 3. 반복 검증 시작
    total_score = 0.0
    processed_count = 0
    
    # 장소 사진 상태는 일단 processing
    scene.ai_verification_status = 'processing'
    scene.save()

    print("\n🔄 각 셀카별 AI 분석 시작...")
    
    for idx, selfie in enumerate(selfies, 1):
        print(f"\n--- [셀카 #{idx}] 검증 중 ({selfie.file.name}) ---")
        
        selfie_bytes = _read_filefield_bytes(selfie.file)
        if not selfie_bytes:
            print(f"⚠️ 읽기 실패, 건너뜀")
            selfie.ai_verification_status = 'failed'
            selfie.save()
            continue

        try:
            # 1:1 비교 분석 호출
            score = analyze_images_similarity(scene_bytes, selfie_bytes)
            
            # 개별 셀카 결과 저장
            selfie.ai_verification_score = score
            selfie.ai_verification_status = 'completed'
            selfie.ai_verification_at = timezone.now()
            selfie.save()
            
            print(f"🎯 개별 점수: {score*100:.2f}%")
            
            total_score += score
            processed_count += 1
            
        except Exception as e:
            print(f"❌ 분석 에러: {e}")
            selfie.ai_verification_status = 'failed'
            selfie.save()

    # 4. 최종 결과 집계 (평균 점수 계산)
    print(f"\n{'='*70}")
    
    if processed_count == 0:
        print("❌ 유효한 분석 결과가 하나도 없습니다.")
        avg_score = 0.0
    else:
        avg_score = total_score / processed_count
    
    avg_percent = avg_score * 100
    threshold = getattr(settings, 'AI_APPROVAL_THRESHOLD', 0.8)
    threshold_percent = threshold * 100

    print(f"📊 최종 종합 결과 (총 {processed_count}장 평균)")
    print(f"{'='*70}")
    print(f"📈 평균 유사도: {avg_percent:.2f}%")
    
    # 장소 사진에도 대표(평균) 점수 저장 (관리자 확인용)
    scene.ai_verification_score = avg_score
    scene.ai_verification_status = 'completed'
    scene.ai_verification_at = timezone.now()
    scene.save()

    # 5. 승인/반려 결정
    if avg_score >= threshold:
        print(f"결과: ✅ 자동 승인 ({avg_percent:.2f}% >= {threshold_percent:.0f}%)")
        with transaction.atomic():
            submission.status = 'ai_pass'
            submission.save()
            grant_points_for_meeting(submission.meeting_id)
    else:
        print(f"결과: ⚠️ 관리자 검토 필요 ({avg_percent:.2f}% < {threshold_percent:.0f}%)")
        submission.status = 'pending'
        submission.save()
        notify_admins_for_review(submission, reason=f"평균 점수 미달: {avg_percent:.2f}%")

    print(f"{'='*70}\n")