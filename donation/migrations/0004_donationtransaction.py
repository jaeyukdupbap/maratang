from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0003_donationpool_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonationTransaction',
            fields=[
                ('transaction_id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.PositiveIntegerField(help_text='기부된 포인트 양 (User Point Consumption 기준)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('pool_id', models.ForeignKey(
                    db_column='pool_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transactions',
                    to='donation.donationpool',
                )),
                ('user_id', models.ForeignKey(
                    db_column='user_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='donation_transactions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'donation_transaction',
                'ordering': ['-created_at'],
            },
        ),
    ]


