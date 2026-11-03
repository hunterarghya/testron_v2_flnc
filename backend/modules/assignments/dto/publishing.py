"""Publishing results (api_contract.md §2.7; D-01, T-11)."""

from ninja import Schema
from pydantic import ConfigDict, Field

from modules.assignments.domain.publishing import PublicationChanges
from modules.assignments.domain.values import PublicationMode, PublishContent


class PublicationOptionsIn(Schema):
    """What a visible result shows (domain_model.md §6.4); leave out to keep."""

    model_config = ConfigDict(extra="forbid")
    content: PublishContent | None = None
    show_paper: bool | None = None
    show_solutions: bool | None = None
    show_rank_and_stats: bool | None = None

    def to_changes(self) -> PublicationChanges:
        return PublicationChanges(
            content=self.content,
            show_paper=self.show_paper,
            show_solutions=self.show_solutions,
            show_rank_and_stats=self.show_rank_and_stats,
        )


class PublishIn(Schema):
    model_config = ConfigDict(extra="forbid")
    options: PublicationOptionsIn | None = None


class PublicationPatchIn(PublicationOptionsIn):
    mode: PublicationMode | None = None
    delay_s: int | None = Field(default=None, gt=0)

    def to_changes(self) -> PublicationChanges:
        base = super().to_changes()
        return PublicationChanges(
            mode=self.mode,
            delay_s=self.delay_s,
            content=base.content,
            show_paper=base.show_paper,
            show_solutions=base.show_solutions,
            show_rank_and_stats=base.show_rank_and_stats,
        )
