# Generated by Django 5.1.3 on 2025-07-14 02:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0013_parkingticket_amount_received_parkingticket_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingticket',
            name='forma_pago',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Forma de pago'),
        ),
    ]
