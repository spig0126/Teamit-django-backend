# Generated by Django 4.2.7 on 2024-04-14 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profile_card", "0003_alter_profilecard_badge_one_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profilecard",
            name="interest",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="profilecard",
            name="position",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
