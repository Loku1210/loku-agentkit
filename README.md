**小红书：@Loku🥕🍏**

# loku-agentkit

<p align="center"><b>简体中文</b> · <a href="#english">English</a></p>

`loku-agentkit` 是一套通用的 agent 协作工具包，覆盖任务路由、提示词设计、记忆治理与
基于证据的交接。它帮你把一个模糊的请求变成一张有边界的任务卡，选择合适的执行形态，并
定义可观察的验收标准。

## 组成

- `guide/`：路由、记忆、归档、提示词与 skill 生命周期方法。
- `skills/guide/`：`loku:guide`，把请求转成提示词的路由器。
- `skills/coop/`：控制器–执行器协作协议。
- `skills/defer-task/`：延迟本地任务 MVP。macOS launchd 已做原生验证；Linux 与 Windows
  适配器仅做静态 / 单元测试，未做原生宿主验证。见 [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)。
- `skills/handoff-compact/`：对 append-only 交接日志做安全压缩。
- `skills/overnight/`：有边界的无人值守探索。

## 安装

见 [INSTALL.md](INSTALL.md)。文件都是纯 Markdown 和 shell 脚本；只安装你需要的 skill，
并在开启写权限前审阅所有命令。

## 五分钟上手

1. 读 [`examples/happy-path/REQUEST.md`](examples/happy-path/REQUEST.md) 里的合成请求。
2. 与 [`examples/happy-path/EXPECTED_TASK.md`](examples/happy-path/EXPECTED_TASK.md) 里那张
   完整、无占位符的任务卡对照。
3. 跑仓库自带的检查：

```bash
python3 verify.py
```

这个示例展示了最短的有用流程：先厘清可观察的结果，选择一个 Workflow，冻结允许的写入与
禁止的操作，再定义基于现实的验收锚点。

## 原创声明

Direct/Loop/Workflow/Graph 路由框架、澄清方法、任务卡契约、验收锚点方法、记忆 / 归档协议
以及打包的提示词模板，均为 Loku1210 发布的原创材料。Skill 文件遵循可移植的 `SKILL.md` 约定。

## 许可

MIT。见 [LICENSE](LICENSE)。

<br>

---

# English

<p align="center"><a href="#loku-agentkit">简体中文</a> · <b>English</b></p>

`loku-agentkit` is a general-purpose toolkit for agent collaboration, task routing, prompt design, memory governance, and evidence-based handoffs. It helps turn an unclear request into a bounded task card, select an execution shape, and define observable acceptance criteria.

## Components

- `guide/`: routing, memory, archive, prompt, and skill-lifecycle methods.
- `skills/guide/`: `loku:guide`, the request-to-prompt router.
- `skills/coop/`: a controller–executor collaboration protocol.
- `skills/defer-task/`: a deferred local task MVP. macOS launchd is natively
  exercised; the Linux and Windows adapters are static/unit-tested only, with no
  native-host validation. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).
- `skills/handoff-compact/`: safe compaction for append-only handoff logs.
- `skills/overnight/`: bounded unattended exploration.

## Install

See [INSTALL.md](INSTALL.md). The files are plain Markdown and shell scripts; install only the skills you need and review all commands before enabling write access.

## Five-minute happy path

1. Read the synthetic request in [`examples/happy-path/REQUEST.md`](examples/happy-path/REQUEST.md).
2. Compare it with the complete, placeholder-free task card in
   [`examples/happy-path/EXPECTED_TASK.md`](examples/happy-path/EXPECTED_TASK.md).
3. Run the repository checks:

```bash
python3 verify.py
```

The example shows the shortest useful flow: clarify the observable outcome, choose a
Workflow, freeze allowed writes and forbidden actions, then define reality-based
acceptance anchors.

## Originality statement

The Direct/Loop/Workflow/Graph routing framework, clarification method, task-card contract, acceptance-anchor method, memory/archive protocols, and packaged prompt templates are original material released by Loku1210. Skill files follow the portable `SKILL.md` convention.

## License

MIT. See [LICENSE](LICENSE).
