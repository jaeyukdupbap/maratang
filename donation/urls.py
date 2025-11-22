from django.urls import path
from . import views

urlpatterns = [
    path('', views.donation, name='donation'),
    path('history/<int:pool_id>/', views.donation_history, name='donation_history'),
]