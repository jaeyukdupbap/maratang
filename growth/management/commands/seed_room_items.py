"""
@Project : Mood Garden (Community & Donation Platform)
@File    : growth/management/commands/seed_room_items.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-09
@Description : 마이룸 가구 테스트 데이터 생성 관리자 명령어
"""

from django.core.management.base import BaseCommand
from growth.models import RoomItem


class Command(BaseCommand):
    """
    RoomItem 테스트 데이터 생성 명령어
    
    사용 방법: python manage.py seed_room_items
    """
    help = '마이룸 가구 테스트 데이터를 생성합니다.'

    def handle(self, *args, **options):
        """
        마이룸 가구 데이터 생성 로직
        
        배경, 가구, 소품 등의 예시 데이터를 생성합니다.
        이미지는 ImageField에 저장되지 않으므로 관리자에서 추가해야 합니다.
        """
        # 기존 데이터 확인
        if RoomItem.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️  이미 데이터가 존재합니다. 생성을 건너뜁니다.'))
            return

        room_items = [
            # ===== 배경 =====
            {
                'item_name': '파란 벽지',
                'category': 'background',
                'cost': 100,
                'z_index': 1,
                'default_top': 0,
                'default_left': 0,
                'width': 800,
                'height': 600,
            },
            {
                'item_name': '노란 벽지',
                'category': 'background',
                'cost': 100,
                'z_index': 1,
                'default_top': 0,
                'default_left': 0,
                'width': 800,
                'height': 600,
            },
            {
                'item_name': '초록 벽지',
                'category': 'background',
                'cost': 100,
                'z_index': 1,
                'default_top': 0,
                'default_left': 0,
                'width': 800,
                'height': 600,
            },

            # ===== 가구 =====
            {
                'item_name': '빨간 쇼파',
                'category': 'furniture',
                'cost': 200,
                'z_index': 10,
                'default_top': 350,
                'default_left': 50,
                'width': 200,
                'height': 150,
            },
            {
                'item_name': '검은 의자',
                'category': 'furniture',
                'cost': 150,
                'z_index': 10,
                'default_top': 350,
                'default_left': 300,
                'width': 100,
                'height': 100,
            },
            {
                'item_name': '나무 책장',
                'category': 'furniture',
                'cost': 250,
                'z_index': 10,
                'default_top': 100,
                'default_left': 600,
                'width': 150,
                'height': 200,
            },
            {
                'item_name': '침대',
                'category': 'furniture',
                'cost': 300,
                'z_index': 10,
                'default_top': 200,
                'default_left': 400,
                'width': 250,
                'height': 200,
            },

            # ===== 소품 =====
            {
                'item_name': '벽걸이 TV',
                'category': 'accessory',
                'cost': 180,
                'z_index': 20,
                'default_top': 50,
                'default_left': 300,
                'width': 180,
                'height': 120,
            },
            {
                'item_name': '화분',
                'category': 'accessory',
                'cost': 80,
                'z_index': 15,
                'default_top': 400,
                'default_left': 700,
                'width': 80,
                'height': 100,
            },
            {
                'item_name': '테이블',
                'category': 'accessory',
                'cost': 120,
                'z_index': 12,
                'default_top': 350,
                'default_left': 500,
                'width': 120,
                'height': 100,
            },
            {
                'item_name': '선선한 선풍기',
                'category': 'accessory',
                'cost': 90,
                'z_index': 25,
                'default_top': 50,
                'default_left': 100,
                'width': 80,
                'height': 80,
            },
            {
                'item_name': '포스터',
                'category': 'accessory',
                'cost': 50,
                'z_index': 3,
                'default_top': 100,
                'default_left': 50,
                'width': 150,
                'height': 200,
            },
        ]

        created_count = 0
        for item_data in room_items:
            room_item, created = RoomItem.objects.get_or_create(**item_data)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {room_item.item_name} ({room_item.get_category_display()}) 생성됨')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⊗ {room_item.item_name} 이미 존재')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ 총 {created_count}개의 마이룸 가구가 생성되었습니다!')
        )
        self.stdout.write(
            self.style.WARNING('\n💡 주의: 이미지는 관리자 페이지에서 개별적으로 업로드해야 합니다.')
        )
