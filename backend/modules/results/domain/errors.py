from core.errors import DomainError


class ResultsNotPublished(DomainError):
    """A result the student may not see yet looks the same as one that doesn't exist (404,
    api_contract.md §1): nothing leaks before publication (rule 1)."""

    code = "results_not_published"
    status = 404
    title = "This result isn't available"


class PerformanceNotShared(DomainError):
    """P-10 while the teacher isn't sharing it: hidden like a missing page (security.md A-11)."""

    code = "performance_not_shared"
    status = 404
    title = "Your performance report isn't shared yet"
