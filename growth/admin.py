"""
@Project : Mood Garden (Community & Donation Platform)
@File    : growth/admin.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-09
@Description : Django 관리자 페이지 - 펫, 아이템, 마이룸 가구, 포인트 히스토리 관리
"""

from django.contrib import admin
from .models import PetItem, UserPet, UserInventory, PointsHistory, RoomItem, UserRoomDecoration

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


@admin.register(RoomItem)
class RoomItemAdmin(admin.ModelAdmin):
    """
    마이룸 가구 상점 관리자 클래스
    
    마이룸 꾸미기용 가구, 배경, 소품을 관리합니다.
    레이어링을 위한 z-index와 기본 위치를 설정합니다.
    """
    list_display = ['room_item_id', 'item_name', 'category', 'cost', 'z_index', 'width', 'height', 'created_at']
    list_filter = ['category', 'z_index', 'created_at']
    search_fields = ['item_name']
    readonly_fields = ['room_item_id', 'created_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('item_name', 'category', 'cost')
        }),
        ('이미지', {
            'fields': ('image',)
        }),
        ('레이어링 & 위치', {
            'fields': ('z_index', 'default_top', 'default_left', 'width', 'height'),
            'description': 'z_index가 높을수록 앞에 표시됩니다.'
        }),
        ('메타정보', {
            'fields': ('room_item_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserRoomDecoration)
class UserRoomDecorationAdmin(admin.ModelAdmin):
    """
    사용자 마이룸 배치 관리자 클래스
    
    사용자가 구매한 가구의 배치 위치와 표시 여부를 관리합니다.
    """
    list_display = ['decoration_id', 'user_id', 'room_item_id', 'position_top', 'position_left', 'is_displayed', 'created_at']
    list_filter = ['is_displayed', 'created_at']
    search_fields = ['user_id__username', 'room_item_id__item_name']
    readonly_fields = ['decoration_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user_id', 'room_item_id', 'is_displayed')
        }),
        ('위치', {
            'fields': ('position_top', 'position_left'),
            'description': '픽셀 단위의 절대 위치입니다.'
        }),
        ('메타정보', {
            'fields': ('decoration_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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
