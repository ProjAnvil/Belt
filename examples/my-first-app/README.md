# my-first-app

> An AI-native app built with [Belt](https://github.com/projanvil/Belt).

## What It Does

[Describe what this app does in 2-3 sentences.]

## Install

```bash
bash install.sh              # English (default)
bash install.sh --lang=zh-cn # Chinese
pwsh ./install.ps1           # English (default)
pwsh ./install.ps1 -Lang zh-cn # Chinese
```

Or from Belt root:

```bash
make install APP=my-first-app
make install APP=my-first-app LANG=zh-cn
```

## Usage

After installation, use it in Claude Code:

```
/my-first-app run [args]
```

Or invoke the agent:

```
@my-first-app [task description]
```

## Structure

```
my-first-app/
├── skills/
│   ├── en/my-first-app/SKILL.md       # English skill prompt
│   ├── zh-cn/my-first-app/SKILL.md    # Chinese skill prompt
│   └── scripts/my-first-app/run.py    # Shared script
├── agents/
│   ├── en/my-first-app.md             # English subagent
│   └── zh-cn/my-first-app.md          # Chinese subagent
├── install.sh
└── install.ps1
```

## Development

Edit the skill prompts:
- `skills/en/my-first-app/SKILL.md` — English instructions
- `skills/zh-cn/my-first-app/SKILL.md` — Chinese instructions

Add scripts:
- `skills/scripts/my-first-app/` — Python or shell scripts

Re-install after changes:
```bash
bash install.sh
pwsh ./install.ps1
```
