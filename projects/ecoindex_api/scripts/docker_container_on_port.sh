#!/usr/bin/env bash
set -euo pipefail

port="${1:?port required}"

for id in $(docker ps -q 2>/dev/null); do
  if docker port "$id" 2>/dev/null | grep -qE "(0\.0\.0\.0|\[::\]|:::):${port}(/|$)"; then
    docker inspect -f '{{.Name}}' "$id" 2>/dev/null | sed 's/^\///'
    exit 0
  fi
done

exit 1
