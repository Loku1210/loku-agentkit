---
name: handoff-compact
description: Use when an append-only AGENT_HANDOFF.md has exceeded a practical size and older entries must be condensed without losing decisions, evidence boundaries, unresolved work, or recoverability.
---

# Compact an append-only handoff

Reduce the active handoff while preserving the header and newest entries verbatim. Archive every older source entry before replacing it with a digest.

## Parameters

- `--dir=<PROJECT_ROOT>`: directory containing `AGENT_HANDOFF.md`; default is the authorized current directory.
- `--keep=N`: newest entries to keep byte-for-byte; default 5.
- `--threshold=N`: minimum line count; default 120.

Entries are expected to begin with `## YYYY-MM-DD`.

## Invariants

1. Preserve the protocol header exactly.
2. Preserve the newest `--keep` entries exactly.
3. Copy the full older entries to `AGENT_HANDOFF_archive.md`; never hard-delete them.
4. Back up the original as `backup/AGENT_HANDOFF_pre_compact_<date>.md`.
5. Carry every unresolved review, unchecked next action, conflict, and evidence limitation into the digest.
6. Mark uncertain completion as unresolved; never infer closure from silence.

## Workflow

1. Resolve the authorized file and report line/character counts plus entry headings.
2. If below threshold, exit without writing.
3. Split header, compactable entries, and verbatim keep-zone by entry boundaries.
4. Extract milestones, still-current decisions, evidence boundaries, and unresolved items from the compactable entries.
5. Write backup first, then append complete compacted entries to the archive with a dated separator.
6. Rewrite the active handoff as header + digest + separator + untouched keep-zone.
7. Verify archive completeness, verbatim keep-zone equality, unresolved-item coverage, and final sizes.

## Digest contract

```markdown
## Historical digest (compacted YYYY-MM-DD; complete text in AGENT_HANDOFF_archive.md)

### Milestones
- <date — actor — material outcome>

### Current decisions and evidence boundaries
- <decision — evidence — limitation>

### Still unresolved
- <owner/status/next action, or ?>
```

## Synthetic example

An old entry says “review required: yes,” and a newer entry never closes it. The digest must retain it under “Still unresolved,” even if its implementation milestone is summarized to one line.

## Common mistakes

- Summarizing before writing the recoverable archive.
- Reformatting the keep-zone.
- Dropping an unresolved item because a later entry looks related.
- Resolving a conflict against a project rule file without user confirmation.
