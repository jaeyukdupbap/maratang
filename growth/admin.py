from django.contrib import admin
from .models import PetItem, UserPet, UserInventory, PointsHistory

# Register your models here.

@admin.register(PetItem)
class PetItemAdmin(admin.ModelAdmin):
    list_display = ['item_id', 'item_name', 'item_type', 'required_level', 'cost', 'created_at']
    list_filter = ['item_type', 'required_level', 'created_at']
    search_fields = ['item_name']
    readonly_fields = ['item_id', 'created_at']


@admin.register(UserPet)
class UserPetAdmin(admin.ModelAdmin):
    list_display = ['user_pet_id', 'user_id', 'pet_type', 'current_level', 'current_xp', 'updated_at']
    list_filter = ['pet_type', 'current_level', 'created_at']
    search_fields = ['user_id__username', 'user_id__email']
    readonly_fields = ['user_pet_id', 'created_at', 'updated_at']


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ['inventory_id', 'user_id', 'item_id', 'is_equipped', 'acquired_at']
    list_filter = ['is_equipped', 'acquired_at']
    search_fields = ['user_id__username', 'item_id__item_name']
    readonly_fields = ['inventory_id', 'acquired_at']


@admin.register(PointsHistory)
class PointsHistoryAdmin(admin.ModelAdmin):
    list_display = ['point_id', 'user_id', 'points_change', 'reason', 'meeting_id', 'item_id', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['user_id__username', 'user_id__email']
    readonly_fields = ['point_id', 'created_at']
    date_hierarchy = 'created_at'
