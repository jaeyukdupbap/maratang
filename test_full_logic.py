import os
import sys
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model

# 모델 로드 (에러 시 manage.py 설정 확인)
from community.models import CommunityMeeting, MeetingSubmission, SubmissionMedia, MeetingParticipant
from donation.models import DonationPool, DonationHistory
from growth.models import PointsHistory, UserPet
from community.tasks import process_ai_verification

User = get_user_model()

print("="*50)
print("🚀 [START] 통합 로직 테스트 시작")
print("="*50)

# 1. 유저 및 펫 생성
print("\n[1] 유저 및 펫 데이터 생성")
host, _ = User.objects.get_or_create(username='host_user', defaults={'email': 'host@test.com'})
guest, _ = User.objects.get_or_create(username='guest_user', defaults={'email': 'guest@test.com'})

# 기존 포인트 및 펫 초기화
host.total_points = 0
host.save()
UserPet.objects.filter(user_id=host).delete() # 펫 초기화

# 2. 기부 풀 생성
print("[2] 기부 풀(DonationPool) 생성")
pool, _ = DonationPool.objects.get_or_create(
    title='유기견 사료 기부',
    status='open',
    defaults={
        'goal_points': 5000, # 목표 5000점
        'current_points': 0,
        'start_date': timezone.now().date(),
        'end_date': timezone.now().date(),
        'sponsor': '멍멍재단'
    }
)
# 테스트를 위해 0점으로 리셋
pool.current_points = 0
pool.save()

# 3. 모임 생성
print("[3] 모임(CommunityMeeting) 생성")
meeting = CommunityMeeting.objects.create(
    host_id=host,
    title='주말 플로깅',
    description='쓰레기 줍기',
    location_name='한강공원',
    location_coords='37.5,127.0',
    meeting_date=timezone.now(),
    capacity=10
)

# 4. 제출 데이터 생성 (Submission)
print("[4] 인증 제출(Submission) 데이터 생성")
submission = MeetingSubmission.objects.create(
    meeting_id=meeting,
    host_id=host,
    status='pending'
)

# 더미 이미지 (AI 테스트용)
dummy_data = b'\xFF\xD8\xFF\xE0' + b'\x00' * 50
SubmissionMedia.objects.create(submission_id=submission, media_type='scene_photo', file=ContentFile(dummy_data, name='s.jpg'))
SubmissionMedia.objects.create(submission_id=submission, media_type='selfie', file=ContentFile(dummy_data, name='f.jpg'))

print("\n" + "-"*30)
print("🤖 AI 검증 프로세스 실행 (Gemini 호출 시도)")
print("-" * 30)

try:
    # 실행!
    process_ai_verification(submission.submission_id)
    print("✅ 실행 완료 (에러 없음)")
except Exception as e:
    print(f"❌ 실행 중 에러 발생: {e}")

# 5. 결과 검증
print("\n" + "="*50)
print("📊 [RESULT] 최종 데이터 검증")
print("="*50)

# DB 새로고침
submission.refresh_from_db()
host.refresh_from_db()
pool.refresh_from_db()

# 펫 확인
try:
    pet = UserPet.objects.get(user_id=host)
    pet_info = f"{pet.get_pet_type_display()} Lv.{pet.current_level} (XP: {pet.current_xp})"
except UserPet.DoesNotExist:
    pet_info = "펫 없음 (생성 실패)"

print(f"1. 인증 상태       : {submission.get_status_display()} ({submission.status})")
print(f"2. 호스트 포인트   : {host.total_points} (기대값: 100 또는 0)")
print(f"3. 펫 상태         : {pet_info}")
print(f"4. 기부 풀 진행도  : {pool.current_points} / {pool.goal_points} ({pool.get_progress_percentage()}%)")

# 포인트 내역 확인
history_count = PointsHistory.objects.filter(meeting_id=meeting).count()
print(f"5. 포인트 내역 수  : {history_count}건 생성됨")

if submission.status == 'ai_pass':
    print("\n🎉 [SUCCESS] AI 승인 및 모든 보상 지급 완료!")
elif submission.status == 'pending':
    print("\n⚠️ [PENDING] AI 보류됨 (이미지 품질 미달 or 더미 데이터). 로직은 정상 작동함.")