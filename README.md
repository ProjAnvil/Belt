# Belt — Build AI-Native Apps for Claude Code

**[中文文档](README.zh-cn.md)**

An **AI-native app** is not a plugin, a webhook, or a wrapper.
It is a first-class tool that lives *inside* the AI's context: Claude reads its instructions, calls its scripts, and delegates sub-tasks to its own agents — all without leaving the conversation.

Belt is a **Go CLI tool** that scaffolds exactly that structure. Run `belt new`, answer a few prompts, and you get a fully wired `skill + subagent + script` bundle ready to install into Claude Code in one command.

> Part of the [projanvil](https://github.com/projanvil) ecosystem.

## What is a Belt App?

```
Claude Code
  └── ~/.claude/
        ├── skills/my-tool/
        │         ├── SKILL.md          ← AI reads this as instructions
        │         ├── scripts/run.py    ← AI can call this script
        │         └── reference/
        │               ├── app.json   ← runtime config (app data dir)
        │               └── *.md       ← bundled component references
        └── agents/my-tool.md          ← AI can delegate tasks here
```

Every piece of a Belt app is **designed to be read or called by the AI**:

- **Skill** — `SKILL.md` tells Claude *what* this tool does and *how* to invoke it
- **Script** — Python scripts the AI calls to perform real computation
- **Agent** — A subagent `.md` Claude can delegate complex workflows to
- **Component** — A testable, self-contained module (e.g. `batch-planner`) whose reference docs are injected directly into the skill so Claude knows how to use it

Belt generates this entire structure from an interactive prompt, with **bilingual support** (en / zh-cn), and ships each app with `install.sh` and `install.ps1` for one-command Claude Code integration.

## Installation

### Build from source

```bash
cd cli
make build
sudo make install   # copies belt to /usr/local/bin/
```

### Pre-built binary

Download the binary for your platform from [Releases](../../releases) and place it in your `$PATH`.

## Quick Start

```bash
# Interactive scaffold — run from your Belt workspace root
belt new

# Scaffold into a specific directory
belt new ./my-projects

# Check environment prerequisites
belt doctor
```

`belt new` walks you through:

1. **App name** — used as the skill/agent identifier in Claude Code
2. **Template** — `empty` (blank placeholders) or `hello-app` (working greet example)
3. **Components** *(empty template only)* — multi-select reusable modules to bundle
4. **App data directory** — where the app stores runtime files (e.g. `~/.claude/.my-tool`)
5. **Language** — `en` or `zh-cn`
6. **Installer** — `both`, `sh` only, or `ps1` only

Then install into Claude Code:

```bash
cd my-tool
bash install.sh              # Linux / macOS
pwsh install.ps1             # Windows
bash install.sh --lang=zh-cn # Chinese variant
```

Claude Code will immediately recognise `/my-tool` (skill) and `@my-tool` (agent).

## Repository Structure

```
belt/
├── cli/                          # Go CLI (the belt binary)
│   ├── cmd/                      # Cobra commands: new, doctor
│   ├── internal/scaffold/        # Template embedding & generation
│   │   └── templates/            # Embedded scaffold templates
│   │       ├── skills/           # Blank skill / script templates
│   │       ├── agents/           # Blank agent templates
│   │       ├── apps/hello-app/   # hello-app template set
│   │       ├── component/        # Component scaffold template
│   │       ├── install.sh
│   │       ├── install.ps1
│   │       ├── app.json
│   │       └── README.md
│   ├── main.go
│   ├── go.mod
│   └── Makefile
├── components/                   # Reusable Belt components
│   └── batch-planner/            # Persistent batch state machine
│       ├── component.json
│       ├── scripts/
│       └── reference/            # Bilingual reference docs
│           ├── en/batch-planner.md
│           └── zh-cn/batch-planner.md
├── apps/                         # Example / reference apps
│   └── hello-belt/
├── _template/                    # Human-readable template source (reference only)
└── README.md
```

## Generated App Structure

```
my-tool/
├── skills/
│   ├── en/my-tool/SKILL.md       # English skill prompt
│   ├── zh-cn/my-tool/SKILL.md    # Chinese skill prompt
│   └── scripts/my-tool/run.py    # Shared script (language-agnostic)
├── agents/
│   ├── en/my-tool.md
│   └── zh-cn/my-tool.md
├── app.json                      # App metadata & runtime data directory
├── install.sh
├── install.ps1
└── README.md
```

`install.sh` / `install.ps1` do the following at install time:
- Link skill files into `~/.claude/skills/my-tool/`
- Create `~/.claude/skills/my-tool/reference/` as a real directory
- Copy `app.json` → `reference/app.json`
- Create the `app_dir` declared in `app.json`
- Link bundled component reference `.md` files into `reference/`
- Link the agent into `~/.claude/agents/`

## Components

Components are **testable, AI-usable building blocks** — self-contained Python modules with a clear separation between logic and AI interface:

- **Scripts** the AI calls to perform real computation
- **Bilingual reference docs** injected into `SKILL.md` so Claude knows exactly how to use the component
- **`pytest`-based test suite** so you can verify behavior before the AI ever touches it
- **`make test`** wired up out of the box for every component

This makes components the safest surface for extending AI capability: write the logic, test it like normal code, then expose it to Claude via reference docs.

When selected during `belt new`, the component's reference doc is injected as a summary stub into `SKILL.md`, and the full doc is symlinked into `reference/<comp>.md` at install time.

To scaffold a new component:

```bash
belt new --type=component my-component
```

Structure:

```
components/my-component/
├── component.json
├── scripts/my-component.py     # AI-callable logic
├── reference/
│   ├── en/my-component.md      # AI reads this to understand the component
│   └── zh-cn/my-component.md
├── tests/
│   └── test_my-component.py   # test before the AI uses it
├── Makefile                    # make test
└── requirements.txt
```

## Commands

| Command | Description |
|---------|-------------|
| `belt new [path]` | Scaffold a new app interactively |
| `belt new --type=component <name>` | Scaffold a new component |
| `belt doctor` | Check environment prerequisites |

## License

[MIT](LICENSE)

