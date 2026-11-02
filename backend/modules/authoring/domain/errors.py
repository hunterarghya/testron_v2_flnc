from core.errors import Conflict


class TagExists(Conflict):
    """Renaming onto another tag's name: the teacher must confirm the merge (T-18)."""

    code = "tag_exists"
    title = "A tag with this name already exists"
