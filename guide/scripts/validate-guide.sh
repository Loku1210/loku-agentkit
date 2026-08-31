#!/usr/bin/env bash
set -euo pipefail

guide_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="$(cd "$guide_root/.." && pwd)"
required=(
  README.md LICENSE CREDITS.md INSTALL.md guide/README.md
  guide/docs/AGENT_ROUTING.md guide/docs/TARGET_AGENT_ROUTING.md
  guide/docs/MEMORY_PROTOCOL.md guide/docs/ARCHIVE_PROTOCOL.md guide/docs/SKILL_LIFECYCLE.md
  guide/prompts/TASK_PROMPT_TEMPLATE.md guide/prompts/FEEDBACK_TEMPLATE.md
  guide/prompts/README.md guide/prompts/LIBRARY_INDEX.md guide/prompts/library/README.md
  guide/prompts/library/research-synthetic-expected-figure-atlas-v1.md
  guide/scripts/new-task.sh guide/scripts/archive-task.sh guide/scripts/validate-guide.sh
  skills/guide/SKILL.md skills/coop/SKILL.md skills/defer-task/SKILL.md
  skills/handoff-compact/SKILL.md skills/overnight/SKILL.md
)

errors=0
for path in "${required[@]}"; do
  [[ -s "$repo_root/$path" ]] || { echo "MISSING_OR_EMPTY: $path"; errors=$((errors + 1)); }
done

while IFS= read -r file; do echo "UNWANTED_METADATA_FILE: ${file#"$repo_root/"}"; errors=$((errors + 1)); done < <(find "$repo_root" -type f -name '.DS_Store' -print)

deny='(^|/)(\.remember|\.work|memory|outputs|skill-staging|docs/superpowers)(/|$)|(^|/)(CLAUDE|AGENTS|CHANGELOG)\.md$|(^|/)docs/(PROJECT_RECORDS|REFERENCES)\.md$'
while IFS= read -r path; do
  rel="${path#"$repo_root/"}"
  if [[ "$rel" =~ $deny ]]; then echo "DENYLIST_PATH: $rel"; errors=$((errors + 1)); fi
done < <(find "$repo_root" -mindepth 1 -print)

for skill in guide coop defer-task handoff-compact overnight; do
  file="$repo_root/skills/$skill/SKILL.md"
  grep -q '^---$' "$file" || { echo "INVALID_FRONTMATTER: skills/$skill/SKILL.md"; errors=$((errors + 1)); }
  grep -q '^name:' "$file" || { echo "MISSING_SKILL_NAME: $skill"; errors=$((errors + 1)); }
  grep -q '^description:' "$file" || { echo "MISSING_SKILL_DESCRIPTION: $skill"; errors=$((errors + 1)); }
done

if (( errors )); then echo "Agentkit validation failed with $errors error(s)."; exit 1; fi
echo "Agentkit validation passed: ${#required[@]} required files and denylist paths checked."
