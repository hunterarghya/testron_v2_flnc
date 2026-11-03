"""The audit can't be rewritten (database_schema.md §3.8, security.md T-07)."""

from django.db import migrations

CREATE = """
CREATE FUNCTION audit_entries_refuse_change() RETURNS trigger AS $$
BEGIN
    -- The one change allowed: forgetting who acted, when that user is deleted (SET NULL)
    IF TG_OP = 'UPDATE' AND NEW.actor_id IS NULL
       AND (NEW.id, NEW.action, NEW.target_type, NEW.target_id, NEW.data, NEW.at)
           IS NOT DISTINCT FROM (OLD.id, OLD.action, OLD.target_type, OLD.target_id, OLD.data, OLD.at) THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'audit entries are append-only'
        USING ERRCODE = 'integrity_constraint_violation';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_entries_append_only
    BEFORE UPDATE OR DELETE ON audit_entries
    FOR EACH ROW EXECUTE FUNCTION audit_entries_refuse_change();
"""

DROP = """
DROP TRIGGER IF EXISTS audit_entries_append_only ON audit_entries;
DROP FUNCTION IF EXISTS audit_entries_refuse_change();
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_audit_entries")]

    operations = [migrations.RunSQL(CREATE, DROP)]
