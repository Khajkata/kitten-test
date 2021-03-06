# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-03 19:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('participants', '0001_initial'),
        ('breakqual', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='breakingteam',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='participants.Team'),
        ),
        migrations.AddField(
            model_name='breakcategory',
            name='breaking_teams',
            field=models.ManyToManyField(through='breakqual.BreakingTeam', to='participants.Team'),
        ),
    ]
