from core.errors import DomainError


class ResultsNotPublished(DomainError):
    """A result the student may not see yet looks the same as one that doesn't exist (404,
    api_contract.md §1): nothing leaks before publication (rule 1)."""

    code = "results_not_published"
    status = 404
    title = "This result isn't available"
