# hello-belt

> Example app showing Belt's skill + subagent + script pattern.

## Install

```bash
bash install.sh              # English
bash install.sh --lang=zh-cn # Chinese
pwsh ./install.ps1           # English
pwsh ./install.ps1 -Lang zh-cn # Chinese
```

Or from Belt root:

```bash
make install APP=hello-belt
make install APP=hello-belt LANG=zh-cn
```

## Usage

```
/hello-belt greet Alice
/hello-belt greet --lang zh-cn 张三
/hello-belt list-langs
```

Or via agent:

```
@hello-belt say hello to Bob in French
```

## How It Works

```
User → /hello-belt greet Alice
         │
         ▼
   SKILL.md reads the command
         │
         ▼
   Calls: python3 ~/.claude/skills/hello-belt/scripts/hello-belt/greet.py --name Alice
         │
         ▼
   Output: Hello, Alice! 👋
```

The skill prompt (`SKILL.md`) tells Claude how to interpret commands.
The script (`greet.py`) does the actual work.
The agent (`hello-belt.md`) handles complex or multi-step tasks.

## File Map

```
hello-belt/
├── skills/
│   ├── en/hello-belt/SKILL.md       ← English instructions
│   ├── zh-cn/hello-belt/SKILL.md    ← Chinese instructions
│   └── scripts/hello-belt/greet.py  ← Shared script
├── agents/
│   ├── en/hello-belt.md             ← English subagent
│   └── zh-cn/hello-belt.md          ← Chinese subagent
├── install.sh
└── install.ps1
```
