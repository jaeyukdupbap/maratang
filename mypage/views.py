"""
@Project : Mood Garden (Community & Donation Platform)
@File    : mypage/views.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-04
@Description : 마이페이지 및 알림 관리. 사용자 프로필, 참여 모임, 포인트 히스토리, 알림 조회 기능을 제공합니다.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from notification.models import Notification
from growth.models import UserPet, UserInventory, PointsHistory
from community.models import MeetingParticipant, CommunityMeeting

# Create your views here.

@login_required
def mypage(request):
    """
    마이페이지
    
    사용자 프로필, 펫 정보, 포인트 히스토리, 참여 및 호스트한 모임을 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: mypage.html 템플릿 렌더링
        
    Context:
        user: 로그인한 사용자 정보
        user_pet: 사용자의 펫
        inventory: 장착된 아이템
        points_history: 최근 포인트 변동 20개
        participated_meetings: 참여한 모임 10개
        hosted_meetings: 호스트한 모임 10개
    """
    # 사용자 펫 정보
    try:
        user_pet = UserPet.objects.get(user_id=request.user)
    except UserPet.DoesNotExist:
        user_pet = None
    
    # 인벤토리
    inventory = UserInventory.objects.filter(user_id=request.user, is_equipped=True)
    
    # 포인트 이력
    points_history = PointsHistory.objects.filter(user_id=request.user).order_by('-created_at')[:20]
    
    # 참여한 모임
    participated_meetings = CommunityMeeting.objects.filter(
        participants__user_id=request.user
    ).distinct().order_by('-created_at')[:10]
    
    # 호스트한 모임
    hosted_meetings = CommunityMeeting.objects.filter(
        host_id=request.user
    ).order_by('-created_at')[:10]
    
    context = {
        'user': request.user,
        'user_pet': user_pet,
        'inventory': inventory,
        'points_history': points_history,
        'participated_meetings': participated_meetings,
        'hosted_meetings': hosted_meetings,
    }
    return render(request, 'mypage.html', context)


@login_required
def notifications(request):
    """
    알림 목록 조회
    
    사용자의 모든 알림을 최신순으로 표시합니다.
    읽지 않은 알림 개수도 함께 제공합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: mypage/notifications.html 템플릿 렌더링
        
    Context:
        notifications: 사용자의 모든 알림 (최신순)
        unread_count: 읽지 않은 알림 개수
    """
    notifications_list = Notification.objects.filter(
        user_id=request.user
    ).order_by('-created_at')
    
    # 읽지 않은 알림 수
    unread_count = notifications_list.filter(is_read=False).count()
    
    context = {
        'notifications': notifications_list,
        'unread_count': unread_count,
    }
    return render(request, 'mypage/notifications.html', context)


@login_required
def notification_read(request, notification_id):
    """
    알림 읽음 처리
    
    특정 알림을 읽음 상태로 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        notification_id (int): 읽을 알림 ID
        
    Returns:
        HttpResponse: notifications 페이지로 리다이렉트
        
    Side Effects:
        - Notification.is_read 업데이트
    """
    notification = Notification.objects.get(
        notification_id=notification_id,
        user_id=request.user
    )
    notification.is_read = True
    notification.save()
    
    return redirect('notifications')
