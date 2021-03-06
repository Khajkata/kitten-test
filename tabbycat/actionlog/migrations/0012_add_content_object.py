# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-10 00:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('actionlog', '0011_auto_20160809_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlogentry',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='actionlogentry',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
