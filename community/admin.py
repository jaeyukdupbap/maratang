import os
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import CommunityMeeting, MeetingParticipant, MeetingSubmission, SubmissionMedia
from .tasks import grant_points_for_meeting
from notification.models import Notification

# =========================================================
# 1. 헬퍼 함수 (안전한 포맷팅을 위해 분리)
# =========================================================
def get_score_html(score):
    """점수를 받아서 색상이 적용된 HTML 문자열(SafeString)을 반환"""
    if score is None:
        return "-"
    
    try:
        # 1. 무조건 float로 변환하여 타입 오류 방지
        score_float = float(score)
        score_percent = score_float * 100
        
        # 2. 색상 결정
        color = '#28a745' if score_float >= 0.8 else '#ffc107'
        
        # 3. [핵심] 숫자를 먼저 문자열로 변환 (f-string 사용)
        # format_html 안에서 {:.1f}를 쓰지 않고, 밖에서 "85.2" 같은 문자열로 만듦
        percent_str = f"{score_percent:.1f}" 
        
        # 4. 단순 문자열 포맷팅으로 HTML 생성
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            percent_str
        )
    except (ValueError, TypeError):
        return "-"

# =========================================================
# 2. Admin 클래스 정의
# =========================================================

class SubmissionMediaInline(admin.TabularInline):
    """제출된 사진을 MeetingSubmission 페이지 안에서 바로 보기"""
    model = SubmissionMedia
    extra = 0
    readonly_fields = ['media_type', 'user_id', 'image_preview', 'ai_verification_info', 'created_at']
    fields = ['media_type', 'user_id', 'image_preview', 'ai_verification_info', 'file', 'created_at']

    def image_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 150px; border-radius: 5px;" /></a>',
                obj.file.url
            )
        return "No Image"
    image_preview.short_description = "미리보기"

    def ai_verification_info(self, obj):
        """AI 검증 정보 표시"""
        if obj.ai_verification_status == 'completed' and obj.ai_verification_score is not None:
            try:
                # 안전하게 float 변환
                score_val = float(obj.ai_verification_score)
                score_percent_str = f"{score_val * 100:.1f}"
                
                color = '#28a745' if score_val >= 0.8 else '#ffc107'
                
                return format_html(
                    '<div><strong style="color: {};">유사도: {}%</strong> ({}) <br/>'
                    '<small>검증: {}</small></div>',
                    color,
                    score_percent_str, # 미리 포맷팅된 문자열 전달
                    obj.get_ai_verification_status_display(),
                    obj.ai_verification_at.strftime('%Y-%m-%d %H:%M') if obj.ai_verification_at else '-'
                )
            except (ValueError, TypeError):
                return "점수 오류"
                
        elif obj.ai_verification_status in ['processing', 'pending']:
            return format_html(
                '<span style="color: #17a2b8;">{}</span>',
                obj.get_ai_verification_status_display()
            )
        elif obj.ai_verification_status == 'failed':
            return format_html(
                '<span style="color: #dc3545;">✗ {}</span>',
                obj.get_ai_verification_status_display()
            )
        return "검증 대기"
    ai_verification_info.short_description = "AI 검증 결과"


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
    list_display = ['submission_id', 'meeting_title', 'host_id', 'status_badge', 'ai_score_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['meeting_id__title', 'host_id__username', 'text_summary']
    readonly_fields = ['submission_id', 'created_at', 'processed_by', 'processed_at', 'ai_score_info']
    actions = ['approve_submission', 'reject_submission']
    
    inlines = [SubmissionMediaInline]

    fieldsets = (
        ('기본 정보', {
            'fields': ('meeting_id', 'host_id', 'status', 'created_at')
        }),
        ('제출 내용', {
            'fields': ('text_summary', 'admin_feedback')
        }),
        ('AI 검증 정보', {
            'fields': ('ai_score_info',),
            'classes': ('collapse',),
        }),
        ('관리자 처리 정보', {
            'fields': ('processed_by', 'processed_at')
        }),
    )

    def meeting_title(self, obj):
        return obj.meeting_id.title
    meeting_title.short_description = "모임명"

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'ai_pass': 'green',
            'admin_pass': 'blue',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = "상태"

    def ai_score_display(self, obj):
        """목록에서 AI 스코어 간략 표시"""
        # 가장 안전한 방법: 헬퍼 함수 사용
        media = SubmissionMedia.objects.filter(submission_id=obj, ai_verification_status='completed').first()
        if media:
            return get_score_html(media.ai_verification_score)
        return "-"
    ai_score_display.short_description = "AI 점수"

    def ai_score_info(self, obj):
        """상세 페이지에서 AI 검증 정보 표시"""
        media = SubmissionMedia.objects.filter(submission_id=obj)
        if not media:
            return "검증 대기"
        
        html_parts = []
        for m in media:
            media_label = "🏞️ 장소 사진" if m.media_type == 'scene_photo' else "🤳 셀카"
            
            if m.ai_verification_status == 'completed' and m.ai_verification_score is not None:
                # 여기서도 안전하게 선(先)포맷팅
                try:
                    score_val = float(m.ai_verification_score)
                    score_str = f"{score_val * 100:.1f}"
                    color = '#28a745' if score_val >= 0.8 else '#ffc107'
                    
                    html_parts.append(format_html(
                        '<div style="margin-bottom: 10px;"><strong>{}</strong><br/>'
                        'AI 유사도: <span style="color: {}; font-weight: bold;">{}%</span><br/>'
                        '검증 시간: {}</div>',
                        media_label,
                        color,
                        score_str, # 문자열 전달
                        m.ai_verification_at.strftime('%Y-%m-%d %H:%M:%S') if m.ai_verification_at else '-'
                    ))
                except:
                    html_parts.append("<div>점수 표시 오류</div>")

            elif m.ai_verification_status == 'failed':
                html_parts.append(format_html(
                    '<div style="margin-bottom: 10px;"><strong>{}</strong><br/>'
                    '<span style="color: #dc3545;">✗ AI 검증 실패</span></div>',
                    media_label
                ))
            else:
                html_parts.append(format_html(
                    '<div style="margin-bottom: 10px;"><strong>{}</strong><br/>'
                    '<span style="color: #17a2b8;">{}</span></div>',
                    media_label,
                    m.get_ai_verification_status_display()
                ))
        
        return mark_safe(''.join(html_parts)) if html_parts else "검증 대기"
    ai_score_info.short_description = "AI 검증 상세 정보"

    def approve_submission(self, request, queryset):
        """관리자 승인 처리"""
        count = 0
        for submission in queryset:
            if submission.status in ['admin_pass', 'rejected']:
                continue

            with transaction.atomic():
                submission.status = 'admin_pass'
                submission.processed_by = request.user
                submission.processed_at = timezone.now()
                submission.save()
                grant_points_for_meeting(submission.meeting_id)

                Notification.objects.create(
                    user_id=submission.host_id,
                    notification_type='admin_approved',
                    title='인증 승인',
                    message=f"관리자가 '{submission.meeting_id.title}' 모임 인증을 승인했습니다.",
                    related_meeting_id=submission.meeting_id
                )
                count += 1
        
        self.message_user(request, f'{count}개의 제출물이 승인 처리되었습니다. (포인트 지급 완료)')
    approve_submission.short_description = '✅ 선택된 제출물 승인 (포인트 지급)'
    
    def reject_submission(self, request, queryset):
        """관리자 반려 처리"""
        count = 0
        for submission in queryset:
            if submission.status == 'rejected':
                continue

            with transaction.atomic():
                submission.status = 'rejected'
                submission.processed_by = request.user
                submission.processed_at = timezone.now()
                if not submission.admin_feedback:
                    submission.admin_feedback = '사진 식별 불가 또는 부적절한 이미지입니다.'
                submission.save()

                Notification.objects.create(
                    user_id=submission.host_id,
                    notification_type='admin_rejected',
                    title='인증 반려',
                    message=f"'{submission.meeting_id.title}' 인증이 반려되었습니다. 사유: {submission.admin_feedback}",
                    related_meeting_id=submission.meeting_id
                )
                count += 1
        
        self.message_user(request, f'{count}개의 제출물이 반려되었습니다.')
    reject_submission.short_description = '⛔ 선택된 제출물 반려'


@admin.register(SubmissionMedia)
class SubmissionMediaAdmin(admin.ModelAdmin):
    list_display = ['media_id', 'submission_info', 'media_type', 'ai_status_badge', 'ai_score_cell', 'image_preview', 'created_at']
    list_filter = ['media_type', 'ai_verification_status', 'created_at']
    search_fields = ['submission_id__meeting_id__title', 'user_id__username']
    readonly_fields = ['media_id', 'image_preview_large', 'ai_verification_info', 'created_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('media_id', 'submission_id', 'user_id', 'media_type', 'created_at')
        }),
        ('이미지', {
            'fields': ('file', 'image_preview_large'),
        }),
        ('AI 검증', {
            'fields': ('ai_verification_status', 'ai_verification_score', 'ai_verification_at', 'ai_verification_info'),
        }),
    )
    
    def submission_info(self, obj):
        return f"{obj.submission_id.meeting_id.title} ({obj.submission_id.host_id.username})"
    submission_info.short_description = "관련 인증"

    def ai_status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.ai_verification_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_ai_verification_status_display()
        )
    ai_status_badge.short_description = "검증 상태"

    def ai_score_cell(self, obj):
        return get_score_html(obj.ai_verification_score)
    ai_score_cell.short_description = "유사도"

    def image_preview(self, obj):
        if obj.file:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 50px;" /></a>', obj.file.url)
        return ""
    image_preview.short_description = "미리보기"

    def image_preview_large(self, obj):
        if obj.file:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-width: 400px; border-radius: 5px;" /></a>',
                obj.file.url
            )
        return "No Image"
    image_preview_large.short_description = "이미지 (클릭하여 원본 확인)"

    def ai_verification_info(self, obj):
        if obj.ai_verification_status == 'completed' and obj.ai_verification_score is not None:
            try:
                # 1. 점수 계산 (안전하게 float 캐스팅)
                score_val = float(obj.ai_verification_score)
                score_percent_str = f"{score_val * 100:.2f}"
                score_raw_str = f"{score_val:.4f}"
                
                # 2. 임계값 계산 (settings 값이 문자열일 경우 대비하여 float 캐스팅)
                threshold_val = float(getattr(settings, 'AI_APPROVAL_THRESHOLD', 0.8))
                threshold_str = f"{threshold_val * 100:.0f}"
                
                color = '#28a745' if score_val >= threshold_val else '#ffc107'
                
                return format_html(
                    '<div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px;">'
                    '<strong>🎯 AI 유사도 점수:</strong> <span style="color: {}; font-weight: bold; font-size: 1.2em;">{}%</span><br/>'
                    '<strong>📊 상세 점수:</strong> {} (0.0 ~ 1.0 범위)<br/>'
                    '<strong>📋 기준값:</strong> {}%<br/>'
                    '<strong>⚖️ 판정:</strong> {}<br/>'
                    '<strong>🕐 검증 시간:</strong> {}'
                    '</div>',
                    color,
                    score_percent_str, # 문자열
                    score_raw_str,     # 문자열
                    threshold_str,     # 문자열
                    '✅ 자동 승인' if score_val >= threshold_val else '⚠️ 관리자 검토 필요',
                    obj.ai_verification_at.strftime('%Y-%m-%d %H:%M:%S') if obj.ai_verification_at else '-'
                )
            except (ValueError, TypeError):
                return "데이터 형식 오류"
                
        elif obj.ai_verification_status == 'failed':
            return format_html(
                '<div style="padding: 10px; background-color: #f8d7da; border-radius: 5px; color: #721c24;">'
                '<strong>❌ AI 검증 실패</strong><br/>'
                '💡 <em>가능한 원인:</em><br/>'
                '• API 연결 오류 또는 타임아웃<br/>'
                '• 이미지 형식 또는 크기 문제<br/>'
                '• Google API 할당량 초과<br/>'
                '</div>'
            )
        elif obj.ai_verification_status == 'processing':
            return format_html(
                '<div style="padding: 10px; background-color: #cfe2ff; border-radius: 5px; color: #084298;">'
                '⏳ AI 검증 진행 중입니다...<br/>'
                '<small>잠시 후 다시 새로고침해주세요</small>'
                '</div>'
            )
        else:
            return format_html(
                '<div style="padding: 10px; background-color: #d1ecf1; border-radius: 5px; color: #0c5460;">'
                '⏳ {}'
                '</div>',
                obj.get_ai_verification_status_display()
            )
    ai_verification_info.short_description = "AI 검증 결과"