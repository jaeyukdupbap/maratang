from django.urls import path
from . import views

urlpatterns = [
    path('', views.mypage, name='mypage'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.notification_read, name='notification_read'),
]
