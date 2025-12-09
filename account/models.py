"""
@Project : Mood Garden (Community & Donation Platform)
@File    : account/models.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-11-25
@Description : 사용자 계정 관리 모델 (커스텀 User 모델, 인증 매니저)
"""

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """
    커스텀 사용자 매니저. Email을 기본 로그인 필드로 사용합니다.
    """

    def create_user(self, email, username, password=None, **extra_fields):
        """
        일반 사용자 계정 생성
        
        Args:
            email (str): 사용자 이메일 (필수, 고유)
            username (str): 사용자명 (필수, 고유)
            password (str, optional): 비밀번호
            **extra_fields: 추가 필드
            
        Returns:
            User: 생성된 사용자 객체
            
        Raises:
            ValueError: email 또는 username이 없을 경우
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        관리자 계정 생성
        
        Args:
            email (str): 관리자 이메일
            username (str): 관리자명
            password (str, optional): 비밀번호
            **extra_fields: 추가 필드
            
        Returns:
            User: 생성된 관리자 객체
            
        Raises:
            ValueError: is_staff 또는 is_superuser 설정 오류 시
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractUser):
    """
    커스텀 사용자 모델. Email을 주요 인증 필드로 사용합니다.
    
    Attributes:
        email (EmailField): 사용자 이메일 (고유, 필수)
        username (CharField): 사용자명 (고유, 필수)
        total_points (IntegerField): 누적 포인트 (기본값: 0)
        created_at (DateTimeField): 계정 생성 시간 (자동 기록)
    """
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=30, unique=True)
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        db_table = 'user'
        ordering = ['-created_at']

    def __str__(self):
        return self.email