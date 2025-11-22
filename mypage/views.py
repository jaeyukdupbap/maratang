from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from notification.models import Notification
from growth.models import UserPet, UserInventory, PointsHistory
from community.models import MeetingParticipant, CommunityMeeting

# Create your views here.

@login_required
def mypage(request):
    """마이페이지"""
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
    """알림 목록"""
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
    """알림 읽음 처리"""
    notification = Notification.objects.get(
        notification_id=notification_id,
        user_id=request.user
    )
    notification.is_read = True
    notification.save()
    
    return redirect('notifications')
