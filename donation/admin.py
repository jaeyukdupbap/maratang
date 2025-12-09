"""
@Project : Mood Garden (Community & Donation Platform)
@File    : donation/admin.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-01 ~ 2025-12-03
@Description : Django 관리자 페이지 - 기부 캠페인 및 기부자 관리
"""

from django.contrib import admin
from .models import DonationPool, DonationHistory

# Register your models here.

@admin.register(DonationPool)
class DonationPoolAdmin(admin.ModelAdmin):
    """
    기부 캠페인 관리자 클래스
    
    기부 목표, 현재 진행 상황, 캠페인 상태를 추적합니다.
    """
    list_display = ['pool_id', 'title', 'current_points', 'goal_points', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title']
    readonly_fields = ['pool_id', 'created_at']
    
    def get_progress_display(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress_display.short_description = '진행률'


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    """
    기부 명예의 전당 관리자 클래스
    
    기부 캠페인 완료 후 기부자별 기여도를 조회합니다.
    기부 기록은 읽기 전용입니다.
    """
    list_display = ['donation_id', 'pool_id', 'user_id', 'contributed_points', 'created_at']
    list_filter = ['created_at']
    search_fields = ['pool_id__title', 'user_id__username', 'user_id__email']
    readonly_fields = ['donation_id', 'created_at']
    ordering = ['-contributed_points', '-created_at']
