"""
@Project : Mood Garden (Community & Donation Platform)
@File    : account/admin.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-11-25
@Description : Django 관리자 페이지 - 사용자 계정 관리
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    사용자 계정 관리 어드민 클래스
    
    Attributes:
        list_display (tuple): 목록에 표시할 필드
        list_filter (tuple): 필터링 옵션
        search_fields (tuple): 검색 가능 필드
        ordering (list): 기본 정렬 순서
        fieldsets (tuple): 필드 편집 레이아웃
    """
    list_display = ['email', 'username', 'total_points', 'created_at', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('total_points',)}),
    )
