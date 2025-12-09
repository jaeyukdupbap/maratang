"""
@Project : Mood Garden (Community & Donation Platform)
@File    : notification/models.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-06
@Description : 사용자 알림 모델. AI 검증 결과, 포인트 지급, 기부 완료 등의 알림을 관리합니다.
"""

from django.db import models
from account.models import User

# Create your models here.

class Notification(models.Model):
    """
    알림 모델
    
    AI 검증 결과, 포인트 지급, 기부 목표 달성 등 다양한 이벤트에 대한 사용자 알림을 관리합니다.
    읽음 상태, 관련 모임/기부 풀 정보를 추적합니다.
    
    Attributes:
        notification_id (AutoField): 알림 ID (PK)
        user_id (ForeignKey): 알림 수신자
        notification_type (CharField): 알림 유형 (AI 승인, 관리자 검토, 포인트 지급 등)
        title (CharField): 알림 제목
        message (TextField): 알림 내용
        is_read (BooleanField): 읽음 상태
        related_meeting_id (ForeignKey): 관련 모임 (선택사항)
        related_pool_id (ForeignKey): 관련 기부 풀 (선택사항)
        created_at (DateTimeField): 생성 시간
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('ai_approved', 'AI 자동 승인'),
        ('admin_review', '관리자 검토 대기'),
        ('admin_rejected', '인증 반려'),
        ('points_earned', '포인트 지급'),
        ('donation_completed', '기부 목표 달성'),
    ]
    
    notification_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', db_column='user_id')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_meeting_id = models.ForeignKey('community.CommunityMeeting', on_delete=models.SET_NULL, 
                                          null=True, blank=True, related_name='notifications', db_column='related_meeting_id')
    related_pool_id = models.ForeignKey('donation.DonationPool', on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name='notifications', db_column='related_pool_id')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'is_read']),  # 읽지 않은 알림 조회 최적화
        ]
    
    def __str__(self):
        return f"{self.user_id.username} - {self.title}"
    
    @property
    def is_unread(self):
        """읽지 않은 알림 여부"""
        return not self.is_read
