---
name: test-gen-app
description: |
  test-gen-app - brief one-line description of what this skill does.

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

# test-gen-app

[One paragraph describing what this skill does and the problem it solves. Be concrete — tell the AI what it will accomplish, not just what the skill "is".]

## Command Parsing

Parse the user's first argument as the subcommand:

```
/test-gen-app run [args]
/test-gen-app help
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
3. [Third action, e.g., "Call the script at scripts/test-gen-app/run.py with the extracted data"]
4. [Final action, e.g., "Print the result as structured markdown"]

## Core Resources

| Resource | Path | Description |
|----------|------|-------------|
| Main script | `scripts/test-gen-app/run.py` | Primary processing logic |

To invoke the main script:

```bash
python3 {skill_path}/scripts/test-gen-app/run.py [args]
```

Where `{skill_path}` is the absolute path to this skill directory (`~/.claude/skills/test-gen-app`).

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

- Scripts in `scripts/test-gen-app/` are language-agnostic and shared across locales
- To extend this skill, add subcommand documentation in `references/` and update the command table above
