# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.db import migrations

logger = logging.getLogger(__name__)


def convert_content_objects(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ActionLogEntry = apps.get_model("actionlog", "ActionLogEntry")

    for action in ActionLogEntry.objects.all():
        done = False
        for field in ('debate', 'ballot_submission', 'adjudicator_feedback',
                      'round', 'motion', 'adjudicator_test_score_history',
                      'break_category', 'adjudicator'):
            value = getattr(action, field)
            if value is not None:
                if done:
                    logger.warning("Two optional fields on %s", action)
                action.content_type = ContentType.objects.get_for_model(value)
                action.object_id = value.id
                action.save()
                done = True


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0012_add_content_object'),
        ('draw', '0010_auto_20160630_1016'),  # Debate
        ('results', '0006_auto_20160824_1208'),  # BallotSubmission
        ('adjfeedback', '0008_auto_20160726_2007'),  # AdjudicatorFeedback, AdjudicatorTestScoreHistory
        ('tournaments', '0016_auto_20160910_1057'),  # Round, Tournament (select_related by Round)
        ('motions', '0007_auto_20160723_1720'),  # Motion
        ('breakqual', '0012_convert_aida_pre2015_to_1996'),  # BreakCategory
        ('participants', '0019_allow_blank_team_reference'),  # Adjudicator, Institution (select_related by Adjudicator)
    ]

    operations = [
        migrations.RunPython(convert_content_objects, reverse_code=migrations.RunPython.noop),
    ]
