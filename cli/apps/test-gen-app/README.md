# test-gen-app

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
make install APP=test-gen-app
make install APP=test-gen-app LANG=zh-cn
```

## Usage

After installation, use it in Claude Code:

```
/test-gen-app run [args]
```

Or invoke the agent:

```
@test-gen-app [task description]
```

## Structure

```
test-gen-app/
├── skills/
│   ├── en/test-gen-app/SKILL.md       # English skill prompt
│   ├── zh-cn/test-gen-app/SKILL.md    # Chinese skill prompt
│   └── scripts/test-gen-app/run.py    # Shared script
├── agents/
│   ├── en/test-gen-app.md             # English subagent
│   └── zh-cn/test-gen-app.md          # Chinese subagent
├── install.sh
└── install.ps1
```

## Development

Edit the skill prompts:
- `skills/en/test-gen-app/SKILL.md` — English instructions
- `skills/zh-cn/test-gen-app/SKILL.md` — Chinese instructions

Add scripts:
- `skills/scripts/test-gen-app/` — Python or shell scripts

Re-install after changes:
```bash
bash install.sh
pwsh ./install.ps1
```
