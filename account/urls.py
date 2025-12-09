"""
@Project : Mood Garden (Community & Donation Platform)
@File    : account/urls.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-11-25
@Description : 사용자 계정 URL 라우팅
"""

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]