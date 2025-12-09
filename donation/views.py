"""
@Project : Mood Garden (Community & Donation Platform)
@File    : donation/views.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-01 ~ 2025-12-03
@Description : 기부 캠페인 관리 및 조회 기능 구현. 기부 이벤트 생성, 리스트 조회, 기부 기록 관리 등을 처리합니다.
"""

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
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
    메인 기부 페이지 조회
    
    현재 진행 중인 활성 캠페인과 완료된 캠페인 목록, TOP 10 기부자,
    최근 기부 내역을 포함하여 사용자에게 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: donation.html 템플릿에 렌더링된 응답
        
    Context:
        active_pool: 현재 진행 중인 DonationPool 객체
        completed_pools: 완료된 DonationPool 목록
        user_contribution: 로그인 사용자의 현재 캠페인 기여 포인트
        top_donors: TOP 10 기부자 리스트
        recent_donations: 최근 기부 내역 (5개 또는 전체)
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
    """
    기부 캠페인 완료 후 명예의 전당 조회
    
    특정 DonationPool이 완료될 때 생성된 DonationHistory 기록을 조회합니다.
    포인트 기여도에 따라 정렬된 기부자 명단을 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        pool_id (int): 조회할 DonationPool ID
        
    Returns:
        HttpResponse: donation/history.html 템플릿에 렌더링된 응답
        
    Raises:
        Http404: 해당 pool_id가 존재하지 않을 경우
        
    Context:
        pool: 기부 캠페인 정보
        history: 기부 기록 (기여 포인트 내림차순 정렬)
    """
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


def donation_history_api(request):
    """
    AJAX 모달용 페이지네이션 API
    
    TOP 10 기부자 또는 최근 기부 내역을 페이지네이션하여 JSON으로 응답합니다.
    기부 메인 페이지의 모달에서 더보기 버튼 클릭 시 호출됩니다.
    
    Args:
        request (HttpRequest): Query parameters 포함
            - type (str): 'top' (상위 기부자) 또는 'recent' (최근 기부)
            - page (int): 페이지 번호 (기본값: 1)
    
    Returns:
        JsonResponse: 다음 구조의 JSON 응답
            - results (list): 기부 데이터 리스트 (rank, username, amount 등)
            - page (int): 현재 페이지 번호
            - num_pages (int): 전체 페이지 수
            - type (str): 요청한 리스트 타입
    """
    list_type = request.GET.get('type', 'recent')
    page = int(request.GET.get('page', 1))

    active_pool = (
        DonationPool.objects.filter(status='open')
        .order_by('-created_at')
        .first()
    )
    if not active_pool:
        return JsonResponse({'results': [], 'page': 1, 'num_pages': 1})

    if list_type == 'top':
        qs = (
            PointsHistory.objects
            .filter(created_at__gte=active_pool.created_at, points_change__gt=0)
            .values('user_id', 'user_id__username')
            .annotate(total_amount=Sum('points_change'))
            .order_by('-total_amount')
        )
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page)
        results = [
            {
                'rank': idx + 1 + (page_obj.number - 1) * paginator.per_page,
                'username': row['user_id__username'],
                'amount': row['total_amount'],
            }
            for idx, row in enumerate(page_obj.object_list)
        ]
    else:
        qs = (
            PointsHistory.objects
            .filter(created_at__gte=active_pool.created_at, points_change__gt=0)
            .select_related('user_id')
            .order_by('-created_at')
        )
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page)
        results = [
            {
                'username': row.user_id.username,
                'amount': row.points_change,
                'created': row.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for row in page_obj.object_list
        ]

    return JsonResponse({
        'results': results,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'type': list_type,
    })


def _is_admin(user):
    """
    사용자 관리자 여부 검증
    
    Args:
        user (User): Django User 객체
        
    Returns:
        bool: 인증된 사용자이면서 스태프 권한이 있으면 True
    """
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_admin)
def donation_create(request):
    """
    관리자 전용 기부 캠페인 생성 페이지
    
    새로운 DonationPool 캠페인을 생성합니다. POST 요청 시 폼을 검증하고 저장합니다.
    
    Args:
        request (HttpRequest): GET/POST 요청 객체
    
    Returns:
        GET: donation/create.html 템플릿에 빈 폼 렌더링
        POST: 성공 시 donation 페이지로 리다이렉트
        
    Context:
        form: DonationPoolForm 인스턴스
    """
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