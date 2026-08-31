# General Agent Guide

This guide turns requests into bounded, testable work. It separates prompt design from execution, chooses the lightest effective architecture, and records decisions without importing private conversation history.

## Start here

For a complete small example before reading the protocols, open
`../examples/happy-path/REQUEST.md` and `../examples/happy-path/EXPECTED_TASK.md`.

1. Clarify purpose, inputs, write boundaries, exclusions, and success evidence.
2. Choose Direct, Loop, Workflow, or Graph with `docs/AGENT_ROUTING.md`.
3. Select a compatible target agent with `docs/TARGET_AGENT_ROUTING.md`.
4. Draft the task with `prompts/TASK_PROMPT_TEMPLATE.md`.
5. Define a reality anchor: a command, opened artifact, authoritative comparison, or external state that proves completion.
6. Archive task-specific prompts separately from reusable templates.

## Contents

- `docs/`: routing and governance protocols.
- `prompts/`: reusable task and feedback templates plus a sanitized example library.
- `scripts/`: optional task scaffolding, archiving, and distribution validation.

This distribution intentionally excludes personal memory, private outputs, project histories, workspace rules, and third-party skill catalogs.
