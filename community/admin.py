from django.contrib import admin
from .models import CommunityMeeting, MeetingParticipant, MeetingSubmission, SubmissionMedia
from .tasks import grant_points_for_meeting
from notification.models import Notification

# Register your models here.

@admin.register(CommunityMeeting)
class CommunityMeetingAdmin(admin.ModelAdmin):
    list_display = ['meeting_id', 'title', 'host_id', 'meeting_date', 'capacity', 'created_at']
    list_filter = ['meeting_date', 'created_at']
    search_fields = ['title', 'description', 'location_name']
    readonly_fields = ['meeting_id', 'created_at']
    date_hierarchy = 'meeting_date'


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['participant_id', 'meeting_id', 'user_id', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['meeting_id__title', 'user_id__username', 'user_id__email']
    readonly_fields = ['participant_id', 'joined_at']


@admin.register(MeetingSubmission)
class MeetingSubmissionAdmin(admin.ModelAdmin):
    list_display = ['submission_id', 'meeting_id', 'host_id', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['meeting_id__title', 'host_id__username', 'text_summary']
    readonly_fields = ['submission_id', 'created_at']
    actions = ['approve_submission', 'reject_submission']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('meeting_id', 'host_id', 'status', 'created_at')
        }),
        ('제출 내용', {
            'fields': ('text_summary', 'admin_feedback')
        }),
    )
    
    def approve_submission(self, request, queryset):
        """관리자 승인 처리"""
        for submission in queryset:
            if submission.status == 'pending':
                submission.status = 'admin_pass'
                submission.save()
                
                # 포인트 지급
                grant_points_for_meeting(submission.meeting_id)
                
                # 알림 전송
                Notification.objects.create(
                    user_id=submission.host_id,
                    notification_type='ai_approved',
                    title='인증 승인',
                    message=f"'{submission.meeting_id.title}' 모임 인증이 승인되었습니다.",
                    related_meeting_id=submission.meeting_id
                )
        
        self.message_user(request, f'{queryset.count()}개의 제출물이 승인되었습니다.')
    approve_submission.short_description = '선택된 제출물 승인'
    
    def reject_submission(self, request, queryset):
        """관리자 반려 처리"""
        # 반려 사유 입력을 위한 별도 페이지로 리다이렉트하거나
        # 여기서 직접 처리할 수 있습니다.
        # 간단한 구현을 위해 admin_feedback 필드를 사용합니다.
        for submission in queryset:
            if submission.status == 'pending':
                submission.status = 'rejected'
                if not submission.admin_feedback:
                    submission.admin_feedback = '관리자에 의해 반려되었습니다.'
                submission.save()
                
                # 알림 전송
                Notification.objects.create(
                    user_id=submission.host_id,
                    notification_type='admin_rejected',
                    title='인증 반려',
                    message=f"'{submission.meeting_id.title}' 모임 인증이 반려되었습니다. (사유: {submission.admin_feedback})",
                    related_meeting_id=submission.meeting_id
                )
        
        self.message_user(request, f'{queryset.count()}개의 제출물이 반려되었습니다.')
    reject_submission.short_description = '선택된 제출물 반려'


@admin.register(SubmissionMedia)
class SubmissionMediaAdmin(admin.ModelAdmin):
    list_display = ['media_id', 'submission_id', 'media_type', 'user_id', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['submission_id__meeting_id__title', 'user_id__username']
    readonly_fields = ['media_id', 'created_at']
