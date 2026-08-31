#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo 'Usage: bash guide/scripts/new-task.sh [--dry-run] <domain> <slug> <target-agent> [title] [target-project]'
  echo 'Domains: research coding writing productivity operations other'
}

dry_run=0
if [[ "${1:-}" == "--dry-run" ]]; then dry_run=1; shift; fi
if (( $# < 3 || $# > 5 )); then usage; exit 2; fi

domain="$1"; slug="$2"; target_agent="$3"; title="${4:-$slug}"; target_project="${5:--}"
case "$domain" in research|coding|writing|productivity|operations|other) ;; *) usage; exit 2 ;; esac
[[ "$slug" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo "Invalid slug: $slug"; exit 2; }

guide_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
task_store="${AGENTKIT_TASK_STORE:-$guide_root/tasks}"
created_date="$(date +%Y-%m-%d)"
task_id="$(date +%Y%m%d)-${domain}-${slug}"
task_dir="$task_store/active/$task_id"

if [[ -e "$task_dir" ]]; then echo "Task already exists: $task_dir"; exit 1; fi
if (( dry_run )); then printf 'Would create: %s\nTask ID: %s\n' "$task_dir" "$task_id"; exit 0; fi

mkdir -p "$task_dir/prompts" "$task_dir/feedback" "$task_dir/evidence"
{
  printf '%s\n' '---'
  printf 'task_id: "%s"\nstatus: "clarifying"\ndomain: "%s"\ntarget_agent: "%s"\ntarget_project: "%s"\ncreated: "%s"\n%s\n\n' "$task_id" "$domain" "$target_agent" "$target_project" "$created_date" '---'
  printf '# %s\n\n## Purpose\n\n[Fill in]\n\n## Observable outcome\n\n[Fill in]\n\n## Boundaries\n\n- Allowed: [Fill in]\n- Forbidden: [Fill in]\n\n## Acceptance anchor\n\n[Command, opened artifact, authoritative comparison, or external state]\n' "$title"
} > "$task_dir/TASK.md"
printf '# Prompt v01\n\nUse `%s/prompts/TASK_PROMPT_TEMPLATE.md` and replace all placeholders.\n' "$guide_root" > "$task_dir/prompts/prompt-v01.md"
printf '# Feedback log\n\nNo feedback yet.\n' > "$task_dir/feedback/feedback-log.md"
printf '# Evidence\n\nRecord commands, artifacts, and acceptance evidence here.\n' > "$task_dir/evidence/README.md"
echo "Created task: $task_dir"
