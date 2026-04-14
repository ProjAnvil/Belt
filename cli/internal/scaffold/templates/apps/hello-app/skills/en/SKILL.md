---
name: __APP_NAME__
description: |
  __APP_NAME__ - greets users and demonstrates how a Belt skill is structured.

  Subcommands:
  - greet [name]: greet a person by name
  - help: show usage

  Use this skill when the user wants to be greeted, or use it as a reference for
  building your own Belt skill.

  Trigger phrases: hello, greet, hi, introduce
allowed-tools: Read, Bash
---

# __APP_NAME__

A sample Belt app that greets users. Use this as a starting point — the structure shows
how skills, scripts, agents, and `app.json` work together.

## Command Parsing

Parse the user's first argument as the subcommand:

```
/__APP_NAME__ greet [name]
/__APP_NAME__ help
```

| Subcommand | Action |
|------------|--------|
| `greet [name]` | Print a personalised greeting for `name` (defaults to "World") |
| `help` | Print the command table above |

## Execution Flow

1. **Parse input** — read subcommand from first argument; default to `greet` when omitted
2. **Validate** — for `greet`, accept an optional name argument
3. **Execute** — call `run.py greet [name]`
4. **Report** — print greeting to stdout

## Core Logic

### greet [name]

1. Read optional `name` from args (default: `"World"`)
2. Call the main script:
   ```bash
   python3 {skill_path}/scripts/__APP_NAME__/run.py greet [name]
   ```
3. Print the returned greeting

## Core Resources

| Resource | Path | Description |
|----------|------|-------------|
| Main script | `scripts/__APP_NAME__/run.py` | Greeting logic |
| App config  | `reference/app.json` | Runtime app directory and metadata |

To invoke the main script:

```bash
python3 {skill_path}/scripts/__APP_NAME__/run.py greet [name]
```

Where `{skill_path}` is `~/.claude/skills/__APP_NAME__`.

## App Directory

This skill has a dedicated **app directory** for storing runtime data.
The path is defined in `app.json` (located at `~/.claude/skills/__APP_NAME__/reference/app.json`).

At the start of every command, read the app directory:

```python
import json, pathlib
config = json.loads(pathlib.Path("~/.claude/skills/__APP_NAME__/reference/app.json").expanduser().read_text())
app_dir = pathlib.Path(config["app_dir"]).expanduser()
app_dir.mkdir(parents=True, exist_ok=True)
```

Always ensure the app directory exists before writing any files.

## Output Format

```
👋 Hello, <name>! Greetings from __APP_NAME__.
```

## Best Practices

**DO:**
- Call the Python script rather than hardcoding logic in this file
- Read `reference/app.json` for runtime paths before writing any state

**DON'T:**
- Hardcode paths — always derive them from `{skill_path}` or `app.json`

## Notes

- Scripts in `scripts/__APP_NAME__/` are language-agnostic — both en and zh-cn locales share
  the same Python script
- This is a demo app; replace the `greet` command with your own logic

__COMPONENTS__
