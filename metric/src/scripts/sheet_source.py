#!/usr/bin/env python3
"""Read AIRBDS metric source tabs from the public Google Sheet.

The sheet is shared "anyone with the link", so each tab is pulled with no auth
via the public CSV export endpoint. Tabs are located by *content* (not a
hard-coded gid) so the script keeps working if gids change.

The `CsvWorksheet` adapter exposes the small slice of the openpyxl Worksheet API
the metric build readers use — `.cell(row, col).value` (1-based), `.max_row`,
`.max_column` — with the same value typing as `load_workbook(data_only=True)`
(numbers come back as int/float, blanks as None). That lets the readers run
unchanged on either an .xlsx (v0.3) or a sheet CSV export (v0.4+).
"""
from __future__ import annotations

import csv
import io
import re
import urllib.request

BASE = "https://docs.google.com/spreadsheets/d"

# A real-ish User-Agent: the default urllib agent is sometimes refused by Google.
_UA = "Mozilla/5.0 (X11; Linux x86_64) AIRBDS-metric-build"


def extract_spreadsheet_id(url_or_id: str) -> str:
    """Pull the spreadsheet id out of a full URL, or accept a bare id."""
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", url_or_id)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]+", url_or_id.strip()):
        return url_or_id.strip()
    raise ValueError(f"Could not extract a spreadsheet id from {url_or_id!r}")


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as resp:  # public sheet, no auth
        return resp.read().decode("utf-8")


def discover_gids(sheet_id: str) -> list[str]:
    """Discover tab gids from the spreadsheet's htmlview page."""
    html = _get(f"{BASE}/{sheet_id}/htmlview")
    gids = {m.group(1) for m in re.finditer(r"[?&#]gid=(\d+)", html)}
    gids.add("0")  # always try the default tab
    return sorted(gids, key=int)


def fetch_tab_csv(sheet_id: str, gid: str) -> str:
    """Fetch one tab as CSV text via the public export endpoint."""
    return _get(f"{BASE}/{sheet_id}/export?format=csv&gid={gid}")


def fetch_named_tabs(sheet_id: str, classifiers: dict) -> dict:
    """Fetch every tab and return {name: csv_text} for each matched classifier.

    `classifiers` maps a name to a predicate `(csv_text) -> bool`. Classifying by
    content (rather than gid) means the canonical sheet keeps working if tab gids
    change. Raises if any classifier matches no tab.
    """
    found: dict[str, str] = {}
    for gid in discover_gids(sheet_id):
        csv_text = fetch_tab_csv(sheet_id, gid)
        for name, is_match in classifiers.items():
            if name not in found and is_match(csv_text):
                found[name] = csv_text
        if len(found) == len(classifiers):
            break
    missing = [n for n in classifiers if n not in found]
    if missing:
        raise RuntimeError(
            f"Could not find tab(s) {missing} in sheet {sheet_id}. "
            'Ensure it is shared "anyone with the link" and follows the AIRBDS '
            "metric template."
        )
    return found


def _coerce(value):
    """Mimic openpyxl data_only typing: '' -> None, ints/floats parsed, else str."""
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    try:
        return float(s)
    except ValueError:
        return value  # keep the original string (incl. any surrounding spaces)


class _Cell:
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value


class CsvWorksheet:
    """Read-only, openpyxl-like view over a parsed CSV grid (1-based indexing)."""

    def __init__(self, csv_text: str):
        self._rows = list(csv.reader(io.StringIO(csv_text)))
        self.max_row = len(self._rows)
        self.max_column = max((len(r) for r in self._rows), default=0)

    def cell(self, row: int, column: int) -> _Cell:
        r, c = row - 1, column - 1
        if 0 <= r < len(self._rows) and 0 <= c < len(self._rows[r]):
            return _Cell(_coerce(self._rows[r][c]))
        return _Cell(None)
