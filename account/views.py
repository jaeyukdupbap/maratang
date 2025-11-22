from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from .models import User

# Create your views here.

def signup(request):
    """회원가입"""
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # 유효성 검사
        if not email or not username or not password:
            messages.error(request, '모든 필드를 입력해주세요.')
            return render(request, 'signup.html')
        
        if password != password_confirm:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, '이미 존재하는 이메일입니다.')
            return render(request, 'signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '이미 존재하는 사용자명입니다.')
            return render(request, 'signup.html')
        
        # 사용자 생성
        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password
            )
            # UserPet 자동 생성
            from growth.models import UserPet
            UserPet.objects.create(
                user_id=user,
                pet_type='otter',
                current_level=1,
                current_xp=0
            )
            messages.success(request, '회원가입이 완료되었습니다. 로그인해주세요.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'회원가입 중 오류가 발생했습니다: {str(e)}')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')


def login_view(request):
    """로그인"""
    if request.user.is_authenticated:
        return redirect('main')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, '이메일과 비밀번호를 입력해주세요.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'환영합니다, {user.username}님!')
            next_url = request.GET.get('next', 'main')
            return redirect(next_url)
        else:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    """로그아웃"""
    logout(request)
    messages.success(request, '로그아웃되었습니다.')
    return redirect('main')
