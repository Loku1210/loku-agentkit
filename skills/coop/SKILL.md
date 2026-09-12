---
name: coop
description: Use when different local AI agents (e.g. Claude Code, Codex) should collaborate on one job — one drafts, another independently reviews — through a bounded, objectively verifiable maker–checker loop.
---

# Cross-agent cooperation (controller × executor)

Let different **local AI agents from different vendors** work on one job together. One agent (the controller) clarifies, plans, and defines a bounded task card; another agent — deliberately a **different model / brand** (for example Codex drafts, Claude Code reviews) — runs it and returns a result. The controller then **independently reviews** that result and iterates over several rounds. Using a second, independent model to check the first lowers the error rate and raises final quality, without granting either agent broader authority than the user supplied.

## Optional mode state

A host may persist opt-in state at `<AGENT_STATE_DIR>/coop-active`. The path must be configured by the installer; this skill never assumes a home-directory layout.

Supported intent:

```text
coop on
coop off
coop status
coop run <task>
```

Mode state is only a preference signal. It does not authorize delegation, file writes, external communication, elevated permissions, or destructive actions.

## Roles

- Controller: clarify, plan, define the task card, dispatch, inspect the actual diff or artifact, run acceptance checks, and report.
- Executor: operate only inside the task card, preserve unrelated changes, verify its work, and return the fixed report format.

## Delegation gate

Delegate only when the task is short, atomic, self-contained, bounded by explicit paths, and objectively verifiable. Keep it with the controller or provide a manual continuation prompt when it requires extensive conversation context, long-form judgment, slow external I/O, broad project access, or several tightly coupled phases.

## Dispatch mode: background run vs. manual paste

Decide per task how the other agent is invoked:

- **Background terminal run** — when a reviewed `<COOP_WRAPPER>` (or a platform-native delegation tool) can invoke the other agent headlessly in a small authorized working directory, and the task is short, bounded, and objectively verifiable. The controller dispatches, captures the process handle and exit code, then reviews the returned artifact.
- **Manual paste to a client** — when the job needs a rich client session, long conversation context, interactive tools, or a capability the headless CLI lacks. Do **not** force it into the background; output a complete, self-contained prompt and tell the user which client / agent to paste it into, then review what comes back.

Pick the lightest mode that still lets the controller independently verify the result. Iterate: draft → independent review by a different-brand agent → apply feedback → re-check, until the acceptance checks pass.

## Execution adapter

Use a reviewed local wrapper or platform-native delegation tool configured as `<COOP_WRAPPER>`. Do not invent a wrapper path. Before dispatch:

1. Probe the executor runtime with a read-only minimal request.
2. Use a small authorized working directory.
3. Keep the executor's final-message file separate from the business artifact.
4. Record the real process handle and exit code if the adapter is asynchronous.
5. Require non-empty artifact checks and scan logs for top-level runtime failure.

## Task-card contract

```text
Goal: <one observable result>
Inputs: <explicit files or sources>
Output: <artifact path distinct from final-message path>
Allowed changes: <exact paths>
Forbidden: <out-of-scope files, destructive actions, external side effects>
Steps: <one atomic workflow>
Verification: <command or deterministic checklist>
Report: Summary / Files changed / Commands run / Risks / Need controller review (y/n)
```

## Safety gates

- Commit, push, deletion, publication, credential use, and external communication require explicit task-level authority.
- The controller must inspect artifacts and rerun relevant checks; an executor's “done” statement is not evidence.
- If the working sandbox cannot cover the required output, stop and redesign the handoff. Do not widen the sandbox silently.
- On failure, retry the failed unit with a new self-contained task card and a bounded retry limit.

## Synthetic example

A controller needs five Markdown headings normalized in `docs/`. It sends the five file paths, exact heading rule, forbidden paths, and a link-check command. The executor edits only those files. The controller reviews the diff and reruns the link check before accepting.

## Common mistakes

- Delegating a multi-phase project as one “atomic” task.
- Reusing the same path for the artifact and the executor's final message.
- Polling by a broad process-name search instead of a captured process handle.
- Treating mode state as permission.
