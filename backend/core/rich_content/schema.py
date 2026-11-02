"""The rich-content allow-list and its limits (editor_content_spec.md §1-§2).

The TipTap editor, this validator and RichContentView must agree on this list: adding a
node means changing all three (project_structure.md, "Add an allowed rich-content node").
"""

import re
from enum import StrEnum


class Profile(StrEnum):
    # Question stem, solution, test and section instructions
    FULL = "full"
    # MCQ/MSQ options: up to 3 paragraphs, inline math, one image
    COMPACT = "compact"


VERSION = 1
# The fixed order marks are stored in, so equal content is stored the same way
MARK_ORDER = ("bold", "italic", "underline", "subscript", "superscript")
EXCLUSIVE_MARKS = frozenset({"subscript", "superscript"})

MAX_BYTES = {Profile.FULL: 64 * 1024, Profile.COMPACT: 8 * 1024}
MAX_DEPTH = 8
MAX_NODES = 2000
MAX_TEXT_LENGTH = 5000
MAX_LATEX_LENGTH = 2000
MAX_LIST_ITEMS = 50
MAX_LIST_DEPTH = 3
MAX_TABLE_ROWS = 20
MAX_TABLE_COLUMNS = 8
MAX_COMPACT_PARAGRAPHS = 3
MAX_COMPACT_IMAGES = 1

IMAGE_PROVIDERS = frozenset({"imagekit"})
IMAGE_SIZES = frozenset({"S", "M", "L", "FULL"})
IMAGE_FILE_ID = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
MAX_IMAGE_SIDE = 10_000
MAX_IMAGE_LABEL_LENGTH = 300

# Blocks each profile allows; inline content is the same everywhere
FULL_BLOCKS = frozenset({"paragraph", "bulletList", "orderedList", "table", "image", "math"})
COMPACT_BLOCKS = frozenset({"paragraph", "image"})
INLINE_NODES = frozenset({"text", "hardBreak", "math"})
