from django.urls import path
from . import views

urlpatterns = [
    path('count/', views.notification_count, name='notification_count'),
    path('list/', views.notification_list_api, name='notification_list_api'),
]
