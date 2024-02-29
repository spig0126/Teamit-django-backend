# Generated by Django 4.2.7 on 2024-01-16 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0031_user_uid_alter_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='visibility',
            field=models.CharField(choices=[('PU', '전체 공개'), ('PI', '비공개'), ('FO', '팔로우 공개')], default='PU', max_length=2),
        ),
    ]
