"""Load assignment JSON from the local data directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
TEXTBOOKS_DIR = REPO_ROOT / "data" / "textbooks"


def assignment_json_path(textbook_id: str, unit_id: str) -> Path:
    return TEXTBOOKS_DIR / textbook_id / "units" / unit_id / "assignment.json"


def load_assignment(textbook_id: str, unit_id: str) -> dict[str, Any]:
    path = assignment_json_path(textbook_id, unit_id)
    if not path.is_file():
        raise FileNotFoundError(f"Assignment not found: {textbook_id}/{unit_id}")
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("assignment.json must be an object")
    return data


def assignment_pages_for(textbook_id: str, unit_id: str) -> list[dict[str, Any]]:
    data = load_assignment(textbook_id, unit_id)
    pages = data.get("assignment_pages") or []
    if not isinstance(pages, list):
        return []
    return [page for page in pages if isinstance(page, dict)]
