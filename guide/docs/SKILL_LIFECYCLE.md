# Skill 晋升与退役协议

## 单一正本

每个 Skill 在任一时点只能有一个可编辑正本：

- 草案或评测中：`<SKILL_WORKSPACE>/<skill-name>/`
- 已晋升：登记在 `<SKILL_REGISTRY>` 的 `canonical_path`
- Agent 入口：只使用指向正本的软链接，不复制文件

GUIDE 的任务档案可以保留发布时快照作为证据，但快照必须位于已归档任务中，不能作为可编辑 Skill 使用。

## 生命周期

1. `draft`：在 staging 中设计，允许包含 `SKILL.md`、references、scripts 和 fixtures。
2. `evaluating`：完成结构检查、代表性成功路径、失败路径和安全边界测试。
3. `promoted`：复制或移动为唯一正本，安装入口改为软链接；staging 删除 `SKILL.md`，只保留指针说明。
4. `retired`：移除安装入口，保留退役原因、替代 Skill 和最后版本记录。

每次状态变化更新 `<SKILL_REGISTRY>`、来源任务记录和项目变更记录。

## 脚本归属

- Skill 运行所必需的脚本必须随正本放在其 `scripts/` 中并纳入回归测试。
- 仅用于某次任务的脚本保留在任务档案，不进入 Skill。
- 具有写入、删除或外部副作用的辅助工具不能因为主题相关就自动并入 Skill；只有明确属于 Skill 能力、权限边界和测试覆盖时才打包。
- Skill 只负责识别或建议某类操作时，应明确写成“审计/建议”，不要暗示具备执行能力。

## 晋升 Gate

- `SKILL.md` 完整且只描述可执行能力；
- 必需 references、scripts 和 assets 齐全；
- 至少一个真实任务验证和一个确定性回归测试；
- 高风险动作有权限、失败和恢复边界；
- canonical path、版本或哈希、来源任务已登记；
- staging 不再保留第二份可发现的 `SKILL.md`。

不采用“长期保持两份 SKILL.md 哈希一致”作为治理方式；那会把重复正本制度化。
