"""
@Project : Mood Garden (Community & Donation Platform)
@File    : growth/views.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-03
@Description : 펫 시스템 및 포인트 상점 관리. 펫 선택, 성장 조회, 아이템 구매 기능을 제공합니다.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PetItem, UserPet, UserInventory, PointsHistory
from account.models import User

# Create your views here.

@login_required
def pet_select(request):
    """
    펫 선택 페이지
    
    첫 로그인 사용자가 키울 펫을 선택합니다.
    기존 펫이 있으면 성장 페이지로 자동 리다이렉트됩니다.
    
    Args:
        request (HttpRequest): GET/POST 요청 객체
        
    Returns:
        GET: pet_select.html 템플릿 렌더링
        POST: 성공 시 growth 페이지로 리다이렉트
    """
    try:
        user_pet = UserPet.objects.get(user_id=request.user)
        # 이미 펫이 있으면 성장 페이지로 리다이렉트
        return redirect('growth')
    except UserPet.DoesNotExist:
        pass
    
    if request.method == 'POST':
        pet_type = request.POST.get('pet_type')
        
        if pet_type not in ['cat', 'dog', 'tree']:
            messages.error(request, '유효하지 않은 펫 종류입니다.')
            return render(request, 'pet_select.html')
        
        try:
            user_pet = UserPet.objects.create(
                user_id=request.user,
                pet_type=pet_type,
                current_level=1,
                current_xp=0
            )
            messages.success(request, f'{user_pet.get_pet_type_display()}을(를) 선택했습니다!')
            return redirect('growth')
        except Exception as e:
            messages.error(request, f'펫 생성 중 오류가 발생했습니다: {str(e)}')
            return render(request, 'pet_select.html')
    
    pet_choices = [
        {'type': 'cat', 'name': '고양이'},
        {'type': 'dog', 'name': '강아지'},
        {'type': 'tree', 'name': '그루트'},
    ]
    
    return render(request, 'pet_select.html', {'pet_choices': pet_choices})


@login_required
def growth(request):
    """
    동물 키우기 메인 페이지
    
    사용자의 펫 상태, 포인트 히스토리, 구매 가능한 아이템을 표시합니다.
    레벨과 포인트에 따라 아이템 구매 가능 여부가 결정됩니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: growth.html 템플릿 렌더링
        
    Context:
        user_pet: 사용자의 펫 정보
        items: 모든 펫 아이템
        inventory: 사용자가 구매한 아이템
        owned_item_ids: 구매한 아이템 ID 세트
        points_history: 최근 포인트 변동 10개
        user_points: 사용자의 현재 포인트
    """
    # 사용자 펫 정보
    try:
        user_pet = UserPet.objects.get(user_id=request.user)
    except UserPet.DoesNotExist:
        # 펫이 없으면 펫 선택 페이지로 리다이렉트
        return redirect('pet_select')
    
    # 상점 아이템 목록
    items = PetItem.objects.all().order_by('required_level', 'cost')
    
    # 사용자 인벤토리
    inventory = UserInventory.objects.filter(user_id=request.user)
    owned_item_ids = set(inventory.values_list('item_id', flat=True))
    
    # 포인트 이력
    points_history = PointsHistory.objects.filter(user_id=request.user).order_by('-created_at')[:10]
    
    context = {
        'user_pet': user_pet,
        'items': items,
        'inventory': inventory,
        'owned_item_ids': owned_item_ids,
        'points_history': points_history,
        'user_points': request.user.total_points,
        'pet_choices': UserPet.PET_TYPE_CHOICES,
    }
    return render(request, 'growth.html', context)


@login_required
def purchase_item(request, item_id):
    """
    아이템 구매 처리
    
    사용자 레벨과 포인트를 확인하고 아이템을 구매합니다.
    포인트 이력을 기록하고 인벤토리에 추가합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        item_id (int): 구매할 아이템 ID
        
    Returns:
        HttpResponse: growth 페이지로 리다이렉트
        
    Side Effects:
        - User.total_points 감소
        - PointsHistory 생성
        - UserInventory 추가
    """
    item = get_object_or_404(PetItem, item_id=item_id)
    user_pet = UserPet.objects.get(user_id=request.user)
    
    # 레벨 체크
    if user_pet.current_level < item.required_level:
        messages.error(request, f'레벨 {item.required_level} 이상이어야 구매할 수 있습니다.')
        return redirect('growth')
    
    # 포인트 체크
    if request.user.total_points < item.cost:
        messages.error(request, '포인트가 부족합니다.')
        return redirect('growth')
    
    # 이미 구매했는지 확인 (중복 구매 방지)
    if UserInventory.objects.filter(user_id=request.user, item_id=item).exists():
        messages.warning(request, '이미 구매한 아이템입니다.')
        return redirect('growth')
    
    try:
        # 포인트 차감
        request.user.total_points -= item.cost
        request.user.save()
        
        # 포인트 이력 기록
        PointsHistory.objects.create(
            user_id=request.user,
            item_id=item,
            points_change=-item.cost,
            reason='item_purchase'
        )
        
        # 인벤토리에 추가
        UserInventory.objects.create(
            user_id=request.user,
            item_id=item,
            is_equipped=False
        )
        
        messages.success(request, f'{item.item_name}을(를) 구매했습니다.')
    except Exception as e:
        messages.error(request, f'구매 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('growth')


@login_required
def equip_item(request, inventory_id):
    """
    아이템 장착/해제 토글
    
    인벤토리 아이템의 장착 상태를 전환합니다.
    장식 아이템은 한 번에 하나만 장착 가능합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        inventory_id (int): 인벤토리 항목 ID
        
    Returns:
        HttpResponse: growth 페이지로 리다이렉트
        
    Side Effects:
        - UserInventory.is_equipped 토글
        - 같은 타입의 다른 아이템 자동 해제
    """
    inventory_item = get_object_or_404(UserInventory, inventory_id=inventory_id, user_id=request.user)
    
    # 같은 타입의 다른 아이템 해제 (선택적)
    if inventory_item.item_id.item_type == 'decoration':
        # 장식 아이템은 하나만 장착 가능
        UserInventory.objects.filter(
            user_id=request.user,
            item_id__item_type='decoration',
            is_equipped=True
        ).update(is_equipped=False)
    
    # 토글
    inventory_item.is_equipped = not inventory_item.is_equipped
    inventory_item.save()
    
    status = '장착' if inventory_item.is_equipped else '해제'
    messages.success(request, f'{inventory_item.item_id.item_name}을(를) {status}했습니다.')
    
    return redirect('growth')


@login_required
def change_pet(request):
    """
    기존 펫 종류 변경
    
    사용자가 키우는 펫의 종류를 변경합니다.
    레벨, 경험치는 유지되고 종류만 변경됩니다.
    
    Args:
        request (HttpRequest): POST 요청 객체
            - pet_type: 변경할 펫 종류
            
    Returns:
        HttpResponse: growth 페이지로 리다이렉트
        
    Side Effects:
        - UserPet.pet_type 변경
    """
    if request.method != 'POST':
        return redirect('growth')
    
    pet_type = request.POST.get('pet_type')
    valid_types = dict(UserPet.PET_TYPE_CHOICES).keys()
    if pet_type not in valid_types:
        messages.error(request, '유효하지 않은 펫 종류입니다.')
        return redirect('growth')
    
    try:
        user_pet = UserPet.objects.get(user_id=request.user)
    except UserPet.DoesNotExist:
        messages.error(request, '먼저 펫을 생성해 주세요.')
        return redirect('pet_select')
    
    user_pet.pet_type = pet_type
    user_pet.save(update_fields=['pet_type', 'updated_at'])
    messages.success(request, f"{user_pet.get_pet_type_display()}(으)로 펫을 변경했습니다.")
    return redirect('growth')

@login_required
def shop(request):
    """
    상점 페이지
    
    펫 아이템 상점 페이지를 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: shop.html 템플릿 렌더링
    """
    return render(request, 'shop.html')