---
name: loku-guide
description: Use when a request is ambiguous, tool-dependent, multi-step, high-risk, or needs a complete prompt for another agent.
---

# loku:guide

Turn one request into a clarified plan, an execution architecture, a target-agent choice, and a complete reusable prompt. Do not execute the target task unless the user separately asks for execution.

## Required references

Read only what the request needs:

- Architecture: `../../guide/docs/AGENT_ROUTING.md`
- Target runtime: `../../guide/docs/TARGET_AGENT_ROUTING.md`
- Task prompt: `../../guide/prompts/TASK_PROMPT_TEMPLATE.md`
- Long-lived memory: `../../guide/docs/MEMORY_PROTOCOL.md`
- Archiving: `../../guide/docs/ARCHIVE_PROTOCOL.md`

## Workflow

1. Restate the observable outcome in one sentence.
2. If confidence is below 95%, ask 1–3 concrete questions together. State the assumptions that would otherwise be used.
3. Freeze inputs, allowed writes, forbidden actions, external side effects, budget, and stop conditions.
4. Choose the lightest effective architecture:
   - Direct: one response or low-risk edit.
   - Loop: one agent can execute, test, and correct.
   - Workflow: ordered steps have deterministic gates.
   - Graph: independent roles need isolation, parallelism, or maker–checker review.
5. Select the target agent based on actual tools, permissions, context limits, and cost—not brand reputation.
6. Fill the task template completely. Replace every bracketed field.
7. Add a reality anchor that independently demonstrates completion.

## Output contract

Return, in order:

1. `Clarified requirement`
2. `Architecture` with Direct/Loop/Workflow/Graph and one-sentence rationale
3. `Target agent` with capability rationale
4. `Complete prompt` in one fenced block
5. `Acceptance anchors and unresolved decisions`

## Synthetic example

Request: “Clean up these configuration files.”

Clarification: identify the authorized directory, define “clean up,” confirm whether formatting changes are allowed, and name the validation command. If all files follow one schema and can be checked mechanically, choose a Workflow; if each file needs interpretation plus independent review, consider a minimal Graph.

## Common mistakes

- Treating “use multiple agents” as a quality requirement rather than a costed architecture choice.
- Naming a target runtime before checking required tools and permissions.
- Using “looks good” as acceptance evidence.
- Leaving placeholders or private absolute paths in the final prompt.
