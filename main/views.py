"""
@Project : Mood Garden (Community & Donation Platform)
@File    : main/views.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-11-30 ~ 2025-12-09
@Description : 메인 홈페이지. 최근 모임, 현재 기부 캠페인, 사용자 펫 정보를 표시합니다.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from community.models import CommunityMeeting
from growth.models import UserPet
from donation.models import DonationPool

# Create your views here.

def main(request):
    """
    메인 홈페이지
    
    최근 생성된 모임, 현재 진행 중인 기부 캠페인, 사용자의 펫 정보를 표시합니다.
    로그인하지 않은 사용자도 접근 가능합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: main.html 템플릿 렌더링
        
    Context:
        recent_meetings: 최근 5개 모임 (참여자 수 포함)
        active_pool: 현재 진행 중인 기부 캠페인
        user_pet: 로그인 사용자의 펫 (로그인하지 않으면 None)
    """
    
    # 1. 최근 모임 목록 (참여자 수 카운트 추가)
    recent_meetings = []
    try:
        # annotate를 사용하여 'participants' 관계를 셉니다.
        # 이제 템플릿에서 {{ meeting.participant_count }}를 사용할 수 있습니다.
        recent_meetings = CommunityMeeting.objects.annotate(
            participant_count=Count('participants')
        ).order_by('-created_at')[:5]
    except Exception:
        pass
    
    # 2. 현재 진행 중인 기부 풀
    active_pool = None
    try:
        active_pool = DonationPool.objects.filter(status='open').order_by('-created_at').first()
    except Exception:
        pass
    
    # 3. 사용자 정보 (로그인한 경우)
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
