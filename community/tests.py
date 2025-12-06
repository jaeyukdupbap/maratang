from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from unittest.mock import patch

# 모델들
from community.models import CommunityMeeting, MeetingSubmission, SubmissionMedia
from donation.models import DonationPool
from growth.models import PointsHistory, UserPet

# 테스트할 함수
from community.tasks import process_ai_verification

User = get_user_model()

class AiVerificationTest(TestCase):
    
    def setUp(self):
        """
        테스트 시작 전 기초 데이터 세팅
        """
        # [수정됨] email 인자를 추가했습니다.
        self.host = User.objects.create_user(
            username='host', 
            email='host@test.com',  # <--- 필수 필드 추가
            password='password'
        )
        
        # 포인트 초기화
        self.host.total_points = 0
        self.host.save()

        # 기부 풀 생성
        self.pool = DonationPool.objects.create(
            title='테스트 기부',
            goal_points=1000,
            current_points=0,
            status='open',
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

        # 모임 생성
        self.meeting = CommunityMeeting.objects.create(
            host_id=self.host,
            title='테스트 모임',
            description='테스트',
            location_name='서울',
            location_coords='0,0',
            meeting_date=timezone.now(),
            capacity=5
        )

        # 제출(Submission) 생성
        self.submission = MeetingSubmission.objects.create(
            meeting_id=self.meeting,
            host_id=self.host,
            status='pending'
        )

        # 이미지 파일 생성 (더미 데이터)
        dummy_data = b'fake_image_data'
        SubmissionMedia.objects.create(submission_id=self.submission, media_type='scene_photo', file=ContentFile(dummy_data, name='scene.jpg'))
        SubmissionMedia.objects.create(submission_id=self.submission, media_type='selfie', file=ContentFile(dummy_data, name='selfie.jpg'))

    @patch('community.tasks.analyze_images_similarity') 
    def test_ai_pass_scenario(self, mock_ai_function):
        """
        시나리오 1: AI가 높은 점수(0.9)를 줬을 때 -> 승인 및 포인트 지급 확인
        """
        # [Mocking] Gemini API가 0.9점을 리턴한다고 가정
        mock_ai_function.return_value = 0.9

        # 실행
        process_ai_verification(self.submission.submission_id)

        # 검증 (DB 새로고침)
        self.submission.refresh_from_db()
        self.host.refresh_from_db()
        self.pool.refresh_from_db()
        
        # 1. 상태가 ai_pass로 변했는가?
        self.assertEqual(self.submission.status, 'ai_pass')
        
        # 2. 호스트 포인트가 100점 올랐는가?
        self.assertEqual(self.host.total_points, 100)

        # 3. 기부 풀에도 100점이 쌓였는가?
        self.assertEqual(self.pool.current_points, 100)

        # 4. 펫 경험치가 올랐는가?
        # (펫이 자동 생성되었는지 확인)
        pet = UserPet.objects.get(user_id=self.host)
        self.assertEqual(pet.current_xp, 100)

    @patch('community.tasks.analyze_images_similarity')
    def test_ai_fail_scenario(self, mock_ai_function):
        """
        시나리오 2: AI가 낮은 점수(0.3)를 줬을 때 -> 보류(Pending) 상태 유지
        """
        # [Mocking] 0.3점 리턴한다고 가정
        mock_ai_function.return_value = 0.3

        # 실행
        process_ai_verification(self.submission.submission_id)

        # 검증
        self.submission.refresh_from_db()
        self.host.refresh_from_db()

        # 1. 상태가 pending으로 남아있는가?
        self.assertEqual(self.submission.status, 'pending')

        # 2. 포인트가 지급되지 않았는가?
        self.assertEqual(self.host.total_points, 0)