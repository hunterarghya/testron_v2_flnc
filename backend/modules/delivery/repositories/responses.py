import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.db import connection

from core.rich_content import Json
from modules.delivery.models import Response


@dataclass(frozen=True, slots=True)
class StoredResponse:
    answer: Json | None
    marked_for_review: bool
    visited: bool
    client_seq: int


# One statement: an older retry is acknowledged and ignored (database_schema.md §3.6, E-05)
_SAVE = """
INSERT INTO responses AS r
    (attempt_id, question_id, answer, marked_for_review, first_visited_at, client_seq, saved_at)
VALUES (%(attempt)s, %(question)s, %(answer)s::jsonb, %(marked)s, %(now)s, %(seq)s, %(now)s)
ON CONFLICT (attempt_id, question_id) DO UPDATE
   SET answer = EXCLUDED.answer, marked_for_review = EXCLUDED.marked_for_review,
       client_seq = EXCLUDED.client_seq, saved_at = EXCLUDED.saved_at,
       first_visited_at = COALESCE(r.first_visited_at, EXCLUDED.first_visited_at)
 WHERE r.client_seq < EXCLUDED.client_seq
RETURNING 1
"""

# Seen but not answered: the palette's "not answered" state. Never touches an answer
_VISIT = """
INSERT INTO responses AS r
    (attempt_id, question_id, answer, marked_for_review, first_visited_at, client_seq, saved_at)
VALUES (%(attempt)s, %(question)s, NULL, FALSE, %(now)s, 0, %(now)s)
ON CONFLICT (attempt_id, question_id) DO UPDATE
   SET first_visited_at = COALESCE(r.first_visited_at, EXCLUDED.first_visited_at)
"""


def save(  # keyword-only after the ids (CLAUDE.md limits)
    attempt_id: UUID,
    question_id: UUID,
    *,
    answer: Json | None,
    marked_for_review: bool,
    client_seq: int,
    now: datetime,
) -> bool:
    """True when stored; False when a newer save is already there."""
    params = {
        "attempt": attempt_id,
        "question": question_id,
        "answer": None if answer is None else json.dumps(answer),
        "marked": marked_for_review,
        "seq": client_seq,
        "now": now,
    }
    with connection.cursor() as cursor:
        cursor.execute(_SAVE, params)
        return cursor.fetchone() is not None


def visit(attempt_id: UUID, question_id: UUID, *, now: datetime) -> None:
    with connection.cursor() as cursor:
        cursor.execute(_VISIT, {"attempt": attempt_id, "question": question_id, "now": now})


def of_attempt(attempt_id: UUID) -> dict[UUID, StoredResponse]:
    rows = Response.objects.filter(attempt_id=attempt_id).values_list(
        "question_id", "answer", "marked_for_review", "first_visited_at", "client_seq"
    )
    return {
        question_id: StoredResponse(answer, marked, visited is not None, seq)
        for question_id, answer, marked, visited, seq in rows
    }
