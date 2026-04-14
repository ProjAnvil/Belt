---
name: __APP_NAME__
description: |
  __APP_DESCRIPTION__

  Subcommands:
  - run [args]: primary action description
  - help: show usage

  Use this skill when the user needs to:
  - [describe trigger scenario 1, e.g., "analyze a specific file or directory"]
  - [describe trigger scenario 2, e.g., "generate a report with structured output"]
  - [describe trigger scenario 3]

  Trigger phrases: [keyword1], [keyword2], [keyword3]
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

# __APP_NAME__

[One paragraph describing what this skill does and the problem it solves. Be concrete — tell the AI what it will accomplish, not just what the skill "is".]

## Command Parsing

Parse the user's first argument as the subcommand:

```
/__APP_NAME__ run [args]
/__APP_NAME__ help
```

| Subcommand | Action | Reference |
|------------|--------|-----------|
| `run` | [describe the main action] | See **Execution Flow** below |
| `help` | Show usage and examples | Print command table above |

## Execution Flow

1. **Parse input** — identify the subcommand and any arguments
2. **Validate** — check that required arguments are present; print usage and exit if missing
3. **Execute** — run the core logic described below
4. **Report** — output results in the format specified in **Output Format**

## Core Logic

[Describe the main work this skill performs. Be specific:
- What files/directories does it read?
- What transformations or analysis does it do?
- What decisions does it make?
- What external commands or APIs does it call?]

### run [args]

[Step-by-step description of what `run` does:]

1. [First action, e.g., "Read the target file at the path provided in args[0]"]
2. [Second action, e.g., "Parse the content and extract X"]
3. [Third action, e.g., "Call the script at scripts/__APP_NAME__/run.py with the extracted data"]
4. [Final action, e.g., "Print the result as structured markdown"]

## Core Resources

| Resource | Path | Description |
|----------|------|--------------|
| Main script | `scripts/__APP_NAME__/run.py` | Primary processing logic |
| App config  | `app.json` | Runtime app directory and metadata |

To invoke the main script:

```bash
python3 {skill_path}/scripts/__APP_NAME__/run.py [args]
```

Where `{skill_path}` is the absolute path to this skill directory (`~/.claude/skills/__APP_NAME__`).

## App Directory

This skill has a dedicated **app directory** for storing runtime data, output files, and state.
The path is defined in `app.json` (located at `~/.claude/skills/__APP_NAME__/reference/app.json`).

At the start of every command, read the app directory:

```bash
APP_DIR=$(python3 -c "import json,pathlib; d=json.loads(pathlib.Path('~/.claude/skills/__APP_NAME__/reference/app.json').expanduser().read_text()); print(d['app_dir'])" 2>/dev/null | sed 's|^~|'"$HOME"'|')
```

Or in Python:

```python
import json, pathlib
config = json.loads(pathlib.Path("~/.claude/skills/__APP_NAME__/reference/app.json").expanduser().read_text())
app_dir = pathlib.Path(config["app_dir"]).expanduser()
app_dir.mkdir(parents=True, exist_ok=True)
```

Always ensure the app directory exists before writing any files.

## Output Format

[Define what the output should look like. Example:]

```
## Result

**Status**: [success/error]
**Summary**: [one-line summary]

### Details
[structured output here]
```

## Best Practices

**DO:**
- [Best practice 1, e.g., "Validate all file paths before reading"]
- [Best practice 2, e.g., "Report progress for long-running operations"]
- [Best practice 3]

**DON'T:**
- [Anti-pattern 1, e.g., "Don't silently skip errors — always report them"]
- [Anti-pattern 2]

## Notes

- Scripts in `scripts/__APP_NAME__/` are language-agnostic and shared across locales
- To extend this skill, add subcommand documentation in `references/` and update the command table above

__COMPONENTS__
