# loku-agentkit

`loku-agentkit` is a general-purpose toolkit for agent collaboration, task routing, prompt design, memory governance, and evidence-based handoffs. It helps turn an unclear request into a bounded task card, select an execution shape, and define observable acceptance criteria.

## Components

- `guide/`: routing, memory, archive, prompt, and skill-lifecycle methods.
- `skills/guide/`: `loku:guide`, the request-to-prompt router.
- `skills/coop/`: a controller–executor collaboration protocol.
- `skills/defer-task/`: a macOS-only deferred local task MVP.
- `skills/handoff-compact/`: safe compaction for append-only handoff logs.
- `skills/overnight/`: bounded unattended exploration.

## Install

See [INSTALL.md](INSTALL.md). The files are plain Markdown and shell scripts; install only the skills you need and review all commands before enabling write access.

## Originality statement

The Direct/Loop/Workflow/Graph routing framework, clarification method, task-card contract, acceptance-anchor method, memory/archive protocols, and packaged prompt templates are original material released by `<PROJECT_AUTHOR>`. Third-party product names are used only to describe interoperability where necessary; no third-party skill catalog or proprietary skill bundle is included.

## License

MIT. See [LICENSE](LICENSE).
