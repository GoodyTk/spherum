# Generated by Django 5.1.3 on 2025-02-27 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0008_report_is_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='is_banned',
            field=models.BooleanField(default=False),
        ),
    ]
