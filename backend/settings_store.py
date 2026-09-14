"""Persists the last-used Raw Data form settings across app restarts.

A small JSON file next to the database, not a table in it: this is just a
handful of short-lived strings (column numbers, nlc, ...) read back once at
startup to seed the form's defaults, not relational data anyone ever queries.
"""

from __future__ import annotations

import json
import os

_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "raw_data_settings.json")


def load_raw_data_settings() -> dict | None:
    """The last-saved settings dict, or None on first run (or if the file is
    missing/corrupt - never raises, since losing a remembered default isn't
    worth failing app startup over)."""
    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_raw_data_settings(params: dict) -> None:
    """Overwrites the saved settings with `params`. Extra keys (e.g.
    has_step) are harmless - only the raw_data_form field names are ever
    read back."""
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(params, f)
