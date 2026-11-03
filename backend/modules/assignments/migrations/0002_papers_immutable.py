"""A paper never changes (database_schema.md §3.5): any UPDATE of `papers` is refused."""

from django.db import migrations

CREATE = """
CREATE FUNCTION papers_refuse_update() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'papers are immutable (assignment %)', OLD.assignment_id
        USING ERRCODE = 'integrity_constraint_violation';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER papers_immutable
    BEFORE UPDATE ON papers
    FOR EACH ROW EXECUTE FUNCTION papers_refuse_update();
"""

DROP = """
DROP TRIGGER IF EXISTS papers_immutable ON papers;
DROP FUNCTION IF EXISTS papers_refuse_update();
"""


class Migration(migrations.Migration):
    dependencies = [("assignments", "0001_assignments")]

    operations = [migrations.RunSQL(CREATE, DROP)]
