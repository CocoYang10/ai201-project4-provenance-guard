import json
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path("audit_log.json")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _read_entries():
    if not LOG_PATH.exists():
        return []
    try:
        with LOG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _write_entries(entries):
    with LOG_PATH.open("w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)


def add_log_entry(entry: dict):
    entries = _read_entries()
    entry_with_timestamp = {"timestamp": _now_iso(), **entry}
    entries.append(entry_with_timestamp)
    _write_entries(entries)
    return entry_with_timestamp


def get_recent_entries(limit: int = 10):
    entries = _read_entries()
    return entries[-limit:][::-1]


def update_entry_for_appeal(content_id: str, creator_reasoning: str):
    entries = _read_entries()
    for entry in entries:
        if entry.get("content_id") == content_id:
            entry["status"] = "under_review"
            entry["appeal_reasoning"] = creator_reasoning
            entry["appeal_timestamp"] = _now_iso()
            _write_entries(entries)
            return entry
    return None
