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
    """사용자 펫 상태 모델"""
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
    """사용자 구매 아이템 인벤토리 모델"""
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


class PointsHistory(models.Model):
    """포인트 변동 이력 모델"""
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
