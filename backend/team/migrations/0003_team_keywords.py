# Generated by Django 4.2.7 on 2023-12-02 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("team", "0002_teammembers_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="team",
            name="keywords",
            field=models.CharField(default=""),
        ),
    ]
