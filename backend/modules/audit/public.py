"""The only names other modules may import from audit (R-08)."""

from modules.audit.repositories.entries import entries_for
from modules.audit.services.commands.record import record

__all__ = ["entries_for", "record"]
