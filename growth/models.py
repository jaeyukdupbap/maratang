"""
@Project : Mood Garden (Community & Donation Platform)
@File    : growth/models.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-03
@Description : 사용자 성장 시스템 모델 (펫, 아이템, 포인트 히스토리 등)
"""

from django.db import models
from account.models import User

# Create your models here.

class PetItem(models.Model):
    """펫 아이템 상점 카탈로그 모델"""
    ITEM_TYPE_CHOICES = [
        ('snack', '간식'),
        ('decoration', '장식'),
    ]
    
    item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    required_level = models.IntegerField(default=1, help_text="구매 가능한 최소 레벨")
    cost = models.IntegerField(help_text="필요한 포인트")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pet_item'
        ordering = ['required_level', 'cost']
    
    def __str__(self):
        return self.item_name


class UserPet(models.Model):
    """
    사용자 펫 상태 모델
    
    각 사용자가 키우는 펫의 현재 상태를 추적합니다.
    포인트 획득 시 경험치가 증가하며, 경험치가 일정 수준에 도달하면 레벨 업합니다.
    
    Attributes:
        user_pet_id (AutoField): 펫 ID (PK)
        user_id (OneToOneField): 펫 소유자
        pet_type (CharField): 펫 종류 ('cat', 'dog', 'tree', 'otter')
        current_level (IntegerField): 현재 레벨
        current_xp (IntegerField): 현재 경험치
        created_at (DateTimeField): 펫 생성 시간
        updated_at (DateTimeField): 마지막 업데이트 시간
        
    Properties:
        max_xp: 현재 레벨에서 다음 레벨까지 필요한 경험치
    """
    PET_TYPE_CHOICES = [
        ('cat', '고양이'),
        ('dog', '강아지'),
        ('tree', '그루트'),
        # 필요시 추가 가능
    ]
    
    user_pet_id = models.AutoField(primary_key=True)
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pet', db_column='user_id')
    pet_type = models.CharField(max_length=20, choices=PET_TYPE_CHOICES, default='otter')
    current_level = models.IntegerField(default=1)
    current_xp = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def max_xp(self):
        return (self.current_level + 1) * 100
        
    class Meta:
        db_table = 'user_pet'
    
    def __str__(self):
        return f"{self.user_id.username}'s {self.get_pet_type_display()} (Lv.{self.current_level})"


class UserInventory(models.Model):
    """
    사용자 구매 아이템 인벤토리 모델
    
    사용자가 포인트로 구매한 펫 아이템을 관리합니다.
    같은 아이템을 여러 개 구매할 수 없으며, 장착/해제 상태를 추적합니다.
    
    Attributes:
        inventory_id (AutoField): 인벤토리 항목 ID (PK)
        user_id (ForeignKey): 아이템 소유자
        item_id (ForeignKey): 구매한 아이템
        is_equipped (BooleanField): 펫에 장착 여부
        acquired_at (DateTimeField): 구매 시간
    """
    inventory_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items', db_column='user_id')
    item_id = models.ForeignKey(PetItem, on_delete=models.CASCADE, related_name='owned_by_users', db_column='item_id')
    is_equipped = models.BooleanField(default=False)
    acquired_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_inventory'
        unique_together = ['user_id', 'item_id']  # 같은 아이템 중복 구매 방지 (또는 허용하려면 제거)
        ordering = ['-acquired_at']
    
    def __str__(self):
        return f"{self.user_id.username} - {self.item_id.item_name}"


class RoomItem(models.Model):
    """
    마이룸 가구/배경 상점 카탈로그 모델
    
    마이룸을 꾸미기 위한 가구, 배경, 소품 등을 관리합니다.
    각 아이템은 레이어링을 위한 z-index를 가집니다.
    
    Attributes:
        room_item_id (AutoField): 아이템 ID (PK)
        item_name (CharField): 아이템 이름
        category (CharField): 카테고리 (배경, 가구, 소품)
        cost (IntegerField): 필요한 포인트
        image (ImageField): 아이템 이미지 파일
        z_index (IntegerField): 레이어 순서 (높을수록 앞에 표시)
        default_top (IntegerField): 기본 위치 (top)
        default_left (IntegerField): 기본 위치 (left)
        width (IntegerField): 이미지 가로 크기 (px)
        height (IntegerField): 이미지 세로 크기 (px)
        created_at (DateTimeField): 생성 시간
    """
    CATEGORY_CHOICES = [
        ('background', '배경'),
        ('furniture', '가구'),
        ('accessory', '소품'),
    ]
    
    room_item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100, help_text="아이템 이름")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, help_text="아이템 카테고리")
    cost = models.IntegerField(help_text="필요한 포인트")
    image = models.ImageField(upload_to='room_items/', help_text="아이템 이미지")
    z_index = models.IntegerField(default=1, help_text="레이어 순서 (높을수록 앞에 표시)")
    default_top = models.IntegerField(default=0, help_text="기본 위치 (top, px)")
    default_left = models.IntegerField(default=0, help_text="기본 위치 (left, px)")
    width = models.IntegerField(default=100, help_text="이미지 가로 크기 (px)")
    height = models.IntegerField(default=100, help_text="이미지 세로 크기 (px)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'room_item'
        ordering = ['z_index', 'created_at']
    
    def __str__(self):
        return f"{self.item_name} ({self.get_category_display()})"


class UserRoomDecoration(models.Model):
    """
    사용자 마이룸 가구 배치 모델
    
    사용자가 구매한 가구를 마이룸에 배치한 정보를 저장합니다.
    각 가구의 위치(top, left)와 활성화 여부를 추적합니다.
    
    Attributes:
        decoration_id (AutoField): 배치 ID (PK)
        user_id (ForeignKey): 사용자
        room_item_id (ForeignKey): 가구 아이템
        position_top (IntegerField): 배치된 위치 (top, px)
        position_left (IntegerField): 배치된 위치 (left, px)
        is_displayed (BooleanField): 마이룸에 표시 여부
        created_at (DateTimeField): 배치 시간
        updated_at (DateTimeField): 마지막 수정 시간
    """
    decoration_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_decorations', db_column='user_id')
    room_item_id = models.ForeignKey(RoomItem, on_delete=models.CASCADE, related_name='user_placements', db_column='room_item_id')
    position_top = models.IntegerField(default=0, help_text="배치된 위치 (top, px)")
    position_left = models.IntegerField(default=0, help_text="배치된 위치 (left, px)")
    is_displayed = models.BooleanField(default=True, help_text="마이룸에 표시 여부")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_room_decoration'
        ordering = ['room_item_id__z_index', 'created_at']
        unique_together = ['user_id', 'room_item_id']  # 사용자당 같은 아이템 1개만 배치
    
    def __str__(self):
        return f"{self.user_id.username} - {self.room_item_id.item_name}"


class PointsHistory(models.Model):
    """
    포인트 변동 이력 모델
    
    모든 포인트 획득 및 소비 내역을 기록합니다.
    기부 시스템, 통계 분석, 감사 추적 등에 사용됩니다.
    
    Attributes:
        point_id (AutoField): 기록 ID (PK)
        user_id (ForeignKey): 포인트 변동 사용자
        meeting_id (ForeignKey): 관련 모임 (선택사항)
        item_id (ForeignKey): 구매한 아이템 (선택사항)
        points_change (IntegerField): 변동 포인트 (+100, -50 등)
        reason (CharField): 변동 사유
        created_at (DateTimeField): 기록 생성 시간
    """
    REASON_CHOICES = [
        ('ai_approval', 'AI 승인'),
        ('admin_approval', '관리자 승인'),
        ('item_purchase', '아이템 구매'),
        ('meeting_participation', '모임 참여'),
    ]
    
    point_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_history', db_column='user_id')
    meeting_id = models.ForeignKey('community.CommunityMeeting', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='points_history', db_column='meeting_id')
    item_id = models.ForeignKey(PetItem, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='points_history', db_column='item_id')
    points_change = models.IntegerField(help_text="+100 or -50 등")
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'points_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_id.username} - {self.points_change:+d} ({self.get_reason_display()})"
