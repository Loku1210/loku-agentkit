# 任务与 Prompt 归档协议

## 两条管理线

### 任务档案

保存某次正式任务的完整生命周期：需求、Prompt 版本、反馈、验证证据和状态。位置：

```text
tasks/active/<task-id>/
tasks/archive/<domain>/<year>/<task-id>/
```

### Prompt 库

只保存已经证明有效、去除项目特异路径和敏感信息、值得跨任务复用的 Prompt。位置：

```text
prompts/library/
```

任务 Prompt 不得直接散放在 `prompts/` 根目录。

## 建档条件

满足任一条件时建立任务档案：

- 生成正式、可交给目标 Agent 执行的 Prompt；
- 任务需要多轮反馈、修订或运行诊断；
- 使用 Workflow、Graph、文件修改、权限或工具；
- 任务结果可能形成长期可复用模板；
- 用户明确要求保存或归档。

普通解释、简短问答、未形成交付物的讨论不建档。

## 任务 ID 与领域

格式：

```text
YYYYMMDD-<domain>-<short-slug>
```

领域固定为：

- `research`
- `coding`
- `writing`
- `productivity`
- `investment`
- `other`

`short-slug` 使用简短小写英文和连字符。中文标题保存在 `TASK.md`，不塞入路径。

## 标准任务目录

```text
<task-id>/
├── TASK.md                  # 元数据、摘要、决策和当前状态
├── prompts/
│   └── prompt-v01.md        # 首版 Prompt，后续递增
├── feedback/
│   └── feedback-log.md      # 用户反馈与修订映射
├── evidence/
│   └── README.md            # 测试、路径、截图或验收记录
└── records/
    ├── claim-evidence-ledger.csv
    ├── asset-manifest.csv
    └── FINAL_PACKAGE.md
```

三份项目记录的字段由任务模板定义。旧任务无需机械补空文件；在重新进入 `running` 或 `review` 时按风险和交付复杂度补充。

## 状态

允许状态：

- `clarifying`：尚在质问和确认；
- `designed`：方案与 Prompt 已生成；
- `running`：用户已在目标项目执行；
- `feedback`：收到问题，等待或正在修订；
- `review`：目标产物等待验收；
- `completed`：有现实锚点或用户明确确认完成；
- `abandoned`：用户明确放弃；
- `superseded`：被新任务或方案替代。

前三类终态为 `completed`、`abandoned`、`superseded`，进入归档。不得只因 Agent 自评通过就标记 `completed`。

## Prompt 版本规则

- 初版：`prompt-v01.md`
- 修订版：`prompt-v02.md`、`prompt-v03.md`
- 已验收终版：`prompt-v03-final.md`
- 不使用 `latest.md`，当前版本以 `TASK.md` 和 `tasks/INDEX.md` 为准。
- 不覆盖旧版本，不直接修改 `-final` 文件；终版再修订时创建新版本。
- 每个新版本在开头写明：基于哪个版本、修订原因、对应反馈记录。

## 反馈闭环

```text
运行反馈
  → 写入 feedback/feedback-log.md
  → 判断是 Prompt 缺陷、执行偏航、输入缺失还是工具限制
  → 新建 Prompt 版本
  → 更新 TASK.md 当前版本与状态
  → 更新 tasks/INDEX.md
```

反馈日志至少包含日期、来源、现象、证据、诊断、修改决定和对应的新版本。

## 归档规则

以下情况移动到 `tasks/archive/<domain>/<year>/`：

- 用户确认完成，且已记录验收证据；
- 用户明确放弃；
- 新任务已取代旧任务，并在二者 `TASK.md` 中互相链接。

30 天没有活动时，只在索引中标记 `needs-review` 并询问用户，不静默归档。归档是移动，不删除；恢复时移回 `active/` 并记录原因。

归档后仍需：

- 更新 `TASK.md` 的状态和归档日期；
- 更新 `tasks/INDEX.md` 的状态、当前版本和路径；
- 保留全部 Prompt 版本、反馈与证据；
- 保留 Claim、资产与 Final Package 记录；若不适用，保留理由；
- 不因归档而把任务自动加入 Prompt 库。
- 创建 `ARCHIVE_RELOCATION.md`，记录归档前后路径前缀。历史快照和带校验值的证据保留当时绝对路径，不机械改写；通过 relocation 映射解析。

## Prompt 库晋升

同时满足以下条件才可晋升：

1. Prompt 已在真实目标项目使用；
2. 有确定性检查、强 Agent 审查或用户确认；
3. 已移除个人敏感信息、绝对项目路径和一次性背景；
4. 明确适用范围、目标 Agent、输入变量和已知限制；
5. 登记到 `prompts/LIBRARY_INDEX.md`。

晋升时复制并泛化，不从任务目录移动原件。库版本采用：

```text
<domain>-<purpose>-v1.md
```

## 清理与审计

- 每累计 10 个任务或每 3 个月检查一次索引。
- 查找无 `TASK.md` 的孤儿目录、索引中的断链、重复任务 ID、根目录散落 Prompt 和长期 `needs-review`。
- 不静默删除档案；无价值内容由用户确认后再处理。
