# Generated by Django 4.2.7 on 2024-03-21 06:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("badge", "0005_remove_badge_shared_profile_cnt_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="badge",
            name="attendance_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="friendship_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="liked_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="recruit_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="review_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="shared_profile_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="team_leader_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="team_participance_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="team_post_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="team_refusal_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="badge",
            name="user_profile_change",
            field=models.BooleanField(default=False),
        ),
    ]
