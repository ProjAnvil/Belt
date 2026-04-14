#!/usr/bin/env python3
"""
Generic batch state machine for persistent LLM orchestration.
Solves context-loss problem in long batch runs.

Usage:
  batch_manager.py plan --session <id> --items <json-file> [--batch-size N]
  batch_manager.py next --session <id>
  batch_manager.py complete --session <id> --item <id>
  batch_manager.py fail --session <id> --item <id> [--error <msg>]
  batch_manager.py status --session <id>
  batch_manager.py done --session <id>
  batch_manager.py resume --session <id>
  batch_manager.py list
  batch_manager.py cleanup [--older-than <days>]
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Import utilities from same directory
sys.path.insert(0, os.path.dirname(__file__))
from util import session_path, load_state, save_state, _now, _die, _ok, SESSIONS_DIR


def cmd_plan(args):
    """Create a new session by splitting items into batches."""
    session_id = args.session
    items_file = Path(args.items)
    batch_size = args.batch_size

    if not items_file.exists():
        _die(f"Items file not found: {items_file}")

    try:
        with open(items_file, "r", encoding="utf-8") as f:
            items = json.load(f)
    except json.JSONDecodeError as e:
        _die(f"Invalid JSON in items file: {e}")
    except Exception as e:
        _die(f"Failed to read items file: {e}")

    if not isinstance(items, list):
        _die("Items file must contain a JSON array")

    if not items:
        _die("Items array cannot be empty")

    # Validate all items have an 'id' field
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            _die(f"Item at index {idx} is not an object")
        if "id" not in item:
            _die(f"Item at index {idx} missing required 'id' field")

    # Check if session already exists
    if session_path(session_id).exists():
        _die(f"Session '{session_id}' already exists. Use a different session ID.")

    # Initialize items with status fields
    processed_items = []
    for item in items:
        processed_items.append(
            {
                **item,
                "status": "pending",
                "error": None,
                "completed_at": None,
                "metadata": {k: v for k, v in item.items() if k != "id"},
            }
        )

    # Split into batches
    batches = []
    for i in range(0, len(processed_items), batch_size):
        batch_items = processed_items[i : i + batch_size]
        batch_num = len(batches) + 1
        batches.append(
            {
                "batch_num": batch_num,
                "item_ids": [item["id"] for item in batch_items],
                "status": "pending",
            }
        )

    # Create state
    state = {
        "session_id": session_id,
        "created_at": _now(),
        "updated_at": _now(),
        "batch_size": batch_size,
        "items": processed_items,
        "batches": batches,
        "current_batch_num": 0,
    }

    save_state(state)

    _ok(
        {
            "session_id": session_id,
            "total_items": len(processed_items),
            "total_batches": len(batches),
            "batch_size": batch_size,
        }
    )


def cmd_next(args):
    """Get the next pending batch, mark it in_progress. Exit 2 if no more batches."""
    session_id = args.session
    state = load_state(session_id)

    # Find next pending batch or return current in_progress batch (idempotent)
    current_batch = None

    for batch in state["batches"]:
        if batch["status"] == "in_progress":
            current_batch = batch
            break

    if current_batch is None:
        for batch in state["batches"]:
            if batch["status"] == "pending":
                batch["status"] = "in_progress"
                state["current_batch_num"] = batch["batch_num"]
                current_batch = batch
                save_state(state)
                break

    if current_batch is None:
        _die("No more pending batches", code=2)

    # Get items for this batch
    batch_items = []
    for item_id in current_batch["item_ids"]:
        item = next((i for i in state["items"] if i["id"] == item_id), None)
        if item:
            batch_items.append(item)

    _ok({"batch_num": current_batch["batch_num"], "items": batch_items})


def cmd_complete(args):
    """Mark a single item as done."""
    session_id = args.session
    item_id = args.item
    state = load_state(session_id)

    # Find and update item
    item = next((i for i in state["items"] if i["id"] == item_id), None)
    if not item:
        _die(f"Item '{item_id}' not found in session")

    if item["status"] == "done":
        _ok({"message": f"Item '{item_id}' already marked as done", "item_id": item_id})
        return

    item["status"] = "done"
    item["completed_at"] = _now()
    item["error"] = None

    _maybe_close_batch(state)
    save_state(state)

    _ok({"message": f"Item '{item_id}' marked as done", "item_id": item_id})


def cmd_fail(args):
    """Mark a single item as failed."""
    session_id = args.session
    item_id = args.item
    error_msg = args.error or "Unspecified error"
    state = load_state(session_id)

    # Find and update item
    item = next((i for i in state["items"] if i["id"] == item_id), None)
    if not item:
        _die(f"Item '{item_id}' not found in session")

    item["status"] = "failed"
    item["completed_at"] = _now()
    item["error"] = error_msg

    _maybe_close_batch(state)
    save_state(state)

    _ok(
        {
            "message": f"Item '{item_id}' marked as failed",
            "item_id": item_id,
            "error": error_msg,
        }
    )


def cmd_status(args):
    """Print JSON progress summary."""
    session_id = args.session
    state = load_state(session_id)

    total_items = len(state["items"])
    done_count = sum(1 for i in state["items"] if i["status"] == "done")
    failed_count = sum(1 for i in state["items"] if i["status"] == "failed")
    in_progress_count = sum(1 for i in state["items"] if i["status"] == "in_progress")
    pending_count = sum(1 for i in state["items"] if i["status"] == "pending")

    total_batches = len(state["batches"])
    done_batches = sum(1 for b in state["batches"] if b["status"] == "done")
    in_progress_batches = sum(
        1 for b in state["batches"] if b["status"] == "in_progress"
    )
    pending_batches = sum(1 for b in state["batches"] if b["status"] == "pending")

    _ok(
        {
            "session_id": session_id,
            "created_at": state["created_at"],
            "updated_at": state["updated_at"],
            "items": {
                "total": total_items,
                "done": done_count,
                "failed": failed_count,
                "in_progress": in_progress_count,
                "pending": pending_count,
            },
            "batches": {
                "total": total_batches,
                "done": done_batches,
                "in_progress": in_progress_batches,
                "pending": pending_batches,
                "current_batch_num": state["current_batch_num"],
            },
        }
    )


def cmd_done(args):
    """Exit 0 if all items processed, exit 1 if pending remain."""
    session_id = args.session
    state = load_state(session_id)

    pending_count = sum(
        1 for i in state["items"] if i["status"] in ["pending", "in_progress"]
    )

    if pending_count > 0:
        _ok({"done": False, "pending_items": pending_count})
        sys.exit(1)
    else:
        _ok({"done": True})
        sys.exit(0)


def cmd_resume(args):
    """Read-only view of pending/in-progress items."""
    session_id = args.session
    state = load_state(session_id)

    pending_items = [
        i for i in state["items"] if i["status"] in ["pending", "in_progress"]
    ]
    pending_batches = [
        b for b in state["batches"] if b["status"] in ["pending", "in_progress"]
    ]

    _ok(
        {
            "session_id": session_id,
            "pending_items": pending_items,
            "pending_batches": pending_batches,
            "total_pending": len(pending_items),
        }
    )


def cmd_list(args):
    """List all sessions with summary stats."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    sessions = []
    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                state = json.load(f)

            total_items = len(state["items"])
            done_count = sum(1 for i in state["items"] if i["status"] == "done")
            failed_count = sum(1 for i in state["items"] if i["status"] == "failed")
            pending_count = sum(
                1 for i in state["items"] if i["status"] in ["pending", "in_progress"]
            )

            sessions.append(
                {
                    "session_id": state["session_id"],
                    "created_at": state["created_at"],
                    "updated_at": state["updated_at"],
                    "total_items": total_items,
                    "done": done_count,
                    "failed": failed_count,
                    "pending": pending_count,
                }
            )
        except Exception:
            # Skip corrupted files
            continue

    # Sort by updated_at (most recent first)
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)

    _ok({"sessions": sessions, "total": len(sessions)})


def cmd_cleanup(args):
    """Remove sessions older than N days."""
    older_than_days = args.older_than
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    removed = []
    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                state = json.load(f)

            updated_at = datetime.fromisoformat(state["updated_at"])
            if updated_at < cutoff_date:
                session_file.unlink()
                removed.append(state["session_id"])
        except Exception:
            # Skip corrupted files
            continue

    _ok({"removed": removed, "count": len(removed), "older_than_days": older_than_days})


def _maybe_close_batch(state: dict) -> None:
    """Auto-close a batch when all its items are settled (done/failed)."""
    for batch in state["batches"]:
        if batch["status"] != "in_progress":
            continue

        # Check if all items in this batch are settled
        all_settled = True
        for item_id in batch["item_ids"]:
            item = next((i for i in state["items"] if i["id"] == item_id), None)
            if item and item["status"] not in ["done", "failed"]:
                all_settled = False
                break

        if all_settled:
            batch["status"] = "done"


def main():
    parser = argparse.ArgumentParser(
        description="Generic batch state machine for persistent LLM orchestration"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # plan
    plan_parser = subparsers.add_parser("plan", help="Create a new session")
    plan_parser.add_argument("--session", required=True, help="Session ID")
    plan_parser.add_argument("--items", required=True, help="Path to items JSON file")
    plan_parser.add_argument(
        "--batch-size", type=int, default=5, help="Batch size (default: 5)"
    )

    # next
    next_parser = subparsers.add_parser("next", help="Get next pending batch")
    next_parser.add_argument("--session", required=True, help="Session ID")

    # complete
    complete_parser = subparsers.add_parser("complete", help="Mark item as done")
    complete_parser.add_argument("--session", required=True, help="Session ID")
    complete_parser.add_argument("--item", required=True, help="Item ID")

    # fail
    fail_parser = subparsers.add_parser("fail", help="Mark item as failed")
    fail_parser.add_argument("--session", required=True, help="Session ID")
    fail_parser.add_argument("--item", required=True, help="Item ID")
    fail_parser.add_argument("--error", help="Error message")

    # status
    status_parser = subparsers.add_parser("status", help="Show progress summary")
    status_parser.add_argument("--session", required=True, help="Session ID")

    # done
    done_parser = subparsers.add_parser("done", help="Check if all items processed")
    done_parser.add_argument("--session", required=True, help="Session ID")

    # resume
    resume_parser = subparsers.add_parser("resume", help="Show pending items")
    resume_parser.add_argument("--session", required=True, help="Session ID")

    # list
    subparsers.add_parser("list", help="List all sessions")

    # cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove old sessions")
    cleanup_parser.add_argument(
        "--older-than",
        type=int,
        default=7,
        help="Remove sessions older than N days (default: 7)",
    )

    args = parser.parse_args()

    # Dispatch to command handler
    command_handlers = {
        "plan": cmd_plan,
        "next": cmd_next,
        "complete": cmd_complete,
        "fail": cmd_fail,
        "status": cmd_status,
        "done": cmd_done,
        "resume": cmd_resume,
        "list": cmd_list,
        "cleanup": cmd_cleanup,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(args)
    else:
        _die(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
