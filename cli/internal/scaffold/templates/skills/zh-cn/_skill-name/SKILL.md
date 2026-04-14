---
name: __APP_NAME__
description: |
  __APP_DESCRIPTION__

  子命令：
  - run [参数]: 主要操作描述
  - help: 显示用法

  当用户需要：
  - [触发场景 1，例如："分析某个文件或目录"]
  - [触发场景 2，例如："生成结构化输出报告"]
  - [触发场景 3]
  时主动使用此 skill。

  触发词：[关键词1]、[关键词2]、[关键词3]
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

# __APP_NAME__

[一段话描述此 skill 的功能和解决的问题。要具体——告诉 AI 它将完成什么，而不只是 skill "是什么"。]

## 命令解析

将用户第一个参数解析为子命令：

```
/__APP_NAME__ run [参数]
/__APP_NAME__ help
```

| 子命令 | 操作 | 参考 |
|--------|------|------|
| `run` | [描述主要操作] | 见下方**执行流程** |
| `help` | 显示用法和示例 | 打印上方命令表 |

## 执行流程

1. **解析输入** — 识别子命令和参数
2. **验证** — 检查必要参数是否存在；缺少时打印用法并退出
3. **执行** — 运行下方描述的核心逻辑
4. **输出** — 按**输出格式**规范输出结果

## 核心逻辑

[描述此 skill 执行的主要工作。要具体：
- 读取哪些文件或目录？
- 进行什么转换或分析？
- 做出什么决策？
- 调用哪些外部命令或 API？]

### run [参数]

[`run` 的分步描述：]

1. [第一步，例如："读取 args[0] 提供的目标文件路径"]
2. [第二步，例如："解析内容并提取 X"]
3. [第三步，例如："携带提取的数据调用 scripts/__APP_NAME__/run.py"]
4. [最后一步，例如："以结构化 markdown 格式打印结果"]

## 核心资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `scripts/__APP_NAME__/run.py` | 主处理逻辑 |
| 应用配置 | `app.json` | 运行时应用目录与元数据 |

调用主脚本：

```bash
python3 {skill_path}/scripts/__APP_NAME__/run.py [参数]
```

其中 `{skill_path}` 是此 skill 目录的绝对路径（`~/.claude/skills/__APP_NAME__`）。

## 应用目录

此 skill 有一个专属的**应用目录**，用于存储运行时数据、输出文件和状态。
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

[定义输出格式。示例：]

```
## 结果

**状态**：[成功/失败]
**摘要**：[一行摘要]

### 详情
[结构化输出内容]
```

## 最佳实践

**应该做：**
- [最佳实践 1，例如："读取前验证所有文件路径"]
- [最佳实践 2，例如："长时间操作时汇报进度"]
- [最佳实践 3]

**不应该做：**
- [反模式 1，例如："不要静默跳过错误——始终报告它们"]
- [反模式 2]

## 备注

- `scripts/__APP_NAME__/` 中的脚本与语言无关，中英文版本共享同一套脚本
- 如需扩展此 skill，在 `references/` 下添加子命令文档并更新上方命令表

__COMPONENTS__
