from core.errors import Conflict


class TagExists(Conflict):
    """Renaming onto another tag's name: the teacher must confirm the merge (T-18)."""

    code = "tag_exists"
    title = "A tag with this name already exists"


class TestChangedElsewhere(Conflict):
    """The save was based on an older revision: another tab changed the test (E-34)."""

    code = "test_changed_elsewhere"
    title = "This test was changed elsewhere"


class SectionNotEmpty(Conflict):
    """Deleting a section that still has questions needs a choice: move them or delete them."""

    code = "section_not_empty"
    title = "This section still has questions"


class TestHasProblems(Conflict):
    """Only a test without validation problems can be assigned (domain_model.md §3.5 #1)."""

    code = "test_has_problems"
    title = "Fix the problems in this test before assigning it"
