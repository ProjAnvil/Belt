#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

SESSIONS_DIR = Path.home() / ".belt" / "sessions"


def session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def load_state(session_id: str) -> dict:
    path = session_path(session_id)
    if not path.exists():
        print(json.dumps({"error": f"Session '{session_id}' not found at {path}"}))
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    state["updated_at"] = _now()
    session_id: str = state["session_id"]
    path = session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}))
    sys.exit(code)


def _ok(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))
