# Generated by Django 4.2.7 on 2023-12-03 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0019_alter_friendrequest_from_user_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="friends",
        ),
        migrations.AddField(
            model_name="user",
            name="friends",
            field=models.ManyToManyField(to="user.user"),
        ),
        migrations.AlterField(
            model_name="friendrequest",
            name="from_user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sent_requests",
                to="user.user",
            ),
        ),
        migrations.AlterField(
            model_name="friendrequest",
            name="to_user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="received_requests",
                to="user.user",
            ),
        ),
    ]
