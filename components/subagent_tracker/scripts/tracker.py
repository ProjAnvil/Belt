#!/usr/bin/env python3
"""
Subagent tracker: fork-and-collect state machine for orchestrating subagents.

Each task carries:
  - global_context  — shared project/environment data for all subagents
  - task context    — task-specific data
  - todos           — structured checklist passed into the subagent prompt

Usage:
  tracker.py init    --session <id> --tasks <json-file> [--context <json-file>]
  tracker.py next    --session <id>
  tracker.py report  --session <id> --task <id> [--result <json-string>]
  tracker.py fail    --session <id> --task <id> [--error <msg>]
  tracker.py status  --session <id>
  tracker.py done    --session <id>
  tracker.py results --session <id>
  tracker.py list
  tracker.py cleanup [--older-than <days>]
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from util import session_path, load_state, save_state, _now, _die, _ok, SESSIONS_DIR


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args):
    """Create a dispatch session from a tasks file and optional global context file."""
    session_id = args.session
    tasks_file = Path(args.tasks)

    if not tasks_file.exists():
        _die(f"Tasks file not found: {tasks_file}")

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            raw_tasks = json.load(f)
    except json.JSONDecodeError as e:
        _die(f"Invalid JSON in tasks file: {e}")
    except Exception as e:
        _die(f"Failed to read tasks file: {e}")

    if not isinstance(raw_tasks, list):
        _die("Tasks file must contain a JSON array")
    if not raw_tasks:
        _die("Tasks array cannot be empty")

    for idx, task in enumerate(raw_tasks):
        if not isinstance(task, dict):
            _die(f"Task at index {idx} is not an object")
        if "id" not in task:
            _die(f"Task at index {idx} missing required 'id' field")
        if "description" not in task:
            _die(f"Task at index {idx} missing required 'description' field")

    # Load optional global context
    global_context = {}
    if args.context:
        ctx_file = Path(args.context)
        if not ctx_file.exists():
            _die(f"Context file not found: {ctx_file}")
        try:
            with open(ctx_file, "r", encoding="utf-8") as f:
                global_context = json.load(f)
        except json.JSONDecodeError as e:
            _die(f"Invalid JSON in context file: {e}")
        except Exception as e:
            _die(f"Failed to read context file: {e}")
        if not isinstance(global_context, dict):
            _die("Context file must contain a JSON object")

    if session_path(session_id).exists():
        _die(f"Session '{session_id}' already exists. Use a different session ID.")

    tasks = []
    for raw in raw_tasks:
        tasks.append(
            {
                "id": raw["id"],
                "description": raw["description"],
                "agent": raw.get("agent", None),
                "todos": raw.get("todos", []),
                "context": raw.get("context", {}),
                "status": "pending",
                "dispatched_at": None,
                "completed_at": None,
                "result": None,
                "error": None,
            }
        )

    state = {
        "session_id": session_id,
        "created_at": _now(),
        "updated_at": _now(),
        "global_context": global_context,
        "tasks": tasks,
    }

    save_state(state)

    _ok(
        {
            "session_id": session_id,
            "total_tasks": len(tasks),
            "global_context_keys": list(global_context.keys()),
        }
    )


def cmd_next(args):
    """Return the next pending task as a full dispatch payload. Marks it 'dispatched'.

    Idempotent: if a task is already 'dispatched' (i.e. the agent crashed before
    reporting), it is returned again so the caller can retry.
    Exit code 2 when no pending/dispatched tasks remain.
    """
    session_id = args.session
    state = load_state(session_id)

    # Prefer re-returning an already-dispatched task (crash recovery)
    task = next((t for t in state["tasks"] if t["status"] == "dispatched"), None)

    if task is None:
        task = next((t for t in state["tasks"] if t["status"] == "pending"), None)
        if task is None:
            _die("No more pending tasks", code=2)
        task["status"] = "dispatched"
        task["dispatched_at"] = _now()
        save_state(state)

    _ok(
        {
            "task_id": task["id"],
            "description": task["description"],
            "agent": task["agent"],
            "todos": task["todos"],
            "context": {
                "global": state["global_context"],
                "task": task["context"],
            },
        }
    )


def cmd_report(args):
    """Store a subagent's result and mark the task done."""
    session_id = args.session
    task_id = args.task
    state = load_state(session_id)

    task = next((t for t in state["tasks"] if t["id"] == task_id), None)
    if not task:
        _die(f"Task '{task_id}' not found in session")

    if task["status"] == "done":
        _ok({"message": f"Task '{task_id}' already reported as done", "task_id": task_id})
        return

    result = None
    if args.result:
        try:
            result = json.loads(args.result)
        except json.JSONDecodeError:
            result = args.result  # store raw string if caller passed plain text

    task["status"] = "done"
    task["completed_at"] = _now()
    task["result"] = result
    task["error"] = None
    save_state(state)

    _ok({"message": f"Task '{task_id}' reported as done", "task_id": task_id})


def cmd_fail(args):
    """Mark a task as failed."""
    session_id = args.session
    task_id = args.task
    error_msg = args.error or "Unspecified error"
    state = load_state(session_id)

    task = next((t for t in state["tasks"] if t["id"] == task_id), None)
    if not task:
        _die(f"Task '{task_id}' not found in session")

    task["status"] = "failed"
    task["completed_at"] = _now()
    task["error"] = error_msg
    save_state(state)

    _ok(
        {
            "message": f"Task '{task_id}' marked as failed",
            "task_id": task_id,
            "error": error_msg,
        }
    )


def cmd_status(args):
    """Print a JSON progress summary."""
    session_id = args.session
    state = load_state(session_id)
    tasks = state["tasks"]

    _ok(
        {
            "session_id": session_id,
            "created_at": state["created_at"],
            "updated_at": state["updated_at"],
            "tasks": {
                "total": len(tasks),
                "done": sum(1 for t in tasks if t["status"] == "done"),
                "failed": sum(1 for t in tasks if t["status"] == "failed"),
                "dispatched": sum(1 for t in tasks if t["status"] == "dispatched"),
                "pending": sum(1 for t in tasks if t["status"] == "pending"),
            },
        }
    )


def cmd_done(args):
    """Exit 0 when all tasks are settled (done/failed). Exit 1 if any remain."""
    state = load_state(args.session)
    pending = sum(
        1 for t in state["tasks"] if t["status"] in ["pending", "dispatched"]
    )
    if pending > 0:
        _ok({"done": False, "pending_tasks": pending})
        sys.exit(1)
    else:
        _ok({"done": True})
        sys.exit(0)


def cmd_results(args):
    """Return all collected subagent results for a session."""
    state = load_state(args.session)
    results = [
        {
            "task_id": t["id"],
            "description": t["description"],
            "agent": t["agent"],
            "status": t["status"],
            "result": t["result"],
            "error": t["error"],
            "dispatched_at": t["dispatched_at"],
            "completed_at": t["completed_at"],
        }
        for t in state["tasks"]
    ]
    _ok({"session_id": args.session, "results": results})


def cmd_list(args):
    """List all dispatch sessions with summary stats."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sessions = []
    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            # Only include sessions that look like dispatcher sessions
            if "tasks" not in state or "global_context" not in state:
                continue
            tasks = state["tasks"]
            sessions.append(
                {
                    "session_id": state["session_id"],
                    "created_at": state["created_at"],
                    "updated_at": state["updated_at"],
                    "total_tasks": len(tasks),
                    "done": sum(1 for t in tasks if t["status"] == "done"),
                    "failed": sum(1 for t in tasks if t["status"] == "failed"),
                    "pending": sum(
                        1 for t in tasks if t["status"] in ["pending", "dispatched"]
                    ),
                }
            )
        except Exception:
            continue
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    _ok({"sessions": sessions, "total": len(sessions)})


def cmd_cleanup(args):
    """Remove sessions older than N days."""
    older_than_days = args.older_than
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    removed = []
    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            updated_at = datetime.fromisoformat(state["updated_at"])
            if updated_at < cutoff:
                session_file.unlink()
                removed.append(state["session_id"])
        except Exception:
            continue
    _ok({"removed": removed, "count": len(removed), "older_than_days": older_than_days})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Subagent tracker: fork-and-collect orchestration state machine"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p = sub.add_parser("init", help="Create a dispatch session")
    p.add_argument("--session", required=True, help="Session ID")
    p.add_argument("--tasks", required=True, help="Path to tasks JSON file")
    p.add_argument("--context", default=None, help="Path to global context JSON file")

    # next
    p = sub.add_parser("next", help="Get next task dispatch payload")
    p.add_argument("--session", required=True, help="Session ID")

    # report
    p = sub.add_parser("report", help="Store subagent result for a task")
    p.add_argument("--session", required=True, help="Session ID")
    p.add_argument("--task", required=True, help="Task ID")
    p.add_argument("--result", default=None, help="Result JSON string (optional)")

    # fail
    p = sub.add_parser("fail", help="Mark a task as failed")
    p.add_argument("--session", required=True, help="Session ID")
    p.add_argument("--task", required=True, help="Task ID")
    p.add_argument("--error", default=None, help="Error message")

    # status
    p = sub.add_parser("status", help="Show progress summary")
    p.add_argument("--session", required=True, help="Session ID")

    # done
    p = sub.add_parser("done", help="Check if all tasks settled")
    p.add_argument("--session", required=True, help="Session ID")

    # results
    p = sub.add_parser("results", help="Return all collected results")
    p.add_argument("--session", required=True, help="Session ID")

    # list
    sub.add_parser("list", help="List all dispatcher sessions")

    # cleanup
    p = sub.add_parser("cleanup", help="Remove old sessions")
    p.add_argument(
        "--older-than",
        type=int,
        default=7,
        dest="older_than",
        help="Remove sessions older than N days (default: 7)",
    )

    args = parser.parse_args()

    handlers = {
        "init": cmd_init,
        "next": cmd_next,
        "report": cmd_report,
        "fail": cmd_fail,
        "status": cmd_status,
        "done": cmd_done,
        "results": cmd_results,
        "list": cmd_list,
        "cleanup": cmd_cleanup,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
