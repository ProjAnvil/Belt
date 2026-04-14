---
name: __APP_NAME__
description: |
  __APP_NAME__ - 问候用户，同时演示 Belt skill 的结构。

  子命令：
  - greet [名字]: 以指定名字问候用户
  - help: 显示用法

  当用户想要被问候，或用来作为构建 Belt skill 的参考时使用此 skill。

  触发词：你好、问候、打招呼、介绍一下
allowed-tools: Read, Bash
---

# __APP_NAME__

一个用于问候用户的示例 Belt 应用。以此为起点——结构展示了 skill、脚本、agent 和 `app.json` 如何协同工作。

## 命令解析

将用户第一个参数解析为子命令：

```
/__APP_NAME__ greet [名字]
/__APP_NAME__ help
```

| 子命令 | 操作 |
|--------|------|
| `greet [名字]` | 打印对 `名字` 的个性化问候（默认为 "世界"） |
| `help` | 打印上方命令表 |

## 执行流程

1. **解析输入** — 读取第一个参数作为子命令；省略时默认为 `greet`
2. **验证** — `greet` 接受一个可选的名字参数
3. **执行** — 调用 `run.py greet [名字]`
4. **输出** — 打印问候语

## 核心逻辑

### greet [名字]

1. 从参数读取可选的 `名字`（默认：`"世界"`）
2. 调用主脚本：
   ```bash
   python3 {skill_path}/scripts/__APP_NAME__/run.py greet [名字]
   ```
3. 打印返回的问候语

## 核心资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `scripts/__APP_NAME__/run.py` | 问候逻辑 |
| 应用配置 | `reference/app.json` | 运行时应用目录与元数据 |

调用主脚本：

```bash
python3 {skill_path}/scripts/__APP_NAME__/run.py greet [名字]
```

其中 `{skill_path}` 为 `~/.claude/skills/__APP_NAME__`。

## 应用目录

此 skill 有一个专属的**应用目录**，用于存储运行时数据。
路径定义在 `app.json`（位于 `~/.claude/skills/__APP_NAME__/reference/app.json`）。

在每条命令开始时，先读取应用目录：

```python
import json, pathlib
config = json.loads(pathlib.Path("~/.claude/skills/__APP_NAME__/reference/app.json").expanduser().read_text())
app_dir = pathlib.Path(config["app_dir"]).expanduser()
app_dir.mkdir(parents=True, exist_ok=True)
```

写入任何文件前，始终确保应用目录已存在。

## 输出格式

```
👋 你好，<名字>！来自 __APP_NAME__ 的问候。
```

## 最佳实践

**应该做：**
- 调用 Python 脚本，而非将逻辑硬编码在此文件中
- 写入状态前先从 `reference/app.json` 读取运行时路径

**不应该做：**
- 硬编码路径——始终从 `{skill_path}` 或 `app.json` 中推导

## 备注

- `scripts/__APP_NAME__/` 中的脚本与语言无关——en 和 zh-cn 共享同一套 Python 脚本
- 这是一个演示应用；将 `greet` 命令替换为你自己的逻辑

__COMPONENTS__
