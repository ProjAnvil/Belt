# batch-planner

Persistent batch state machine for LLM orchestration. Solves the context-loss problem when running long batch jobs — the state is stored on disk so you never lose track of progress even as context grows.

## About

This component provides scripts that must be installed before use.

Install the component scripts:
```bash
belt install batch-planner
```

## When to Use

Use this component when you need to process a large list of items across multiple agent turns and must not lose track of which items are done, pending, or failed.

## Script Location

```
~/.claude/skills/batch-planner/scripts/batch_manager.py
```

Alias: `python ~/.claude/skills/batch-planner/scripts/batch_manager.py`

## Workflow

```
1. plan   → Create session, split items into batches
2. next   → Get next batch to process (idempotent)
3. complete/fail → Mark each item as done or failed
4. status → Check progress at any time
5. done   → Check if all items are finished
```

## Commands

### plan — Create a session

```bash
python batch_manager.py plan \
  --session <session-id> \
  --items <path-to-items.json> \
  [--batch-size 5]
```

Items JSON format — array of objects, each **must** have an `id` field:
```json
[
  {"id": "project-alpha", "name": "Alpha", "priority": "high"},
  {"id": "project-beta",  "name": "Beta",  "priority": "low"}
]
```

Output:
```json
{"session_id": "my-run", "total_items": 10, "total_batches": 2, "batch_size": 5}
```

---

### next — Get the next batch

```bash
python batch_manager.py next --session <session-id>
```

Returns the next pending batch and marks it `in_progress`. **Idempotent** — safe to call again after a crash; returns the same in-progress batch.

Exit code `2` when no more batches remain.

Output:
```json
{"batch_num": 1, "items": [...]}
```

---

### complete — Mark an item done

```bash
python batch_manager.py complete --session <session-id> --item <item-id>
```

---

### fail — Mark an item failed

```bash
python batch_manager.py fail --session <session-id> --item <item-id> [--error "reason"]
```

---

### status — Progress summary

```bash
python batch_manager.py status --session <session-id>
```

Output:
```json
{
  "session_id": "my-run",
  "items": {"total": 10, "done": 3, "failed": 1, "pending": 6},
  "batches": {"total": 2, "done": 0, "in_progress": 1, "pending": 1}
}
```

---

### done — Check completion

```bash
python batch_manager.py done --session <session-id>
# exit 0 = all done, exit 1 = still pending
```

---

### resume — View pending items (read-only)

```bash
python batch_manager.py resume --session <session-id>
```

---

### list — List all sessions

```bash
python batch_manager.py list
```

---

### cleanup — Remove old sessions

```bash
python batch_manager.py cleanup [--older-than 7]
```

## Agent Usage Pattern

```python
# 1. Create a session
run("python batch_manager.py plan --session my-run --items items.json --batch-size 5")

# 2. Loop until done
while True:
    result = run("python batch_manager.py next --session my-run")
    if result.exit_code == 2:
        break  # no more batches
    
    for item in result.json["items"]:
        try:
            process(item)
            run(f"python batch_manager.py complete --session my-run --item {item['id']}")
        except Exception as e:
            run(f"python batch_manager.py fail --session my-run --item {item['id']} --error '{e}'")

# 3. Verify completion
run("python batch_manager.py done --session my-run")
```

## Session Files

Sessions are stored at `~/.belt/sessions/<session-id>.json`.
