# subagent_tracker

Fork-and-collect state machine for subagent orchestration. Each task bundles a structured **todo list** and **two-layer context** (global + task-specific) into a single dispatch payload — everything a subagent needs to execute independently.

## About

Install the component scripts:

```bash
belt install subagent_tracker
```

## When to Use

Use this component when you need to:
- Fan out independent tasks to specialized subagents in parallel or sequentially
- Pass rich shared context (project info, conventions, credentials) to every subagent without copy-pasting it
- Give each subagent a structured checklist of todos to drive its work
- Collect and aggregate results back to the orchestrating agent
- Recover gracefully from crashes mid-dispatch

## Script Location

```
~/.claude/skills/subagent_tracker/scripts/tracker.py
```

## Workflow

```
1. init    → Create session: define global context + task list
2. next    → Fetch next pending task as a full dispatch payload (idempotent)
3.           → runSubagent(agent=payload.agent, prompt=build_prompt(payload))
4. report  → Store result when subagent succeeds
5. fail    → Mark task failed on error
   repeat 2–5 until done
6. done    → Verify all tasks settled
7. results → Collect all outputs
```

## Tasks JSON Format

```json
[
  {
    "id": "build-login",
    "description": "Build the login page component",
    "agent": "frontend-engineer",
    "todos": [
      {"id": 1, "title": "Create LoginForm component"},
      {"id": 2, "title": "Add form validation"},
      {"id": 3, "title": "Write unit tests"}
    ],
    "context": {
      "design_url": "https://figma.com/...",
      "api_endpoint": "/api/auth/login"
    }
  },
  {
    "id": "build-api",
    "description": "Implement the auth REST API",
    "agent": "python-backend-engineer",
    "todos": [
      {"id": 1, "title": "Create /auth/login endpoint"},
      {"id": 2, "title": "Add JWT signing"},
      {"id": 3, "title": "Write integration tests"}
    ],
    "context": {
      "spec_file": "docs/api-spec.yaml"
    }
  }
]
```

Required fields per task: `id`, `description`.
Optional: `agent`, `todos`, `context`.

## Global Context File (optional)

Shared data injected into every dispatch payload under `context.global`:

```json
{
  "project": "my-app",
  "repo": "https://github.com/org/my-app",
  "tech_stack": ["React", "TypeScript", "FastAPI"],
  "conventions": "Follow existing code style. All new files need tests.",
  "shared_env": {
    "base_url": "http://localhost:3000"
  }
}
```

---

## Commands

### init — Create a session

```bash
python tracker.py init \
  --session <session-id> \
  --tasks <path-to-tasks.json> \
  [--context <path-to-global-context.json>]
```

Output:
```json
{"session_id": "sprint-42", "total_tasks": 3, "global_context_keys": ["project", "repo"]}
```

---

### next — Get next dispatch payload

```bash
python tracker.py next --session <session-id>
```

Returns the next pending task as a complete payload and marks it `dispatched`. **Idempotent** — safe after a crash; re-returns the same `dispatched` task if not yet reported.

Exit code `2` when no more pending/dispatched tasks exist.

Output:
```json
{
  "task_id": "build-login",
  "description": "Build the login page component",
  "agent": "frontend-engineer",
  "todos": [
    {"id": 1, "title": "Create LoginForm component"},
    {"id": 2, "title": "Add form validation"},
    {"id": 3, "title": "Write unit tests"}
  ],
  "context": {
    "global": {"project": "my-app", "repo": "https://github.com/..."},
    "task":   {"design_url": "https://figma.com/...", "api_endpoint": "/api/auth/login"}
  }
}
```

---

### report — Store subagent result

```bash
python tracker.py report \
  --session <session-id> \
  --task <task-id> \
  [--result '{"files_created": ["src/LoginForm.tsx"]}']
```

---

### fail — Mark task failed

```bash
python tracker.py fail \
  --session <session-id> \
  --task <task-id> \
  [--error "timeout after 60s"]
```

---

### status — Progress summary

```bash
python tracker.py status --session <session-id>
```

Output:
```json
{
  "session_id": "sprint-42",
  "tasks": {"total": 3, "done": 1, "failed": 0, "dispatched": 1, "pending": 1}
}
```

---

### done — Check completion

```bash
python tracker.py done --session <session-id>
# exit 0 = all settled, exit 1 = still pending/dispatched
```

---

### results — Collect all outputs

```bash
python tracker.py results --session <session-id>
```

Output:
```json
{
  "session_id": "sprint-42",
  "results": [
    {
      "task_id": "build-login",
      "description": "Build the login page component",
      "agent": "frontend-engineer",
      "status": "done",
      "result": {"files_created": ["src/LoginForm.tsx"]},
      "error": null,
      "dispatched_at": "2026-04-14T10:00:00+00:00",
      "completed_at": "2026-04-14T10:05:00+00:00"
    }
  ]
}
```

---

### list / cleanup

```bash
python tracker.py list
python tracker.py cleanup [--older-than 7]
```

---

## Agent Usage Pattern

```python
SCRIPT = "python ~/.claude/skills/subagent_tracker/scripts/tracker.py"

# 1. Create session
run(f"{SCRIPT} init --session sprint-42 --tasks tasks.json --context ctx.json")

# 2. Dispatch tasks one by one (or drive parallel forks)
while True:
    result = run(f"{SCRIPT} next --session sprint-42")
    if result.exit_code == 2:
        break  # all tasks dispatched

    payload = result.json
    try:
        agent_result = runSubagent(
            agentName=payload["agent"],
            prompt=f"""
You are working on: {payload['description']}

## Global Context
{json.dumps(payload['context']['global'], indent=2)}

## Task Context
{json.dumps(payload['context']['task'], indent=2)}

## Todo List
{chr(10).join(f"- [ ] {t['title']}" for t in payload['todos'])}

Complete all todos above.
"""
        )
        run(f"{SCRIPT} report --session sprint-42 --task {payload['task_id']} "
            f"--result '{json.dumps(agent_result)}'")
    except Exception as e:
        run(f"{SCRIPT} fail --session sprint-42 --task {payload['task_id']} --error '{e}'")

# 3. Verify completion
run(f"{SCRIPT} done --session sprint-42")

# 4. Gather all results
run(f"{SCRIPT} results --session sprint-42")
```

## Session Files

Sessions are stored at `~/.belt/sessions/<session-id>.json`.
