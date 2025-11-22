from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

# Create your views here.

@login_required
def notification_count(request):
    """읽지 않은 알림 개수 API"""
    count = Notification.objects.filter(
        user_id=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def notification_list_api(request):
    """알림 목록 API (AJAX용)"""
    notifications = Notification.objects.filter(
        user_id=request.user
    ).order_by('-created_at')[:10]
    
    data = [{
        'id': n.notification_id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notifications]
    
    return JsonResponse({'notifications': data})
