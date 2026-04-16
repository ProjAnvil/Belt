---
name: my-first-app
description: |
  [One-line description of what my-first-app does.]

  Subcommands:
  - run [args]: [primary action]

  Use this skill when the user needs to:
  - [trigger scenario 1]
  - [trigger scenario 2]

  Trigger phrases: [keyword1], [keyword2], [keyword3]
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

# my-first-app

[Short description of what this skill does.]

## Commands

```
/my-first-app run [args]
/my-first-app help
```

## Execution Flow

1. Parse the user's input to identify the subcommand
2. Load the relevant reference if needed (`references/*.md`)
3. Execute the logic

## Core Resources

| Resource | Path | Description |
|----------|------|-------------|
| Main script | `scripts/my-first-app/run.py` | Primary entry point |

## Usage

To invoke the main script:

```bash
python3 {skill_path}/scripts/my-first-app/run.py [args]
```

Where `{skill_path}` is the absolute path to this skill directory (typically `~/.claude/skills/my-first-app`).

## Notes

- Scripts in `scripts/my-first-app/` are language-agnostic and shared across locales
- Add subcommand documentation in `references/` if the skill grows complex
