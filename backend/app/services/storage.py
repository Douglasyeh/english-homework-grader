"""Local page-image storage. Replaceable later; not a production store."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

SUBMISSION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def storage_root() -> Path:
    override = os.environ.get("EHG_STORAGE_DIR")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "english-homework-grader"


def page_image_path(submission_id: str, page_index: int) -> Path:
    return (
        storage_root()
        / "submissions"
        / submission_id
        / "pages"
        / f"page-{page_index:03d}.png"
    )


def page_image_url(submission_id: str, page_index: int) -> str:
    return f"/api/submissions/{submission_id}/pages/{page_index}/image"
