# Generated manually

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DonationPool',
            fields=[
                ('pool_id', models.AutoField(primary_key=True, serialize=False)),
                ('current_points', models.IntegerField(default=0, help_text='모든 PointsHistory의 points_change > 0 합계')),
                ('goal_points', models.IntegerField()),
                ('status', models.CharField(choices=[('open', '진행 중'), ('completed', '완료')], default='open', max_length=20)),
                ('title', models.CharField(help_text="예: '유기동물 보호소 간식 기부'", max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'donation_pool',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DonationHistory',
            fields=[
                ('donation_id', models.AutoField(primary_key=True, serialize=False)),
                ('contributed_points', models.IntegerField(help_text='해당 pool에 대한 기여분')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('pool_id', models.ForeignKey(db_column='pool_id', on_delete=django.db.models.deletion.CASCADE, related_name='donation_history', to='donation.donationpool')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='donation_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'donation_history',
                'ordering': ['-contributed_points', '-created_at'],
                'unique_together': {('pool_id', 'user_id')},
            },
        ),
    ]


