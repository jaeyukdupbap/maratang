"""
@Project : Mood Garden (Community & Donation Platform)
@File    : growth/admin.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-03
@Description : Django 관리자 페이지 - 펫, 아이템, 포인트 히스토리 관리
"""

from django.contrib import admin
from .models import PetItem, UserPet, UserInventory, PointsHistory

# Register your models here.

@admin.register(PetItem)
class PetItemAdmin(admin.ModelAdmin):
    """
    펫 아이템 상점 관리자 클래스
    
    구매 가능한 펫 아이템의 종류, 가격, 요구 레벨을 관리합니다.
    """
    list_display = ['item_id', 'item_name', 'item_type', 'required_level', 'cost', 'created_at']
    list_filter = ['item_type', 'required_level', 'created_at']
    search_fields = ['item_name']
    readonly_fields = ['item_id', 'created_at']


@admin.register(UserPet)
class UserPetAdmin(admin.ModelAdmin):
    """
    사용자 펫 관리자 클래스
    
    각 사용자의 펫 상태(레벨, 경험치) 및 성장 추적을 관리합니다.
    """
    list_display = ['user_pet_id', 'user_id', 'pet_type', 'current_level', 'current_xp', 'updated_at']
    list_filter = ['pet_type', 'current_level', 'created_at']
    search_fields = ['user_id__username', 'user_id__email']
    readonly_fields = ['user_pet_id', 'created_at', 'updated_at']


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    """
    사용자 인벤토리 관리자 클래스
    
    사용자가 구매한 펫 아이템 및 장착 상태를 관리합니다.
    """
    list_display = ['inventory_id', 'user_id', 'item_id', 'is_equipped', 'acquired_at']
    list_filter = ['is_equipped', 'acquired_at']
    search_fields = ['user_id__username', 'item_id__item_name']
    readonly_fields = ['inventory_id', 'acquired_at']


@admin.register(PointsHistory)
class PointsHistoryAdmin(admin.ModelAdmin):
    """
    포인트 히스토리 관리자 클래스
    
    모든 포인트 획득 및 소비 내역을 감사 추적 및 통계 용도로 관리합니다.
    """
    list_display = ['point_id', 'user_id', 'points_change', 'reason', 'meeting_id', 'item_id', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['user_id__username', 'user_id__email']
    readonly_fields = ['point_id', 'created_at']
    date_hierarchy = 'created_at'
