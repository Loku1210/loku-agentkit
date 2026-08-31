---
name: overnight
description: Use when a user requests bounded unattended exploration, verification, or reporting while unavailable and supplies explicit write, network, download, and stop boundaries.
---

# Bounded unattended exploration

Continue safe, traceable work while the user is unavailable without expanding authorization.

## Startup gate

Confirm up to three missing items in one batch:

1. goal and exclusion criteria;
2. authorized write directory, defaulting only to `<PROJECT_ROOT>/overnight-work/` when the user has authorized `<PROJECT_ROOT>`;
3. network/download allowance, maximum download size, and whether new isolated environments are allowed.

If a material boundary remains unanswered, restrict work to read-only inspection of already authorized inputs and write only a blocker report when that report path is already authorized.

At the top of the report, freeze allowed writes, forbidden actions, network allowance, download cap, stop conditions, date, and the authoritative rule source.

## Workflow

1. Generate up to five candidates with source identity, testable claim, smallest useful check, reproducibility risk, and licensing boundary.
2. Check novelty or duplication against authoritative and primary sources. “Not found” never proves uniqueness.
3. Verify source identity, units, versions, labels, and availability; reject ambiguous inputs.
4. Before substantial execution, preregister the primary comparison, unit of analysis, null check, success threshold, and no-go condition.
5. Implement lightly only after identity, duplication, signal, and reproducibility gates pass. Record negative results without moving thresholds to rescue a candidate.
6. At each material stage, checkpoint inputs, commands, complete output paths, conclusion strength, and remaining risks.

## Safety boundary

- No permission bypass, broad allowlist, privilege escalation, credential flow, system-wide install, or persistent service.
- No commit, push, publication, external messaging, deletion, overwrite, or source-data modification without explicit authority.
- Do not run unreviewed hooks, extensions, or installation scripts.
- Install a pinned dependency only inside an explicitly authorized isolated environment; otherwise write an installation plan.
- On network failure, unclear identity, uncertain license, download overflow, or need for offline validation, record a blocker and move to another safe candidate.

## Morning deliverable

Write `OVERNIGHT_SUMMARY_<date>.md` inside the authorized directory with:

- candidate funnel;
- source and duplication checks;
- identity verification;
- passed and failed gates;
- artifact paths and commands;
- actions explicitly not performed;
- decisions that still require the user.

## Synthetic example

Goal: compare three public formatting specifications for a conversion tool. Allowed: read official documentation and write under `<PROJECT_ROOT>/overnight-work/`. Forbidden: installing converters, sending files externally, or modifying the application. Stop after 200 MB of downloads or two consecutive authentication failures.

A deferred scheduler may resume only this frozen scope; it cannot enable broader permissions.
