# Generated by Django 4.2.7 on 2024-05-11 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0041_remove_userprofile_visibility_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tool",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField()),
            ],
            options={
                "managed": False,
            },
        ),
    ]
