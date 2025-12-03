from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
    ]

    operations = [
        # remove old URLField if it exists in DB schema
        migrations.RemoveField(
            model_name='submissionmedia',
            name='file_url',
        ),
        # add FileField for uploaded files
        migrations.AddField(
            model_name='submissionmedia',
            name='file',
            field=models.FileField(blank=True, max_length=500, null=True, upload_to='submission_media/%Y/%m/%d/'),
        ),
        # add processed fields to MeetingSubmission
        migrations.AddField(
            model_name='meetingsubmission',
            name='processed_by',
            field=models.ForeignKey(blank=True, db_column='processed_by', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_submissions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingsubmission',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # add processed fields to SubmissionMedia
        migrations.AddField(
            model_name='submissionmedia',
            name='processed_by',
            field=models.ForeignKey(blank=True, db_column='processed_by', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_media', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='submissionmedia',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
