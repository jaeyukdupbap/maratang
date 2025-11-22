# Generated manually

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('community', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PetItem',
            fields=[
                ('item_id', models.AutoField(primary_key=True, serialize=False)),
                ('item_name', models.CharField(max_length=100)),
                ('item_type', models.CharField(choices=[('snack', '간식'), ('decoration', '장식')], max_length=20)),
                ('required_level', models.IntegerField(default=1, help_text='구매 가능한 최소 레벨')),
                ('cost', models.IntegerField(help_text='필요한 포인트')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'pet_item',
                'ordering': ['required_level', 'cost'],
            },
        ),
        migrations.CreateModel(
            name='UserPet',
            fields=[
                ('user_pet_id', models.AutoField(primary_key=True, serialize=False)),
                ('pet_type', models.CharField(choices=[('otter', '수달'), ('fox', '여우')], default='otter', max_length=20)),
                ('current_level', models.IntegerField(default=1)),
                ('current_xp', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.OneToOneField(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='pet', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_pet',
            },
        ),
        migrations.CreateModel(
            name='UserInventory',
            fields=[
                ('inventory_id', models.AutoField(primary_key=True, serialize=False)),
                ('is_equipped', models.BooleanField(default=False)),
                ('acquired_at', models.DateTimeField(auto_now_add=True)),
                ('item_id', models.ForeignKey(db_column='item_id', on_delete=django.db.models.deletion.CASCADE, related_name='owned_by_users', to='growth.petitem')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_inventory',
                'ordering': ['-acquired_at'],
                'unique_together': {('user_id', 'item_id')},
            },
        ),
        migrations.CreateModel(
            name='PointsHistory',
            fields=[
                ('point_id', models.AutoField(primary_key=True, serialize=False)),
                ('points_change', models.IntegerField(help_text='+100 or -50 등')),
                ('reason', models.CharField(choices=[('ai_approval', 'AI 승인'), ('admin_approval', '관리자 승인'), ('item_purchase', '아이템 구매'), ('meeting_participation', '모임 참여')], max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item_id', models.ForeignKey(blank=True, db_column='item_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='points_history', to='growth.petitem')),
                ('meeting_id', models.ForeignKey(blank=True, db_column='meeting_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='points_history', to='community.communitymeeting')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='points_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'points_history',
                'ordering': ['-created_at'],
            },
        ),
    ]


