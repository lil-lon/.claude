#!/bin/bash
set -e

if git diff --cached --quiet; then
  echo "No staged changes. Run 'git add' first."
  exit 1
fi

echo "=== Reviewing staged files ==="
git diff --cached --name-only
echo ""

git diff --cached | codex exec \
  --model gpt-5.5 \
  -c 'model_reasoning_effort="high"' \
  --sandbox read-only \
  "Review this staged diff for bugs, design issues, and security concerns. Label each finding with P1-P4 severity."
