# __APP_NAME__

> An AI-native app built with [Belt](https://github.com/projanvil/Belt).

## What It Does

__APP_DESCRIPTION__

## Install

```bash
bash install.sh              # English (default)
bash install.sh --lang=zh-cn # Chinese
pwsh ./install.ps1           # English (default)
pwsh ./install.ps1 -Lang zh-cn # Chinese
```

Or from Belt root:

```bash
make install APP=__APP_NAME__
make install APP=__APP_NAME__ LANG=zh-cn
```

## Usage

After installation, use it in Claude Code:

```
/__APP_NAME__ run [args]
```

Or invoke the agent:

```
@__APP_NAME__ [task description]
```

## Structure

```
__APP_NAME__/
├── skills/
│   ├── en/__APP_NAME__/SKILL.md       # English skill prompt
│   ├── zh-cn/__APP_NAME__/SKILL.md    # Chinese skill prompt
│   └── scripts/__APP_NAME__/run.py    # Shared script
├── agents/
│   ├── en/__APP_NAME__.md             # English subagent
│   └── zh-cn/__APP_NAME__.md          # Chinese subagent
├── install.sh
└── install.ps1
```

## Development

Edit the skill prompts:
- `skills/en/__APP_NAME__/SKILL.md` — English instructions
- `skills/zh-cn/__APP_NAME__/SKILL.md` — Chinese instructions

Add scripts:
- `skills/scripts/__APP_NAME__/` — Python or shell scripts

Re-install after changes:
```bash
bash install.sh
pwsh ./install.ps1
```
