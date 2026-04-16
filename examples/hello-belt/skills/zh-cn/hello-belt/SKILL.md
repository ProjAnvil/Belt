---
name: hello-belt
description: |
  hello-belt — 演示 Belt skill + subagent + script 模式的最小示例应用。

  子命令：
  - greet [名字] [--lang=zh-cn]: 以指定语言输出对指定名字的问候
  - list-langs: 显示所有支持的问候语言

  当用户说 "hello-belt"、请求问候演示，或想了解 Belt 应用结构时使用此 skill。

  触发词：hello-belt、belt 演示、belt 示例、问候我
allowed-tools: Read, Bash
---

# hello-belt

展示 Belt 中 skill、agent、script 如何协同工作的最小示例应用。
被调用时，它会调用 `greet.py` 生成多语言问候——展示所有 Belt 应用都使用的 skill → script 委托模式。

## 命令解析

将用户的第一个参数解析为子命令：

```
/hello-belt greet [名字] [--lang=zh-cn]
/hello-belt list-langs
/hello-belt help
```

| 子命令 | 操作 | 参考 |
|--------|------|------|
| `greet` | 打印对 `[名字]` 的问候 | 见下方**执行流程** |
| `list-langs` | 列出支持的语言 | 运行 `greet.py --list-langs` |
| `help` | 显示用法 | 打印上方命令表 |

## 执行流程

1. **解析输入** — 识别子命令、`名字` 参数（默认："世界"）以及 `--lang` 标志（默认：`zh-cn`）
2. **验证** — 确保 `--lang` 是支持的语言代码；若不支持，运行 `list-langs` 并提示用户
3. **执行** — 携带解析后的参数调用 `greet.py`
4. **输出** — 显示问候结果

## 核心逻辑

### greet [名字] [--lang=zh-cn]

1. 从用户消息中提取 `名字`（或默认使用"世界"）
2. 提取 `--lang`（或默认使用 `zh-cn`）
3. 调用问候脚本：

```bash
python3 {skill_path}/scripts/hello-belt/greet.py --name "张三" --lang zh-cn
```

预期输出：
```
你好, 张三! 👋
(Powered by hello-belt — a Belt AI-native app)
```

### list-langs

```bash
python3 {skill_path}/scripts/hello-belt/greet.py --list-langs
```

## 核心资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 问候脚本 | `scripts/hello-belt/greet.py` | 多语言问候逻辑 |

其中 `{skill_path}` 是此 skill 目录的绝对路径（通常为 `~/.claude/skills/hello-belt`）。

## 输出格式

```
## 问候

{问候语}, {名字}! 👋
(Powered by hello-belt — a Belt AI-native app)
```

## 最佳实践

**应该做：**
- 始终将问候生成委托给 `greet.py`——不要在 prompt 中硬编码问候语
- 调用 `greet` 前先用 `list-langs` 验证语言代码
- 未指定语言时默认使用 `zh-cn`

**不应该做：**
- 覆盖脚本的输出格式
- 使用 `list-langs` 未列出的语言代码

## 备注

- `scripts/hello-belt/` 中的脚本在中英文版本间共享
- 这是演示应用——请将 `greet.py` 替换为你的实际逻辑
- 对于多步骤任务（批量问候、语言检测），请改用 `@hello-belt` 代理
