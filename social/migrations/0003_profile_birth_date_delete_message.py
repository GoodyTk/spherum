# Generated by Django 5.1.3 on 2025-01-25 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0002_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='Message',
        ),
    ]
