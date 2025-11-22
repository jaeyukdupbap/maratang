"""
AI 인증 및 포인트 지급 로직
"""
from .models import MeetingSubmission, SubmissionMedia
from growth.models import PointsHistory, UserPet
from notification.models import Notification
from django.utils import timezone


def process_ai_verification(submission_id):
    """AI 인증 처리 (시뮬레이션)"""
    submission = MeetingSubmission.objects.get(submission_id=submission_id)
    
    # AI 검증 로직 (시뮬레이션)
    # 실제로는 이미지 분석, 좌표 비교, 셀카 매칭 등을 수행
    ai_result = simulate_ai_verification(submission)
    
    if ai_result['approved']:
        # AI 승인
        submission.status = 'ai_pass'
        submission.save()
        
        # 포인트 지급
        grant_points_for_meeting(submission.meeting_id)
        
        # 알림 전송
        Notification.objects.create(
            user_id=submission.host_id,
            notification_type='ai_approved',
            title='인증 자동 승인',
            message=f"'{submission.meeting_id.title}' 모임 인증이 자동 승인되었습니다."
        )
    else:
        # 관리자 검토 필요
        submission.status = 'pending'
        submission.save()
        
        # 알림 전송
        Notification.objects.create(
            user_id=submission.host_id,
            notification_type='admin_review',
            title='관리자 검토 대기',
            message=f"'{submission.meeting_id.title}' 모임 인증이 관리자 검토 대기 중입니다.",
            related_meeting_id=submission.meeting_id
        )


def simulate_ai_verification(submission):
    """AI 검증 시뮬레이션 (실제로는 AI 모델 사용)"""
    # 간단한 시뮬레이션: 80% 확률로 승인
    import random
    approved = random.random() > 0.2
    
    return {
        'approved': approved,
        'confidence': random.uniform(0.7, 0.95) if approved else random.uniform(0.3, 0.6)
    }


def grant_points_for_meeting(meeting):
    """모임 완료 시 포인트 지급"""
    from community.models import MeetingParticipant
    
    # 호스트와 참여자에게 포인트 지급
    participants = MeetingParticipant.objects.filter(meeting_id=meeting)
    points_per_person = 100
    
    # 호스트 포인트 지급
    host = meeting.host_id
    PointsHistory.objects.create(
        user_id=host,
        meeting_id=meeting,
        points_change=points_per_person,
        reason='admin_approval'  # 또는 'ai_approval'
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
        
        # XP 업데이트 및 레벨업 체크
        update_user_pet_xp(user, points_per_person)
        
        # 알림 전송
        Notification.objects.create(
            user_id=user,
            notification_type='points_earned',
            title='포인트 지급',
            message=f"'{meeting.title}' 모임 활동으로 {points_per_person} 포인트가 지급되었습니다.",
            related_meeting_id=meeting
        )
    
    # Donation Pool 업데이트
    update_donation_pool(points_per_person * (participants.count() + 1))


def update_user_pet_xp(user, points):
    """사용자 펫 XP 업데이트 및 레벨업"""
    try:
        user_pet = UserPet.objects.get(user_id=user)
        user_pet.current_xp += points
        
        # 레벨업 체크 (간단한 로직: 레벨당 100 XP 필요)
        xp_needed = user_pet.current_level * 100
        while user_pet.current_xp >= xp_needed:
            user_pet.current_xp -= xp_needed
            user_pet.current_level += 1
            xp_needed = user_pet.current_level * 100
        
        user_pet.save()
    except UserPet.DoesNotExist:
        # UserPet이 없으면 생성
        UserPet.objects.create(
            user_id=user,
            pet_type='otter',
            current_level=1,
            current_xp=points
        )


def update_donation_pool(points):
    """기부 풀 업데이트"""
    from donation.models import DonationPool
    
    # 현재 진행 중인 풀에 포인트 추가
    active_pools = DonationPool.objects.filter(status='open')
    for pool in active_pools:
        pool.current_points += points
        pool.save()
        
        # 목표 달성 체크
        if pool.current_points >= pool.goal_points:
            pool.status = 'completed'
            pool.completed_at = timezone.now()
            pool.save()
            
            # DonationHistory 생성
            create_donation_history(pool)


def create_donation_history(pool):
    """기부 명예의 전당 생성"""
    from donation.models import DonationHistory
    from growth.models import PointsHistory
    from django.db import models
    from account.models import User
    
    # 해당 풀 기간 동안의 포인트 기여 집계
    # 간단한 로직: 모든 사용자의 기여 포인트 집계
    for user in User.objects.all():
        # 해당 풀 기간 동안의 포인트 기여 계산
        # 실제로는 pool 생성일 이후의 포인트만 집계해야 함
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
            
            # 알림 전송
            Notification.objects.create(
                user_id=user,
                notification_type='donation_completed',
                title='기부 목표 달성',
                message=f"'{pool.title}' 기부 목표가 달성되었습니다! 명예의 전당을 확인하세요.",
                related_pool_id=pool
            )

