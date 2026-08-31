#!/usr/bin/env bash
set -euo pipefail

if (( $# != 2 )); then
  echo 'Usage: bash guide/scripts/archive-task.sh <task-id> <completed|abandoned|superseded>'
  exit 2
fi

task_id="$1"; final_status="$2"
case "$final_status" in completed|abandoned|superseded) ;; *) echo "Invalid status"; exit 2 ;; esac

guide_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
task_store="${AGENTKIT_TASK_STORE:-$guide_root/tasks}"
source_dir="$task_store/active/$task_id"
task_file="$source_dir/TASK.md"
[[ -f "$task_file" ]] || { echo "Active task not found: $task_id"; exit 1; }

domain="$(sed -n 's/^domain: "\(.*\)"/\1/p' "$task_file" | head -1)"
[[ -n "$domain" ]] || { echo "Task domain missing"; exit 1; }
target_dir="$task_store/archive/$domain/${task_id:0:4}/$task_id"
[[ ! -e "$target_dir" ]] || { echo "Archive target exists: $target_dir"; exit 1; }

archive_date="$(date +%Y-%m-%d)"
tmp_task="$(mktemp)"
trap 'rm -f "$tmp_task"' EXIT
awk -v status="$final_status" '/^status:/ { print "status: \"" status "\""; next } { print }' "$task_file" > "$tmp_task"
mv "$tmp_task" "$task_file"
mkdir -p "$(dirname "$target_dir")"
mv "$source_dir" "$target_dir"
printf '# Archive relocation\n\n- Task ID: `%s`\n- Archived: %s\n- Status: `%s`\n- Previous prefix: `%s/`\n- Current prefix: `%s/`\n' "$task_id" "$archive_date" "$final_status" "$source_dir" "$target_dir" > "$target_dir/ARCHIVE_RELOCATION.md"
echo "Archived task: $target_dir"
