from django.urls import path
from . import views

urlpatterns = [
    path('', views.community_list, name='community'),
    path('meeting/<int:meeting_id>/', views.meeting_detail, name='meeting_detail'),
    path('create/', views.meeting_create, name='meeting_create'),
    path('meeting/<int:meeting_id>/join/', views.meeting_join, name='meeting_join'),
    path('meeting/<int:meeting_id>/cancel/', views.meeting_cancel, name='meeting_cancel'),
    path('meeting/<int:meeting_id>/submission/', views.submission_create, name='submission_create'),
]