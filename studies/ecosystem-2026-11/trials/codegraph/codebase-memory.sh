#!/bin/sh
# Five questions from truth.json through codebase-memory-mcp's CLI mode. Offline.
cd /work/demo
echo "### versions"; cat /versions.txt
codebase-memory-mcp cli --quiet index_repository --repo-path /work/demo 2>&1 | tail -3
P=$(codebase-memory-mcp cli --quiet list_projects --format json | sed -n 's/.*"name": *"\([^"]*\)".*/\1/p' | head -1)
echo "project=$P"
for f in dev_open timer_fire submit heartbeat; do
  echo "-- trace_path $f (both directions)"; codebase-memory-mcp cli --quiet trace_path --project "$P" --function-name "$f" --direction both 2>&1 | head -40
done
echo "-- Q5 search handle_ and heartbeat"; codebase-memory-mcp cli --quiet search_graph --project "$P" --name-pattern '(handle_.*|heartbeat)' 2>&1 | head -20
cat /sys/fs/cgroup/memory.peak | awk '{printf "peak_mb=%d\n", $1/1048576}'
