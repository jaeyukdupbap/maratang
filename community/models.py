from django.db import models
from account.models import User

# Create your models here.

class CommunityMeeting(models.Model):
    """커뮤니티 모임 모델"""
    meeting_id = models.AutoField(primary_key=True)
    host_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_meetings', db_column='host_id')
    title = models.CharField(max_length=200)
    description = models.TextField()
    location_name = models.CharField(max_length=200)
    location_coords = models.CharField(max_length=100, help_text="Latitude,Longitude 형식")
    meeting_date = models.DateTimeField()
    capacity = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'community_meeting'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class MeetingParticipant(models.Model):
    """모임 참여자 모델"""
    participant_id = models.AutoField(primary_key=True)
    meeting_id = models.ForeignKey(CommunityMeeting, on_delete=models.CASCADE, related_name='participants', db_column='meeting_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participated_meetings', db_column='user_id')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'meeting_participant'
        unique_together = ['meeting_id', 'user_id']  # 같은 모임에 중복 참여 방지
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user_id.username} - {self.meeting_id.title}"


class MeetingSubmission(models.Model):
    """모임 인증 제출 모델"""
    STATUS_CHOICES = [
        ('pending', '검토 대기'),
        ('ai_pass', 'AI 승인'),
        ('admin_pass', '관리자 승인'),
        ('rejected', '반려'),
    ]
    
    submission_id = models.AutoField(primary_key=True)
    meeting_id = models.ForeignKey(CommunityMeeting, on_delete=models.CASCADE, related_name='submissions', db_column='meeting_id')
    host_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', db_column='host_id')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    text_summary = models.TextField(blank=True, null=True)
    admin_feedback = models.TextField(blank=True, null=True, help_text="반려 사유 등")
    created_at = models.DateTimeField(auto_now_add=True)
    # 관리자 처리 기록
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='processed_submissions', db_column='processed_by')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'meeting_submission'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.meeting_id.title} - {self.get_status_display()}"


class SubmissionMedia(models.Model):
    """제출 미디어 모델"""
    MEDIA_TYPE_CHOICES = [
        ('scene_photo', '장소 사진'),
        ('selfie', '셀카'),
    ]
    
    media_id = models.AutoField(primary_key=True)
    submission_id = models.ForeignKey(MeetingSubmission, on_delete=models.CASCADE, related_name='media_files', db_column='submission_id')
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submission_media', db_column='user_id', 
                                help_text="selfie일 때 해당 셀카의 사용자 ID, scene_photo일 때는 NULL")
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    # store uploaded file using Django storage (local MEDIA or configured S3/etc.)
    file = models.FileField(upload_to='submission_media/%Y/%m/%d/', max_length=500, null=True, blank=True,
                            help_text="업로드된 파일(로컬 또는 스토리지)")
    # 관리자 처리 정보 (누가 언제 처리했는지 감사용)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='processed_media', db_column='processed_by')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'submission_media'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.submission_id.meeting_id.title} - {self.get_media_type_display()}"
