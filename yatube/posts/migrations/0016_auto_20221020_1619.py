# Generated by Django 2.2.16 on 2022-10-20 09:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0015_follow'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together=set(),
        ),
    ]
