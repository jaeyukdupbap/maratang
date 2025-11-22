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
            name='CommunityMeeting',
            fields=[
                ('meeting_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('location_name', models.CharField(max_length=200)),
                ('location_coords', models.CharField(help_text='Latitude,Longitude 형식', max_length=100)),
                ('meeting_date', models.DateTimeField()),
                ('capacity', models.IntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('host_id', models.ForeignKey(db_column='host_id', on_delete=django.db.models.deletion.CASCADE, related_name='hosted_meetings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'community_meeting',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MeetingParticipant',
            fields=[
                ('participant_id', models.AutoField(primary_key=True, serialize=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('meeting_id', models.ForeignKey(db_column='meeting_id', on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='community.communitymeeting')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='participated_meetings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'meeting_participant',
                'ordering': ['-joined_at'],
                'unique_together': {('meeting_id', 'user_id')},
            },
        ),
        migrations.CreateModel(
            name='MeetingSubmission',
            fields=[
                ('submission_id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', '검토 대기'), ('ai_pass', 'AI 승인'), ('admin_pass', '관리자 승인'), ('rejected', '반려')], default='pending', max_length=20)),
                ('text_summary', models.TextField(blank=True, null=True)),
                ('admin_feedback', models.TextField(blank=True, help_text='반려 사유 등', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('host_id', models.ForeignKey(db_column='host_id', on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL)),
                ('meeting_id', models.ForeignKey(db_column='meeting_id', on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='community.communitymeeting')),
            ],
            options={
                'db_table': 'meeting_submission',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SubmissionMedia',
            fields=[
                ('media_id', models.AutoField(primary_key=True, serialize=False)),
                ('media_type', models.CharField(choices=[('scene_photo', '장소 사진'), ('selfie', '셀카')], max_length=20)),
                ('file_url', models.URLField(help_text='S3 or Storage URL', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('submission_id', models.ForeignKey(db_column='submission_id', on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='community.meetingsubmission')),
                ('user_id', models.ForeignKey(blank=True, db_column='user_id', help_text='selfie일 때 해당 셀카의 사용자 ID, scene_photo일 때는 NULL', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submission_media', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'submission_media',
                'ordering': ['created_at'],
            },
        ),
    ]


