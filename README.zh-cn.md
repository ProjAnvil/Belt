# Belt — 为 Claude Code 构建 AI 原生应用

**[English](README.md)**

**AI 原生应用**不是插件、Webhook 或封装层。
它是一个活在 AI *上下文内部*的一等工具：Claude 读取它的指令、调用它的脚本、将子任务委托给它自己的代理——全程无需离开对话。

Belt 是一个 **Go CLI 工具**，用于构建这一完整结构。运行 `belt new`，回答几个问题，即可得到一个完整的 `技能（skill）+ 子代理（subagent）+ 脚本（script）` 组合包，一条命令安装到 Claude Code。

> 隶属于 [projanvil](https://github.com/projanvil) 生态系统。

## 什么是 Belt 应用？

```
Claude Code
  └── ~/.claude/
        ├── skills/my-tool/
        │         ├── SKILL.md          ← AI 读取此文件作为指令
        │         ├── scripts/run.py    ← AI 可调用此脚本
        │         └── reference/
        │               ├── app.json   ← 运行时配置（应用数据目录）
        │               └── *.md       ← 已打包的组件参考文档
        └── agents/my-tool.md          ← AI 可委托任务给此代理
```

Belt 应用的每一部分都**专为 AI 读取或调用而设计**：

- **技能（Skill）** — `SKILL.md` 告诉 Claude 这个工具*做什么*以及*如何调用*
- **脚本（Script）** — AI 调用的 Python 脚本，用于执行真实计算
- **代理（Agent）** — Claude 可以委托复杂工作流的子代理 `.md` 文件
- **组件（Component）** — 可测试的自包含模块（例如 `batch-planner`），其参考文档直接注入到技能中，让 Claude 知道如何使用它

Belt 通过交互式提示生成完整结构，支持**双语**（en / zh-cn），并为每个应用附带 `install.sh` 和 `install.ps1`，一键集成到 Claude Code。

## 安装

### 从源码构建

```bash
cd cli
make build
sudo make install   # 将 belt 复制到 /usr/local/bin/
```

### 使用预编译二进制

从 [Releases](../../releases) 下载对应平台的二进制文件，放入 `$PATH` 即可。

## 快速开始

```bash
# 交互式脚手架——在 Belt 工作区根目录运行
belt new

# 指定目录生成
belt new ./my-projects

# 检查环境依赖
belt doctor
```

`belt new` 会引导你完成以下步骤：

1. **应用名称** — 作为 Claude Code 中的技能/代理标识符
2. **模板** — `empty`（空白占位符）或 `hello-app`（带示例问候功能）
3. **组件** *（仅 empty 模板）* — 多选要打包的可复用模块
4. **应用数据目录** — 应用存储运行时文件的位置（例如 `~/.claude/.my-tool`）
5. **语言** — `en` 或 `zh-cn`
6. **安装程序** — `both`（两个）、仅 `sh` 或仅 `ps1`

然后安装到 Claude Code：

```bash
cd my-tool
bash install.sh              # Linux / macOS
pwsh install.ps1             # Windows
bash install.sh --lang=zh-cn # 中文变体
```

Claude Code 会立即识别 `/my-tool`（技能）和 `@my-tool`（代理）。

## 仓库结构

```
belt/
├── cli/                          # Go CLI（belt 二进制）
│   ├── cmd/                      # Cobra 命令：new、doctor
│   ├── internal/scaffold/        # 模板嵌入与生成
│   │   └── templates/            # 嵌入式脚手架模板
│   │       ├── skills/           # 空白技能/脚本模板
│   │       ├── agents/           # 空白代理模板
│   │       ├── apps/hello-app/   # hello-app 模板集合
│   │       ├── component/        # 组件脚手架模板
│   │       ├── install.sh
│   │       ├── install.ps1
│   │       ├── app.json
│   │       └── README.md
│   ├── main.go
│   ├── go.mod
│   └── Makefile
├── components/                   # 可复用 Belt 组件
│   └── batch-planner/            # 持久化批处理状态机
│       ├── component.json
│       ├── scripts/
│       └── reference/            # 双语参考文档
│           ├── en/batch-planner.md
│           └── zh-cn/batch-planner.md
├── apps/                         # 示例/参考应用
│   └── hello-belt/
├── _template/                    # 人类可读模板源（仅参考）
└── README.md
```

## 生成的应用结构

```
my-tool/
├── skills/
│   ├── en/my-tool/SKILL.md       # 英文技能提示
│   ├── zh-cn/my-tool/SKILL.md    # 中文技能提示
│   └── scripts/my-tool/run.py    # 共享脚本（语言无关）
├── agents/
│   ├── en/my-tool.md
│   └── zh-cn/my-tool.md
├── app.json                      # 应用元数据及运行时数据目录
├── install.sh
├── install.ps1
└── README.md
```

`install.sh` / `install.ps1` 在安装时执行以下操作：
- 将技能文件链接到 `~/.claude/skills/my-tool/`
- 将 `~/.claude/skills/my-tool/reference/` 创建为真实目录
- 复制 `app.json` → `reference/app.json`
- 创建 `app.json` 中声明的 `app_dir`
- 将打包的组件参考 `.md` 文件链接到 `reference/`
- 将代理链接到 `~/.claude/agents/`

## 组件

组件是**可测试的 AI 可用构建块**——自包含的 Python 模块，逻辑层与 AI 接口层清晰分离：

- **脚本**：AI 调用以执行真实计算
- **双语参考文档**：注入到 `SKILL.md` 中，让 Claude 确切知道如何使用该组件
- **`pytest` 测试套件**：在 AI 使用之前，可像普通代码一样验证行为
- **`make test`**：每个组件开箱即用

这使得组件成为扩展 AI 能力最安全的方式：先写逻辑、测试代码，再通过参考文档将其暴露给 Claude。

在 `belt new` 时选择组件后，组件的参考文档摘要会注入到 `SKILL.md` 中，完整文档在安装时以符号链接形式写入 `reference/<comp>.md`。

创建新组件：

```bash
belt new --type=component my-component
```

结构：

```
components/my-component/
├── component.json
├── scripts/my-component.py     # AI 可调用的逻辑
├── reference/
│   ├── en/my-component.md      # AI 读取此文件了解组件用法
│   └── zh-cn/my-component.md
├── tests/
│   └── test_my-component.py   # AI 使用前先测试
├── Makefile                    # make test
└── requirements.txt
```

## 命令

| 命令 | 描述 |
|------|------|
| `belt new [path]` | 交互式生成新应用 |
| `belt new --type=component <name>` | 生成新组件 |
| `belt doctor` | 检查环境依赖 |

## 许可证

[MIT](LICENSE)
