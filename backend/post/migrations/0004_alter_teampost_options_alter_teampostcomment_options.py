# Generated by Django 4.2.7 on 2024-01-20 08:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0003_remove_teampost_likes_teampost_viewed'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teampost',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='teampostcomment',
            options={'ordering': ['-created_at']},
        ),
    ]
