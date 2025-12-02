from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from growth.models import PointsHistory

from .models import DonationHistory, DonationPool, DonationTransaction


class DonationPoolForm(forms.ModelForm):
    """기부 이벤트 생성 폼 (views.py 내 정의)"""

    class Meta:
        model = DonationPool
        fields = ['title', 'sponsor', 'start_date', 'end_date', 'goal_points']
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '예: 유기동물 보호소 간식 기부',
                }
            ),
            'sponsor': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '후원사 이름을 입력하세요',
                }
            ),
            'start_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'end_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'goal_points': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '목표 포인트를 입력하세요',
                    'min': 1,
                }
            ),
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
    - 좌측: 관리자 전용 캠페인 생성 버튼
    - 중앙: 현재 진행 중 캠페인, 돼지저금통, 진행률
    - 우측: 상위 기부 TOP 10, 내 기여도, 최근 기부 내역(+더보기)
    - 하단: 현재 캠페인 요약 정보
    """
    active_pool = None
    completed_pools = []
    user_contribution = 0
    top_donors = []
    recent_donations = []
    show_all_donations = request.GET.get('view') == 'all'

    try:
        # 현재 진행 중인 기부 캠페인 (가장 최근 open)
        active_pool = (
            DonationPool.objects.filter(status='open')
            .order_by('-created_at')
            .first()
        )

        # 완료된 캠페인 목록
        completed_pools = (
            DonationPool.objects.filter(status='completed')
            .order_by('-completed_at', '-created_at')
        )

        if active_pool:
            # 우측 패널 - TOP 10 (현재 진행 중 캠페인 기준)
            top_donors = (
                DonationTransaction.objects.filter(pool_id=active_pool)
                .values('user_id', 'user_id__username')
                .annotate(total_amount=Sum('amount'))
                .order_by('-total_amount')[:10]
            )

            # 내 기여도 (현재 로그인 유저 기준)
            if request.user.is_authenticated:
                user_contribution = (
                    DonationTransaction.objects.filter(
                        pool_id=active_pool, user_id=request.user
                    ).aggregate(total=Sum('amount'))['total']
                    or 0
                )

            # 최근 기부 내역 (DonationTransaction 기준)
            base_qs = DonationTransaction.objects.select_related(
                'user_id', 'pool_id'
            ).order_by('-created_at')

            if show_all_donations:
                recent_donations = base_qs[:100]  # 안전을 위한 상한
            else:
                recent_donations = base_qs[:3]

    except Exception:
        # 메인 페이지는 최대한 죽지 않도록 방어
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
    history = DonationHistory.objects.filter(pool_id=pool).order_by(
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
    """
    관리자 전용 기부 캠페인 생성 페이지
    - Title, Content(=description), Start/End Date, Goal Amount 입력
    """
    if request.method == 'POST':
        form = DonationPoolForm(request.POST)
        if form.is_valid():
            pool = form.save(commit=False)
            # 새 캠페인은 항상 진행 중 상태로 시작
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
