# Installation

## Use the guide directly

Copy `guide/` into a project-owned documentation directory, or keep this repository available as a read-only reference. Start with `guide/README.md`.

## Install a skill

Copy or symlink one directory from `skills/` into the skill directory supported by your agent runtime. Keep each `SKILL.md` beside any relative references it names.

Example layout:

```text
<AGENT_SKILLS_DIR>/
└── guide/
    └── SKILL.md
```

For `loku:guide`, retain the repository layout because the skill references `../../guide/`.

## Validate

From the repository root:

```bash
bash guide/scripts/validate-guide.sh
```

Before using a shell-based skill, read its safety section and replace placeholders such as `<PROJECT_ROOT>` with an explicitly authorized path.
