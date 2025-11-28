# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donationpool',
            name='sponsor',
            field=models.CharField(blank=True, help_text='후원사 이름', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='donationpool',
            name='start_date',
            field=models.DateField(blank=True, help_text='기부 시작일', null=True),
        ),
        migrations.AddField(
            model_name='donationpool',
            name='end_date',
            field=models.DateField(blank=True, help_text='기부 종료일', null=True),
        ),
    ]

