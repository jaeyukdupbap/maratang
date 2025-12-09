from django.urls import path
from . import views

urlpatterns = [
    path('', views.growth, name='growth'),
    path('pet-select/', views.pet_select, name='pet_select'),
    path('pet-change/', views.change_pet, name='pet_change'),
    path('purchase/<int:item_id>/', views.purchase_item, name='purchase_item'),
    path('equip/<int:inventory_id>/', views.equip_item, name='equip_item'),
    path('shop/', views.shop, name='shop'),
    # 마이룸 관련 URL
    path('my-room/', views.my_room, name='my_room'),
    path('buy-room-item/<int:room_item_id>/', views.buy_room_item, name='buy_room_item'),
    path('update-decoration/<int:decoration_id>/', views.update_decoration_position, name='update_decoration_position'),
    path('toggle-decoration/<int:decoration_id>/', views.toggle_decoration_display, name='toggle_decoration_display'),
]
