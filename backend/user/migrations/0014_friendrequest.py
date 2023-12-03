# Generated by Django 4.2.7 on 2023-12-03 09:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0013_alter_userprofile_certificates_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="FriendRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("accepted", models.BooleanField(default=False)),
                (
                    "from_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_requests",
                        to="user.user",
                    ),
                ),
                (
                    "to_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_requests",
                        to="user.user",
                    ),
                ),
            ],
        ),
    ]
