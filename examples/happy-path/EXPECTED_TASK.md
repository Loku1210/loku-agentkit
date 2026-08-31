# Complete synthetic task card

## Clarified requirement

Inspect Markdown files under `sample-notes/`, resolve each relative Markdown link
against its containing file, and write a deterministic broken-link report.

## Architecture

Workflow: inventory files, validate links, write the report, then independently rerun
the checker against the report fixture.

## Target agent

Use a local coding agent with read access to `sample-notes/`, write access only to
`output/`, and shell access for the validation command.

## Allowed writes

- `output/link-report.md`

## Forbidden actions

- Do not edit or rename anything under `sample-notes/`.
- Do not access the network, commit, push, or delete files.

## Complete prompt

Inventory every `*.md` file under `sample-notes/`. For each relative Markdown link,
resolve the target from the source file's directory and record whether it exists.
Write `output/link-report.md` with source file, line, link target, and status. Preserve
the input tree unchanged. Stop if an input cannot be read.

## Acceptance anchors

- `find sample-notes -type f -name '*.md' -exec shasum -a 256 {} +` is unchanged
  before and after execution.
- The synthetic checker exits `0` and confirms every planted broken link is listed.

## Stop conditions

Stop without writing if `sample-notes/` is missing, if `output/` is outside the
authorized project root, or if validation cannot distinguish relative from external links.
