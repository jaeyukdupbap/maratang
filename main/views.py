from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from community.models import CommunityMeeting
from growth.models import UserPet
from donation.models import DonationPool

# Create your views here.

def main(request):
    """메인 홈 페이지"""
    # 최근 모임 목록
    recent_meetings = []
    try:
        recent_meetings = CommunityMeeting.objects.all().order_by('-created_at')[:5]
    except Exception:
        pass
    
    # 현재 진행 중인 기부 풀
    active_pool = None
    try:
        active_pool = DonationPool.objects.filter(status='open').order_by('-created_at').first()
    except Exception:
        pass
    
    # 사용자 정보 (로그인한 경우)
    user_pet = None
    if request.user.is_authenticated:
        try:
            user_pet = UserPet.objects.get(user_id=request.user)
        except (UserPet.DoesNotExist, Exception):
            pass
    
    context = {
        'recent_meetings': recent_meetings,
        'active_pool': active_pool,
        'user_pet': user_pet,
    }
    return render(request, 'main.html', context)
