# The numbers in "Deleted student #n" (database_schema.md §3.2, §8.3): a sequence, so
# two deletions at the same moment never get the same number.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE students_anonymized_seq START 1",
            reverse_sql="DROP SEQUENCE students_anonymized_seq",
        ),
    ]
