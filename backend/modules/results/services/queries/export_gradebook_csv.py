from dataclasses import dataclass
from uuid import UUID

from core.context import Ctx
from modules.results.domain.breakdown import INDIA, section_titles
from modules.results.domain.csv_export import csv_file_name, to_csv
from modules.results.services.queries.get_gradebook import GradebookRow, get_gradebook


@dataclass(frozen=True, slots=True)
class CsvFile:
    name: str
    text: str


def export_gradebook_csv(ctx: Ctx, *, assignment_id: UUID) -> CsvFile:
    """T-11 Export → Gradebook (CSV) (domain_model.md §6.6): one row per student per take,
    absent students included, sections as columns. The only export made on the server."""
    book = get_gradebook(ctx, assignment_id=assignment_id)
    titles = section_titles(book.frame.paper)
    sections = [title or f"Section {i + 1}" for i, title in enumerate(titles)]
    header = ["Student", "Take", "Status", "Score", "Max", "Rank", *sections, "Minutes", "Warnings"]
    title = book.frame.row.record.settings.title
    date = ctx.now.astimezone(INDIA).date().isoformat()
    return CsvFile(
        csv_file_name(title, date), to_csv(header, [_cells(r, len(sections)) for r in book.rows])
    )


def _cells(row: GradebookRow, section_count: int) -> list[object]:
    attempt = row.attempt
    parts: list[object] = [part.score for part in row.sections] or [""] * section_count
    return [
        row.name,
        attempt.take_number if attempt else "",
        row.status,
        attempt.score if attempt and attempt.score is not None else "",
        attempt.max_score if attempt else "",
        row.placing.rank if row.placing else "",
        *parts,
        round(row.time_taken_s / 60) if row.time_taken_s is not None else "",
        attempt.warning_count if attempt else "",
    ]
