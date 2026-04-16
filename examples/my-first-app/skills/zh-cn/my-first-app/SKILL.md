---
name: my-first-app
description: |
  [一句话描述 my-first-app 的功能。]

  子命令:
  - run [参数]: [主要操作]

  当用户需要:
  - [触发场景 1]
  - [触发场景 2]
  时主动使用此 skill。

  触发词:[关键词1]、[关键词2]、[关键词3]
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

# my-first-app

[简短描述此 skill 的功能。]

## 命令解析

```
/my-first-app run [参数]
/my-first-app help
```

## 执行流程

1. 解析用户输入,识别子命令
2. 如有需要,加载 `references/*.md` 中的详细文档
3. 执行对应逻辑

## 核心资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `scripts/my-first-app/run.py` | 主入口 |

## 调用方式

调用主脚本:

```bash
python3 {skill_path}/scripts/my-first-app/run.py [参数]
```

其中 `{skill_path}` 是此 skill 目录的绝对路径(通常为 `~/.claude/skills/my-first-app`)。

## 备注

- `scripts/my-first-app/` 中的脚本与语言无关,中英文版本共享同一套脚本
- 如果 skill 功能增多,可在 `references/` 下添加子命令文档
