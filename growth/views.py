"""
@Project : Mood Garden (Community & Donation Platform)
@File    : growth/views.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-09
@Description : 펫 시스템 및 마이룸 관리. 펫 선택, 성장 조회, 아이템/가구 구매, 마이룸 꾸미기 기능을 제공합니다.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PetItem, UserPet, UserInventory, PointsHistory, RoomItem, UserRoomDecoration
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
    상점 페이지 (펫 아이템 & 마이룸 가구)
    
    펫 아이템과 마이룸 가구를 탭 형태로 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: shop.html 템플릿 렌더링
        
    Context:
        pet_items: 구매 가능한 펫 아이템
        room_items: 구매 가능한 마이룸 가구
        owned_pet_items: 구매한 펫 아이템 ID 세트
        owned_room_items: 구매한 마이룸 아이템 ID 세트
        user_pet: 사용자의 펫
        user_points: 사용자의 현재 포인트
    """
    from .models import RoomItem, UserRoomDecoration
    
    # 펫 아이템
    pet_items = PetItem.objects.all().order_by('required_level', 'cost')
    
    # 마이룸 아이템
    room_items = RoomItem.objects.all().order_by('category', 'cost')
    
    # 사용자 인벤토리 확인
    owned_pet_items = set(UserInventory.objects.filter(user_id=request.user).values_list('item_id', flat=True))
    owned_room_items = set(UserRoomDecoration.objects.filter(user_id=request.user).values_list('room_item_id', flat=True))
    
    # 사용자 펫
    try:
        user_pet = UserPet.objects.get(user_id=request.user)
    except UserPet.DoesNotExist:
        user_pet = None
    
    context = {
        'pet_items': pet_items,
        'room_items': room_items,
        'owned_pet_items': owned_pet_items,
        'owned_room_items': owned_room_items,
        'user_pet': user_pet,
        'user_points': request.user.total_points,
    }
    return render(request, 'growth/shop.html', context)


@login_required
def buy_room_item(request, room_item_id):
    """
    마이룸 가구 구매
    
    사용자가 마이룸 가구를 구매합니다.
    포인트를 차감하고 UserRoomDecoration에 배치 기록을 저장합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        room_item_id (int): 구매할 가구 아이템 ID
        
    Returns:
        HttpResponse: shop 페이지로 리다이렉트
        
    Side Effects:
        - User.total_points 감소
        - PointsHistory 생성
        - UserRoomDecoration 생성
    """
    from .models import RoomItem, UserRoomDecoration
    
    room_item = get_object_or_404(RoomItem, room_item_id=room_item_id)
    
    # 포인트 확인
    if request.user.total_points < room_item.cost:
        messages.error(request, '포인트가 부족합니다.')
        return redirect('shop')
    
    # 이미 구매했는지 확인
    if UserRoomDecoration.objects.filter(user_id=request.user, room_item_id=room_item).exists():
        messages.warning(request, '이미 구매한 아이템입니다.')
        return redirect('shop')
    
    try:
        # 포인트 차감
        request.user.total_points -= room_item.cost
        request.user.save()
        
        # 포인트 이력 기록
        PointsHistory.objects.create(
            user_id=request.user,
            points_change=-room_item.cost,
            reason='item_purchase'
        )
        
        # 마이룸 배치 기록 생성 (기본 위치로)
        UserRoomDecoration.objects.create(
            user_id=request.user,
            room_item_id=room_item,
            position_top=room_item.default_top,
            position_left=room_item.default_left,
            is_displayed=True
        )
        
        messages.success(request, f'{room_item.item_name}을(를) 구매했습니다.')
    except Exception as e:
        messages.error(request, f'구매 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('shop')


@login_required
def my_room(request):
    """
    마이룸 조회 페이지
    
    사용자의 펫과 배치된 가구들을 표시합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        
    Returns:
        HttpResponse: my_room.html 템플릿 렌더링
        
    Context:
        user_pet: 사용자의 펫 정보
        decorations: 표시 중인 마이룸 가구들
        all_decorations: 구매한 모든 가구들
    """
    from .models import UserRoomDecoration
    
    # 사용자 펫
    try:
        user_pet = UserPet.objects.get(user_id=request.user)
    except UserPet.DoesNotExist:
        messages.warning(request, '먼저 펫을 선택해주세요.')
        return redirect('pet_select')
    
    # 표시 중인 가구들 (z-index 순서로)
    decorations = UserRoomDecoration.objects.filter(
        user_id=request.user,
        is_displayed=True
    ).select_related('room_item_id').order_by('room_item_id__z_index')
    
    # 모든 가구들 (배치 관리용)
    all_decorations = UserRoomDecoration.objects.filter(
        user_id=request.user
    ).select_related('room_item_id').order_by('room_item_id__z_index')
    
    context = {
        'user_pet': user_pet,
        'decorations': decorations,
        'all_decorations': all_decorations,
    }
    return render(request, 'growth/my_room.html', context)


@login_required
def update_decoration_position(request, decoration_id):
    """
    마이룸 가구 위치 변경
    
    사용자가 가구의 위치를 드래그 앤 드롭으로 변경합니다.
    AJAX POST 요청으로 처리합니다.
    
    Args:
        request (HttpRequest): POST 요청 객체
            - position_top (int): 새로운 top 위치 (px)
            - position_left (int): 새로운 left 위치 (px)
        decoration_id (int): 배치 ID
        
    Returns:
        JsonResponse: {'status': 'success'} 또는 오류 메시지
    """
    from django.http import JsonResponse
    from .models import UserRoomDecoration
    
    try:
        decoration = UserRoomDecoration.objects.get(
            decoration_id=decoration_id,
            user_id=request.user
        )
        
        position_top = request.POST.get('position_top')
        position_left = request.POST.get('position_left')
        
        decoration.position_top = int(position_top)
        decoration.position_left = int(position_left)
        decoration.save()
        
        return JsonResponse({'status': 'success'})
    except UserRoomDecoration.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '가구를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def toggle_decoration_display(request, decoration_id):
    """
    마이룸 가구 표시/숨김 토글
    
    가구의 표시 여부를 전환합니다.
    
    Args:
        request (HttpRequest): 사용자 요청 객체
        decoration_id (int): 배치 ID
        
    Returns:
        HttpResponse: my_room 페이지로 리다이렉트
        
    Side Effects:
        - UserRoomDecoration.is_displayed 토글
    """
    from .models import UserRoomDecoration
    
    try:
        decoration = UserRoomDecoration.objects.get(
            decoration_id=decoration_id,
            user_id=request.user
        )
        
        decoration.is_displayed = not decoration.is_displayed
        decoration.save()
        
        status = '표시' if decoration.is_displayed else '숨김'
        messages.success(request, f'{decoration.room_item_id.item_name}을(를) {status}했습니다.')
    except UserRoomDecoration.DoesNotExist:
        messages.error(request, '가구를 찾을 수 없습니다.')
    except Exception as e:
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    return redirect('my_room')