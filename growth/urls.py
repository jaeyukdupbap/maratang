from django.urls import path
from . import views

urlpatterns = [
    path('', views.growth, name='growth'),
    path('pet-select/', views.pet_select, name='pet_select'),
    path('purchase/<int:item_id>/', views.purchase_item, name='purchase_item'),
    path('equip/<int:inventory_id>/', views.equip_item, name='equip_item'),
    path('shop/', views.shop, name='shop'),
]