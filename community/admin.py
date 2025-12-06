from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction
from django.utils import timezone

from .models import CommunityMeeting, MeetingParticipant, MeetingSubmission, SubmissionMedia
from .tasks import grant_points_for_meeting
from notification.models import Notification

# 1. 사진 미리보기를 위한 Inline 클래스 정의
class SubmissionMediaInline(admin.TabularInline):
    """제출된 사진을 MeetingSubmission 페이지 안에서 바로 보기"""
    model = SubmissionMedia
    extra = 0
    # 사진 수정은 불필요하므로 읽기 전용으로 설정
    readonly_fields = ['media_type', 'user_id', 'image_preview', 'created_at']
    fields = ['media_type', 'user_id', 'image_preview', 'file']

    def image_preview(self, obj):
        if obj.file:
            # 클릭하면 원본이 열리는 썸네일 표시
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 150px; border-radius: 5px;" /></a>',
                obj.file.url
            )
        return "No Image"
    image_preview.short_description = "미리보기"


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
    list_display = ['submission_id', 'meeting_title', 'host_id', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['meeting_id__title', 'host_id__username', 'text_summary']
    readonly_fields = ['submission_id', 'created_at', 'processed_by', 'processed_at']
    actions = ['approve_submission', 'reject_submission']
    
    # [중요] 사진을 여기서 바로 볼 수 있게 Inline 추가
    inlines = [SubmissionMediaInline]

    fieldsets = (
        ('기본 정보', {
            'fields': ('meeting_id', 'host_id', 'status', 'created_at')
        }),
        ('제출 내용', {
            'fields': ('text_summary', 'admin_feedback')
        }),
        ('관리자 처리 정보', {
            'fields': ('processed_by', 'processed_at')
        }),
    )

    def meeting_title(self, obj):
        return obj.meeting_id.title
    meeting_title.short_description = "모임명"

    def status_badge(self, obj):
        """상태를 색상으로 구분하여 표시"""
        colors = {
            'pending': 'orange',
            'ai_pass': 'green',
            'admin_pass': 'blue',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = "상태"

    # --- 승인 로직 ---
    def approve_submission(self, request, queryset):
        """관리자 승인 처리"""
        count = 0
        for submission in queryset:
            # 이미 승인된 건은 중복 처리 방지
            if submission.status in ['ai_pass', 'admin_pass']:
                continue

            with transaction.atomic():
                submission.status = 'admin_pass'
                submission.processed_by = request.user
                submission.processed_at = timezone.now()
                submission.save()

                # 포인트 지급
                grant_points_for_meeting(submission.meeting_id)

                # 알림 전송
                Notification.objects.create(
                    user_id=submission.host_id,
                    notification_type='admin_approved',
                    title='인증 승인',
                    message=f"관리자가 '{submission.meeting_id.title}' 모임 인증을 승인했습니다.",
                    related_meeting_id=submission.meeting_id
                )
                count += 1
        
        self.message_user(request, f'{count}개의 제출물이 승인 처리되었습니다.')
    approve_submission.short_description = '✅ 선택된 제출물 승인 (포인트 지급)'
    
    # --- 반려 로직 ---
    def reject_submission(self, request, queryset):
        """관리자 반려 처리"""
        count = 0
        for submission in queryset:
            # 이미 반려된 건은 건너뜀
            if submission.status == 'rejected':
                continue

            with transaction.atomic():
                submission.status = 'rejected'
                submission.processed_by = request.user
                submission.processed_at = timezone.now()
                
                # 반려 사유가 없으면 기본 메시지 입력
                if not submission.admin_feedback:
                    submission.admin_feedback = '사진 식별 불가 또는 부적절한 이미지입니다.'
                
                submission.save()

                # 알림 전송
                Notification.objects.create(
                    user_id=submission.host_id,
                    notification_type='admin_rejected',
                    title='인증 반려',
                    message=f"'{submission.meeting_id.title}' 인증이 반려되었습니다. 사유: {submission.admin_feedback}",
                    related_meeting_id=submission.meeting_id
                )
                count += 1
        
        self.message_user(request, f'{count}개의 제출물이 반려되었습니다. (유저에게 알림 발송됨)')
    reject_submission.short_description = '⛔ 선택된 제출물 반려'


@admin.register(SubmissionMedia)
class SubmissionMediaAdmin(admin.ModelAdmin):
    """미디어 파일 개별 관리 (보통은 위 Inline에서 보지만, 따로 필요할 경우를 위해 유지)"""
    list_display = ['media_id', 'submission_info', 'media_type', 'image_preview', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['submission_id__meeting_id__title', 'user_id__username']
    
    def submission_info(self, obj):
        return f"{obj.submission_id.meeting_id.title} ({obj.submission_id.host_id.username})"
    submission_info.short_description = "관련 인증"

    def image_preview(self, obj):
        if obj.file:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 50px;" /></a>', obj.file.url)
        return ""
    image_preview.short_description = "사진" 