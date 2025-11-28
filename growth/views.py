from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PetItem, UserPet, UserInventory, PointsHistory
from account.models import User

# Create your views here.

@login_required
def pet_select(request):
    """펫 선택 페이지"""
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
    """동물 키우기 메인 페이지"""
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
    }
    return render(request, 'growth.html', context)


@login_required
def purchase_item(request, item_id):
    """아이템 구매"""
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
    """아이템 장착/해제"""
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
def shop(request):
    return render(request, 'shop.html')