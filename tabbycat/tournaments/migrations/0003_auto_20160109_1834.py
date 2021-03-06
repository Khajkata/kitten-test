# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-09 18:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0002_auto_20160103_1927'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='division',
            options={'ordering': ['tournament', 'seq'], 'verbose_name': '➗ Division'},
        ),
        migrations.AlterModelOptions(
            name='round',
            options={'ordering': ['tournament', 'seq'], 'verbose_name': '⏰ Round'},
        ),
        migrations.AlterModelOptions(
            name='tournament',
            options={'ordering': ['seq'], 'verbose_name': '🏆 Tournament'},
        ),
    ]
