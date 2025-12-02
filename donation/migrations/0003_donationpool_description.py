from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0002_donationpool_sponsor_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='donationpool',
            name='description',
            field=models.TextField(
                null=True,
                blank=True,
                help_text='캠페인 상세 설명',
            ),
        ),
    ]


