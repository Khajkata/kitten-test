# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-23 17:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motions', '0006_auto_20160621_1129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='motion',
            name='text',
            field=models.TextField(help_text='The full motion e.g., "This House would straighten all bananas"', max_length=500),
        ),
    ]
