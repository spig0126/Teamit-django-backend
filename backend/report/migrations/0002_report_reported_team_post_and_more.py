# Generated by Django 4.2.7 on 2023-12-27 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0003_remove_teampost_likes_teampost_viewed'),
        ('report', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='reported_team_post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='post.teampost'),
        ),
        migrations.AddField(
            model_name='report',
            name='reported_team_post_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='post.teampostcomment'),
        ),
        migrations.AlterField(
            model_name='report',
            name='reported_type',
            field=models.CharField(choices=[('user', 'User'), ('team', 'Team'), ('team_post', 'TeamPost'), ('team_post_comment', 'TeamPostComment')], max_length=17),
        ),
    ]
