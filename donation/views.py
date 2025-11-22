from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import DonationPool, DonationHistory
from growth.models import PointsHistory
from django.db.models import Sum

# Create your views here.

def donation(request):
    """기부 돼지저금통 페이지"""
    # 현재 진행 중인 기부 풀
    active_pool = None
    completed_pools = []
    user_contribution = 0
    
    try:
        active_pool = DonationPool.objects.filter(status='open').order_by('-created_at').first()
        
        # 완료된 기부 풀 목록
        completed_pools = DonationPool.objects.filter(status='completed').order_by('-completed_at')
        
        # 사용자 기여도 (로그인한 경우)
        if request.user.is_authenticated:
            if active_pool:
                # 현재 풀에 대한 기여도
                user_contribution = PointsHistory.objects.filter(
                    user_id=request.user,
                    points_change__gt=0,
                    created_at__gte=active_pool.created_at
                ).aggregate(total=Sum('points_change'))['total'] or 0
    except Exception:
        pass
    
    context = {
        'active_pool': active_pool,
        'completed_pools': completed_pools,
        'user_contribution': user_contribution,
    }
    return render(request, 'donation.html', context)


@login_required
def donation_history(request, pool_id):
    """기부 명예의 전당"""
    try:
        pool = DonationPool.objects.get(pool_id=pool_id)
        history = DonationHistory.objects.filter(pool_id=pool).order_by('-contributed_points')
        
        context = {
            'pool': pool,
            'history': history,
        }
        return render(request, 'donation/history.html', context)
    except DonationPool.DoesNotExist:
        from django.http import Http404
        raise Http404("기부 풀을 찾을 수 없습니다.")
