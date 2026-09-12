**小红书：@Loku🥕🍏**

# loku-agentkit

<p align="center"><b>简体中文</b> · <a href="#english">English</a></p>

`loku-agentkit` 是一套通用的 agent 协作工具包。它不替你执行任务，而是帮你把"模糊的想法"
变成"清晰、可交付、可验收"的任务，并在多 agent 协作、延迟任务、交接日志、无人值守探索等
场景里，提供一套有边界、可追溯的方法。

核心由 5 个 skill 组成，其中 **`guide` 是主打**。

---

## 🌟 主打：`guide` —— 新手向导 + 随时在线的导师

**要解决的问题**：很多刚接触 AI / agent 的人，有一个想法或一个问题，却**不知道该用什么工具、
怎么把它交给 AI 才能真正做成**。`guide` 就是为这一步而生的。

**它怎么帮你**：你只需要用大白话描述"我现在遇到的问题 / 我想做的事"，`guide` 会：

1. **听懂 + 答疑**：用简单易懂的方式解释可行的做法，先不急着写代码；
2. **确认理解**：在对你的想法有 **95% 把握**之前，只问你 1–3 个关键问题（并说明如果你不答，
   它会默认怎么假设）；
3. **给方案 + Prompt**：把需求冻结清楚（能改什么、不能碰什么、怎样算完成），选一个最轻的
   执行形态（Direct / Loop / Workflow / Graph），再给你一段**可直接复制去用的完整 Prompt**
   和执行方法；
4. **陪你调试**：你把 Prompt 拿到目标项目目录里运行，遇到报错 / 结果不对，**把问题贴回来**，
   `guide` 会帮你优化方案、修正 Prompt，直到跑通。

一句话：**`guide` = 新手指引 + 一个随时都在的导师**，把"我不知道怎么让 AI 做这件事"变成
"我拿到一段能用的 Prompt 和清晰的下一步"。

**输出固定五段**：`澄清后的需求` → `执行架构（及理由）` → `目标 agent（及理由）` →
`完整 Prompt（一整块）` → `验收锚点与未决问题`。

### 上手案例（新手视角）

> **你说**：我有一个文件夹全是 PDF，想按里面的标题自动重命名整理，但我不懂代码，也不知道
> 让 AI 怎么做。
>
> **guide 会**：先问你 1–3 个关键问题（哪个目录？"整理"具体指什么？允许移动文件吗？用什么
> 命令算验证成功？）→ 冻结边界（只在该目录内操作、不删原文件）→ 判断这是一个有确定步骤的
> **Workflow** → 产出一段完整 Prompt，让你贴给自己的编程 agent 去执行 → 你运行时若报
> "找不到某字段"，把报错贴回来，guide 帮你把 Prompt 改到能跑通。

调用：把上面的话直接发给装了 `loku:guide` 的 agent 即可（默认只做"需求编译"，不会擅自执行）。

---

## 其余 4 个 skill

### 🤝 `coop` —— 双 agent 分工（控制者 × 执行者）
**功能**：一个"控制者"agent 负责澄清、规划、写任务卡、派活、**独立复查**结果；一个"执行者"
agent 只在任务卡边界内干活。谁都不会因此获得比你授权更大的权限。
**优势**：maker–checker 双人校验，既能并行提速，又不放大风险；只把**短、原子、可客观验证**的
任务外派，判断类 / 长上下文的活儿留在控制者手里。
**上手**：`coop on` 开启 → `coop run <任务>` 派一个边界清晰的小任务 → 控制者看实际 diff 跑验收 →
`coop off` 关闭。（模式开关只是偏好信号，不授权任何写入 / 删除 / 外发。）

### ⏰ `defer-task` —— 延迟的本地任务
**功能**：把一条**你已批准**的 shell 命令安排到稍后执行，不扩大它的权限（命令真正运行时仍走
正常授权提示）。用随附的 `deferctl.py`（仅标准库）管理。
**优势**：额度 / 时间不凑手时，先排期，到点自动在指定目录跑；全程可 list / status / cancel 追踪。
**上手**：
```bash
python3 <SKILL_DIR>/deferctl.py schedule --delay 2h30m --cwd <项目目录> --cmd '<命令>' --label '<备注>'
python3 <SKILL_DIR>/deferctl.py list
```
> 兼容性：macOS launchd 已原生验证；Linux / Windows 适配器仅静态 / 单元测试，未做原生宿主验证。

### 🗂 `handoff-compact` —— 安全压缩交接日志
**功能**：当 append-only 的 `AGENT_HANDOFF.md` 太长时，**保留表头和最近 N 条原文**，把更早的
条目折叠成摘要，并把**完整旧条目归档**到 `AGENT_HANDOFF_archive.md`（绝不硬删），压缩前先备份。
**优势**：日志瘦身但不丢信息——决策、证据边界、未决事项、可追溯性全部保留。
**上手**：`handoff-compact --dir=<项目目录> --keep=5 --threshold=120`（低于阈值直接跳过）。

### 🌙 `overnight` —— 有边界的无人值守探索
**功能**：你不在时，让 agent 在**明确的写入 / 网络 / 下载 / 停止边界**内，继续做安全、可追溯的
探索、验证与报告；早上给你一份成果 + 阻塞清单。
**优势**：先冻结允许 / 禁止的操作，再干活；生成候选 → 查重与来源核验 → 预注册对比 → 轻量实现，
每一步留输入 / 命令 / 输出路径。绝不越权提交、发布、删除或装系统级依赖。
**上手**：发起时一次性确认 3 件事（目标与排除项 / 授权写入目录 / 网络与下载额度），其余按只读
处理。

---

## 安装

见 [INSTALL.md](INSTALL.md)。文件都是纯 Markdown 和 shell 脚本；只安装你需要的 skill，
安装时保留相对目录结构，并在开启写权限前审阅所有命令，然后跑 `python3 verify.py` 检查引用完整。

## 原创声明

Direct/Loop/Workflow/Graph 路由框架、澄清方法、任务卡契约、验收锚点方法、记忆 / 归档协议
以及打包的提示词模板，均为 Loku1210 发布的原创材料。Skill 文件遵循可移植的 `SKILL.md` 约定。

## 许可

MIT。见 [LICENSE](LICENSE)。

<br>

---

# English

<p align="center"><a href="#loku-agentkit">简体中文</a> · <b>English</b></p>

`loku-agentkit` is a general-purpose toolkit for agent collaboration. It does not execute
your task for you; it helps turn a vague idea into a **clear, deliverable, verifiable**
task, and provides bounded, traceable methods for multi-agent collaboration, deferred
tasks, handoff logs, and unattended exploration.

It is built from 5 skills, and **`guide` is the flagship**.

---

## 🌟 Flagship: `guide` — a beginner's wizard and an always-on mentor

**The problem it solves.** Many people new to AI / agents have an idea or a problem but
**don't know which tool to use, or how to hand it to an AI to actually get it done.**
`guide` is built for exactly that step.

**How it helps.** Describe, in plain words, "the problem I'm facing / what I want to do,"
and `guide` will:

1. **Understand and explain** — lay out feasible approaches in plain language, without
   rushing to write code;
2. **Confirm understanding** — until it is **95% confident** it understands you, it asks
   only 1–3 concrete questions (and states the assumptions it would use otherwise);
3. **Give a plan + prompt** — freeze the requirement (what may change, what must not be
   touched, what counts as done), choose the lightest execution shape
   (Direct / Loop / Workflow / Graph), and hand you a **complete, copy-ready prompt** plus
   how to run it;
4. **Debug with you** — take the prompt into your target project, and if you hit an error
   or a wrong result, **paste it back**; `guide` refines the plan and prompt until it works.

In one line: **`guide` = a beginner's guide plus an always-available mentor**, turning
"I don't know how to make an AI do this" into "I have a working prompt and a clear next step."

**Fixed five-part output:** `Clarified requirement` → `Architecture (with rationale)` →
`Target agent (with rationale)` → `Complete prompt (one block)` → `Acceptance anchors and
unresolved decisions`.

### Getting started (beginner's view)

> **You:** I have a folder full of PDFs and want to auto-rename them by their titles, but
> I can't code and don't know how to have an AI do it.
>
> **guide:** asks 1–3 key questions (which directory? what does "organize" mean? may files
> be moved? which command validates success?) → freezes boundaries (operate only in that
> directory, don't delete originals) → decides this is a deterministic **Workflow** →
> produces a complete prompt for you to paste into your own coding agent → if running it
> raises "field not found," paste the error back and `guide` fixes the prompt until it runs.

Invoke it by sending the message above to an agent that has `loku:guide` installed (it only
"compiles" the requirement by default and won't execute on its own).

---

## The other 4 skills

### 🤝 `coop` — two-agent division of labor (controller × executor)
**What:** a *controller* agent clarifies, plans, writes the task card, dispatches, and
**independently reviews** the result; an *executor* agent works only inside the task-card
boundary. Neither gains authority beyond what you granted.
**Why:** a maker–checker loop that parallelizes safely; only **short, atomic, objectively
verifiable** tasks are delegated, while judgment / long-context work stays with the controller.
**Start:** `coop on` → `coop run <task>` for a well-bounded small task → controller reviews
the actual diff and runs acceptance → `coop off`. (The switch is only a preference signal;
it authorizes no writes, deletions, or external messaging.)

### ⏰ `defer-task` — a deferred local task
**What:** schedule a shell command **you have approved** to run later, without expanding its
authority (standard permission prompts still apply when it runs). Managed by the bundled,
stdlib-only `deferctl.py`.
**Why:** when time / quota isn't convenient, schedule it and it runs in the chosen directory
on time; fully trackable via list / status / cancel.
**Start:**
```bash
python3 <SKILL_DIR>/deferctl.py schedule --delay 2h30m --cwd <PROJECT_ROOT> --cmd '<CMD>' --label '<LABEL>'
python3 <SKILL_DIR>/deferctl.py list
```
> Compatibility: macOS launchd is natively validated; Linux / Windows adapters are
> static/unit-tested only, without native-host validation.

### 🗂 `handoff-compact` — safe compaction of handoff logs
**What:** when an append-only `AGENT_HANDOFF.md` gets too long, **keep the header and newest
N entries verbatim**, fold older ones into a digest, and **archive the full old entries** to
`AGENT_HANDOFF_archive.md` (never hard-deleted), backing up first.
**Why:** slim the log without losing information — decisions, evidence boundaries, unresolved
items, and recoverability are all preserved.
**Start:** `handoff-compact --dir=<PROJECT_ROOT> --keep=5 --threshold=120` (exits if below threshold).

### 🌙 `overnight` — bounded unattended exploration
**What:** while you're away, let an agent continue safe, traceable exploration, verification,
and reporting within **explicit write / network / download / stop boundaries**, and hand you
a morning deliverable plus a blocker list.
**Why:** freeze allowed / forbidden actions first, then work; generate candidates → novelty
and source checks → preregister the comparison → implement lightly, recording inputs /
commands / output paths at every step. Never commits, publishes, deletes, or installs
system-wide without authority.
**Start:** confirm three things up front (goal & exclusions / authorized write directory /
network & download allowance); otherwise it stays read-only.

---

## Install

See [INSTALL.md](INSTALL.md). The files are plain Markdown and shell scripts; install only
the skills you need, keep the relative directory structure, review all commands before
enabling write access, then run `python3 verify.py` to check references.

## Originality statement

The Direct/Loop/Workflow/Graph routing framework, clarification method, task-card contract, acceptance-anchor method, memory/archive protocols, and packaged prompt templates are original material released by Loku1210. Skill files follow the portable `SKILL.md` convention.

## License

MIT. See [LICENSE](LICENSE).
