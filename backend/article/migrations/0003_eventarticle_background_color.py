# Generated by Django 4.2.7 on 2024-01-02 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0002_eventarticle'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventarticle',
            name='background_color',
            field=models.CharField(default='0xffEEE7F7', max_length=10),
        ),
    ]
