#!/bin/sh
# Create the ten seeded issues from docs/seed-issues/*.md (title = first line, labels = "Labels:" line).
set -eu
R=suchipizza/Topoli
for f in docs/seed-issues/*.md; do
  title=$(sed -n '1s/^# //p' "$f")
  labels=$(sed -n 's/^Labels: //p' "$f")
  body=$(sed '1d;/^Labels: /d' "$f")
  if gh issue list -R "$R" --search "\"$title\" in:title" --state all --json title --jq '.[].title' | grep -qx "$title"; then
    echo "exists: $title"; continue
  fi
  gh issue create -R "$R" --title "$title" --label "$labels" --body "$body" >/dev/null
  echo "created: $title"
done
