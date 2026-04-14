# subagent_tracker

Fork-and-collect 状态机，用于编排多个子代理（subagent）。每个任务打包一份**结构化 todo 列表**和**两层上下文**（全局 + 任务专属）作为完整的派遣载荷——子代理独立执行所需的一切都在其中。

## 关于

安装组件脚本：

```bash
belt install subagent_tracker
```

## 何时使用

适用于以下场景：
- 将相互独立的任务分发给专业子代理（顺序或并行均可）
- 向每个子代理传递丰富的共享上下文（项目信息、规范、凭证等），无需反复复制粘贴
- 为每个子代理提供结构化的 todo 清单来驱动其工作
- 将所有子代理的执行结果收集汇总回编排代理
- 在派遣中途崩溃后能优雅恢复

## 脚本位置

```
~/.claude/skills/subagent_tracker/scripts/tracker.py
```

## 工作流程

```
1. init    → 创建会话：定义全局上下文 + 任务列表
2. next    → 获取下一个待处理任务的完整派遣载荷（幂等）
3.           → runSubagent(agent=payload.agent, prompt=build_prompt(payload))
4. report  → 子代理成功时存储结果
5. fail    → 出错时标记任务失败
   重复 2–5 直到全部完成
6. done    → 检查所有任务是否已结算
7. results → 收集所有输出
```

## 任务 JSON 格式

```json
[
  {
    "id": "build-login",
    "description": "构建登录页面组件",
    "agent": "frontend-engineer",
    "todos": [
      {"id": 1, "title": "创建 LoginForm 组件"},
      {"id": 2, "title": "添加表单校验"},
      {"id": 3, "title": "编写单元测试"}
    ],
    "context": {
      "design_url": "https://figma.com/...",
      "api_endpoint": "/api/auth/login"
    }
  },
  {
    "id": "build-api",
    "description": "实现认证 REST API",
    "agent": "python-backend-engineer",
    "todos": [
      {"id": 1, "title": "创建 /auth/login 端点"},
      {"id": 2, "title": "添加 JWT 签名"},
      {"id": 3, "title": "编写集成测试"}
    ],
    "context": {
      "spec_file": "docs/api-spec.yaml"
    }
  }
]
```

每个任务的必填字段：`id`、`description`。  
可选字段：`agent`、`todos`、`context`。

## 全局上下文文件（可选）

在每个派遣载荷的 `context.global` 中注入共享数据：

```json
{
  "project": "my-app",
  "repo": "https://github.com/org/my-app",
  "tech_stack": ["React", "TypeScript", "FastAPI"],
  "conventions": "遵循现有代码风格，所有新文件需要测试。",
  "shared_env": {
    "base_url": "http://localhost:3000"
  }
}
```

---

## 命令

### init — 创建会话

```bash
python tracker.py init \
  --session <会话ID> \
  --tasks <tasks.json路径> \
  [--context <全局上下文.json路径>]
```

输出：
```json
{"session_id": "sprint-42", "total_tasks": 3, "global_context_keys": ["project", "repo"]}
```

---

### next — 获取下一个派遣载荷

```bash
python tracker.py next --session <会话ID>
```

返回下一个待处理任务的完整载荷，并将其标记为 `dispatched`。**幂等**——崩溃恢复后安全调用；若任务已是 `dispatched` 状态且尚未上报，则重新返回该任务。

当没有更多待处理/派遣中任务时，退出码为 `2`。

输出：
```json
{
  "task_id": "build-login",
  "description": "构建登录页面组件",
  "agent": "frontend-engineer",
  "todos": [
    {"id": 1, "title": "创建 LoginForm 组件"},
    {"id": 2, "title": "添加表单校验"},
    {"id": 3, "title": "编写单元测试"}
  ],
  "context": {
    "global": {"project": "my-app", "repo": "https://github.com/..."},
    "task":   {"design_url": "https://figma.com/...", "api_endpoint": "/api/auth/login"}
  }
}
```

---

### report — 存储子代理结果

```bash
python tracker.py report \
  --session <会话ID> \
  --task <任务ID> \
  [--result '{"files_created": ["src/LoginForm.tsx"]}']
```

---

### fail — 标记任务失败

```bash
python tracker.py fail \
  --session <会话ID> \
  --task <任务ID> \
  [--error "超时 60s"]
```

---

### status — 进度摘要

```bash
python tracker.py status --session <会话ID>
```

输出：
```json
{
  "session_id": "sprint-42",
  "tasks": {"total": 3, "done": 1, "failed": 0, "dispatched": 1, "pending": 1}
}
```

---

### done — 检查完成情况

```bash
python tracker.py done --session <会话ID>
# 退出码 0 = 全部结算完毕，退出码 1 = 仍有待处理/派遣中任务
```

---

### results — 收集所有输出

```bash
python tracker.py results --session <会话ID>
```

输出：
```json
{
  "session_id": "sprint-42",
  "results": [
    {
      "task_id": "build-login",
      "description": "构建登录页面组件",
      "agent": "frontend-engineer",
      "status": "done",
      "result": {"files_created": ["src/LoginForm.tsx"]},
      "error": null,
      "dispatched_at": "2026-04-14T10:00:00+00:00",
      "completed_at": "2026-04-14T10:05:00+00:00"
    }
  ]
}
```

---

### list / cleanup

```bash
python tracker.py list
python tracker.py cleanup [--older-than 7]
```

---

## 代理使用模式

```python
SCRIPT = "python ~/.claude/skills/subagent_tracker/scripts/tracker.py"

# 1. 创建会话
run(f"{SCRIPT} init --session sprint-42 --tasks tasks.json --context ctx.json")

# 2. 逐一派遣任务
while True:
    result = run(f"{SCRIPT} next --session sprint-42")
    if result.exit_code == 2:
        break  # 所有任务已派遣

    payload = result.json
    try:
        agent_result = runSubagent(
            agentName=payload["agent"],
            prompt=f"""
你正在处理：{payload['description']}

## 全局上下文
{json.dumps(payload['context']['global'], indent=2, ensure_ascii=False)}

## 任务上下文
{json.dumps(payload['context']['task'], indent=2, ensure_ascii=False)}

## Todo 列表
{chr(10).join(f"- [ ] {t['title']}" for t in payload['todos'])}

请完成上述所有 todo 项。
"""
        )
        run(f"{SCRIPT} report --session sprint-42 --task {payload['task_id']} "
            f"--result '{json.dumps(agent_result)}'")
    except Exception as e:
        run(f"{SCRIPT} fail --session sprint-42 --task {payload['task_id']} --error '{e}'")

# 3. 确认完成
run(f"{SCRIPT} done --session sprint-42")

# 4. 收集所有结果
run(f"{SCRIPT} results --session sprint-42")
```

## 会话文件

会话存储在 `~/.belt/sessions/<session-id>.json`。
