# Generated by Django 4.2.7 on 2024-01-20 08:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0005_remove_teamnotification_is_read'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='teamnotification',
            options={'ordering': ['-created_at']},
        ),
    ]
