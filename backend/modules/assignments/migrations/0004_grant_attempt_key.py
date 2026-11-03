# Written by hand: the plain id becomes a key to delivery's attempts (ADR-069, ADR-074).
# No attempt could exist before this, so every grant is still unused and nothing is lost.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0003_source_groups'),
        ('delivery', '0001_attempts'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='retakegrant',
            name='retake_grants_open',
        ),
        migrations.RemoveField(
            model_name='retakegrant',
            name='consumed_by_attempt_id',
        ),
        migrations.AddField(
            model_name='retakegrant',
            name='consumed_by_attempt',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='+', to='delivery.attempt'),
        ),
        migrations.AddIndex(
            model_name='retakegrant',
            index=models.Index(condition=models.Q(('consumed_by_attempt__isnull', True)), fields=['assignment', 'student', 'granted_at'], name='retake_grants_open'),
        ),
    ]
