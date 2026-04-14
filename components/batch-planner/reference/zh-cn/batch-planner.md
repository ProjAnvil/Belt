# batch-planner（批次规划器）

持久化批次状态机，专为 LLM 编排设计。解决长批处理任务中上下文丢失的问题——状态存储在磁盘上，即使上下文增长也不会丢失进度。

## 关于

此组件提供脚本，使用前需要先安装。

安装组件脚本：
```bash
belt install batch-planner
```

## 使用场景

当你需要在多个 Agent 轮次中处理大量任务项，且必须跟踪哪些项已完成、待处理或失败时，使用此组件。

## 脚本位置

```
~/.claude/skills/batch-planner/scripts/batch_manager.py
```

## 工作流程

```
1. plan   → 创建 session，将任务项分割为批次
2. next   → 获取下一批任务（幂等操作）
3. complete/fail → 标记每个任务项为完成或失败
4. status → 随时检查进度
5. done   → 检查是否全部完成
```

## 命令

### plan — 创建 session

```bash
python batch_manager.py plan \
  --session <session-id> \
  --items <items.json 路径> \
  [--batch-size 5]
```

items.json 格式——对象数组，每个对象**必须**包含 `id` 字段：
```json
[
  {"id": "project-alpha", "name": "Alpha", "priority": "high"},
  {"id": "project-beta",  "name": "Beta",  "priority": "low"}
]
```

输出：
```json
{"session_id": "my-run", "total_items": 10, "total_batches": 2, "batch_size": 5}
```

---

### next — 获取下一批次

```bash
python batch_manager.py next --session <session-id>
```

返回下一个待处理批次并标记为 `in_progress`。**幂等**——崩溃后再次调用会返回同一批次。

无更多批次时退出码为 `2`。

---

### complete — 标记任务完成

```bash
python batch_manager.py complete --session <session-id> --item <item-id>
```

---

### fail — 标记任务失败

```bash
python batch_manager.py fail --session <session-id> --item <item-id> [--error "原因"]
```

---

### status — 进度摘要

```bash
python batch_manager.py status --session <session-id>
```

---

### done — 检查是否全部完成

```bash
python batch_manager.py done --session <session-id>
# 退出码 0 = 全部完成，退出码 1 = 仍有待处理项
```

---

### resume — 查看待处理项（只读）

```bash
python batch_manager.py resume --session <session-id>
```

---

### list — 列出所有 session

```bash
python batch_manager.py list
```

---

### cleanup — 清理旧 session

```bash
python batch_manager.py cleanup [--older-than 7]
```

## Agent 使用模式

```python
# 1. 创建 session
run("python batch_manager.py plan --session my-run --items items.json --batch-size 5")

# 2. 循环处理直到完成
while True:
    result = run("python batch_manager.py next --session my-run")
    if result.exit_code == 2:
        break  # 没有更多批次
    
    for item in result.json["items"]:
        try:
            process(item)
            run(f"python batch_manager.py complete --session my-run --item {item['id']}")
        except Exception as e:
            run(f"python batch_manager.py fail --session my-run --item {item['id']} --error '{e}'")

# 3. 验证完成
run("python batch_manager.py done --session my-run")
```

## Session 文件位置

Session 存储于 `~/.belt/sessions/<session-id>.json`。
