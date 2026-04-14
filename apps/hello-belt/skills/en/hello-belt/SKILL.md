---
name: hello-belt
description: |
  hello-belt — a minimal Belt app demonstrating skill + subagent + script patterns.

  Subcommands:
  - greet [name]: Print a greeting for the given name in the specified language
  - list-langs: Show all supported greeting languages

  Use this skill when the user says "hello-belt", asks for a greeting demo,
  or wants to see how Belt apps are structured.

  Trigger phrases: hello-belt, belt demo, belt example, greet me
allowed-tools: Read, Bash
---

# hello-belt

A minimal example app showing how Belt skills, agents, and scripts fit together.
When invoked, it calls `greet.py` to produce a multilingual greeting — demonstrating
the skill → script delegation pattern that all Belt apps use.

## Command Parsing

Parse the user's first argument as the subcommand:

```
/hello-belt greet [name] [--lang=en]
/hello-belt list-langs
/hello-belt help
```

| Subcommand | Action | Reference |
|------------|--------|-----------|
| `greet` | Print a greeting for `[name]` | See **Execution Flow** below |
| `list-langs` | List supported languages | Run `greet.py --list-langs` |
| `help` | Show usage | Print command table above |

## Execution Flow

1. **Parse input** — identify subcommand, `name` argument (default: "World"), and `--lang` flag (default: `en`)
2. **Validate** — ensure `--lang` is a supported code; if not, run `list-langs` and prompt the user
3. **Execute** — call `greet.py` with the resolved arguments
4. **Report** — display the greeting output

## Core Logic

### greet [name] [--lang=en]

1. Extract `name` from the user's message (or use "World" if not provided)
2. Extract `--lang` (or use `en` if not specified)
3. Call the greeting script:

```bash
python3 {skill_path}/scripts/hello-belt/greet.py --name "Alice" --lang zh-cn
```

Expected output:
```
你好, Alice! 👋
(Powered by hello-belt — a Belt AI-native app)
```

### list-langs

```bash
python3 {skill_path}/scripts/hello-belt/greet.py --list-langs
```

## Core Resources

| Resource | Path | Description |
|----------|------|-------------|
| Greeting script | `scripts/hello-belt/greet.py` | Multilingual greeting logic |

Where `{skill_path}` is the absolute path to this skill directory (typically `~/.claude/skills/hello-belt`).

## Output Format

```
## Greeting

{greeting}, {name}! 👋
(Powered by hello-belt — a Belt AI-native app)
```

## Best Practices

**DO:**
- Always delegate greeting generation to `greet.py` — don't hardcode greetings in the prompt
- Use `list-langs` to validate language codes before calling `greet`
- Default to `en` if no language is specified

**DON'T:**
- Override the script's output format
- Invent language codes not listed by `list-langs`

## Notes

- Scripts in `scripts/hello-belt/` are shared across locales
- This is a demo app — replace `greet.py` with your real logic
- For multi-step tasks (batch greetings, language detection), delegate to `@hello-belt` agent
