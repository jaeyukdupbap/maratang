from django.contrib import admin
from .models import DonationPool, DonationHistory

# Register your models here.

@admin.register(DonationPool)
class DonationPoolAdmin(admin.ModelAdmin):
    list_display = ['pool_id', 'title', 'current_points', 'goal_points', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title']
    readonly_fields = ['pool_id', 'created_at']
    
    def get_progress_display(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress_display.short_description = '진행률'


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    list_display = ['donation_id', 'pool_id', 'user_id', 'contributed_points', 'created_at']
    list_filter = ['created_at']
    search_fields = ['pool_id__title', 'user_id__username', 'user_id__email']
    readonly_fields = ['donation_id', 'created_at']
    ordering = ['-contributed_points', '-created_at']
