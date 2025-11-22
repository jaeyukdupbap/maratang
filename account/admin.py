from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'total_points', 'created_at', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('total_points',)}),
    )
