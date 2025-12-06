from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model

# PointsHistory를 메인 데이터 소스로 사용합니다.
from growth.models import PointsHistory
from .models import DonationHistory, DonationPool

# DonationTransaction은 tasks.py 로직상 더 이상 실시간으로 생성되지 않으므로 제거하거나 주석 처리합니다.
# from .models import DonationTransaction 

User = get_user_model()

class DonationPoolForm(forms.ModelForm):
    """기부 이벤트 생성 폼"""
    class Meta:
        model = DonationPool
        fields = ['title', 'sponsor', 'start_date', 'end_date', 'goal_points']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '예: 유기동물 보호소 간식 기부'}),
            'sponsor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '후원사 이름을 입력하세요'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'goal_points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '목표 포인트를 입력하세요', 'min': 1}),
        }
        labels = {
            'title': '기부 이벤트 제목',
            'sponsor': '후원사',
            'start_date': '시작일',
            'end_date': '종료일',
            'goal_points': '목표 포인트',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('종료일은 시작일보다 이후여야 합니다.')

        return cleaned_data


def donation(request):
    """
    메인 기부 페이지
    """
    active_pool = None
    completed_pools = []
    user_contribution = 0
    top_donors = []
    recent_donations = []
    show_all_donations = request.GET.get('view') == 'all'

    try:
        # 1. 현재 진행 중인 기부 캠페인
        active_pool = (
            DonationPool.objects.filter(status='open')
            .order_by('-created_at')
            .first()
        )
        
        # 2. 완료된 캠페인 목록
        completed_pools = (
            DonationPool.objects.filter(status='completed')
            .order_by('-completed_at', '-created_at')
        )

        if active_pool:
            # [수정됨] 우측 패널 - TOP 10 (PointsHistory 집계)
            # 현재 active_pool이 생성된 이후에 획득한 포인트(gt=0)를 기준으로 집계
            top_donors = (
                PointsHistory.objects
                .filter(created_at__gte=active_pool.created_at, points_change__gt=0)
                .values('user_id', 'user_id__username') # Group By user
                .annotate(total_amount=Sum('points_change'))
                .order_by('-total_amount')[:10]
            )

            # [수정됨] 내 기여도 (현재 로그인 유저 기준)
            if request.user.is_authenticated:
                user_contribution = (
                    PointsHistory.objects.filter(
                        user_id=request.user,
                        created_at__gte=active_pool.created_at,
                        points_change__gt=0
                    ).aggregate(total=Sum('points_change'))['total']
                    or 0
                )

            # [수정됨] 최근 기부 내역 (실시간 포인트 획득 내역)
            # 기부에 기여하는 포인트 획득 내역을 최신순으로 가져옴
            base_qs = PointsHistory.objects.filter(
                created_at__gte=active_pool.created_at,
                points_change__gt=0
            ).select_related('user_id').order_by('-created_at')

            if show_all_donations:
                recent_donations = base_qs[:100]
            else:
                recent_donations = base_qs[:5]

    except Exception:
        # 에러 발생 시 로그를 남기는 것이 좋지만, 일단 사용자 경험을 위해 패스
        pass
    
    context = {
        'active_pool': active_pool,
        'completed_pools': completed_pools,
        'user_contribution': user_contribution,
        'top_donors': top_donors,
        'recent_donations': recent_donations,
        'show_all_donations': show_all_donations,
    }
    return render(request, 'donation.html', context)


@login_required
def donation_history(request, pool_id):
    """기부 명예의 전당 (완료된 캠페인 기준)"""
    pool = get_object_or_404(DonationPool, pool_id=pool_id)
    
    # 완료된 캠페인은 tasks.py의 create_donation_history 함수에 의해 
    # DonationHistory 테이블에 데이터가 생성되어 있으므로 그대로 사용 가능
    history = DonationHistory.objects.filter(pool_id=pool).select_related('user_id').order_by(
        '-contributed_points'
    )
        
    context = {
        'pool': pool,
        'history': history,
    }
    return render(request, 'donation/history.html', context)


def _is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_admin)
def donation_create(request):
    """관리자 전용 기부 캠페인 생성 페이지"""
    if request.method == 'POST':
        form = DonationPoolForm(request.POST)
        if form.is_valid():
            pool = form.save(commit=False)
            pool.status = 'open'
            pool.current_points = 0
            pool.save()
            return redirect('donation')
    else:
        form = DonationPoolForm()

    context = {
        'form': form,
    }
    return render(request, 'donation/create.html', context)