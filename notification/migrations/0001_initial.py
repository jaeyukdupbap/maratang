# Generated manually

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('community', '0001_initial'),
        ('donation', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('notification_id', models.AutoField(primary_key=True, serialize=False)),
                ('notification_type', models.CharField(choices=[('ai_approved', 'AI 자동 승인'), ('admin_review', '관리자 검토 대기'), ('admin_rejected', '인증 반려'), ('points_earned', '포인트 지급'), ('donation_completed', '기부 목표 달성')], max_length=30)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('related_meeting_id', models.ForeignKey(blank=True, db_column='related_meeting_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='community.communitymeeting')),
                ('related_pool_id', models.ForeignKey(blank=True, db_column='related_pool_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='donation.donationpool')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notification',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user_id', 'is_read'], name='notification_user_id_is_read_idx'),
        ),
    ]

