#!/bin/sh
# Five questions from truth.json, asked through the colbymchenry/codegraph CLI. Offline, telemetry off.
export CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1 CODEGRAPH_NO_UPDATE_CHECK=1
cd /work
echo "### versions"; cat /versions.txt
codegraph init --local-only . 2>&1 | tail -5
echo "-- Q1 callers of dev_open"; codegraph callers dev_open
echo "-- Q2 callees of dev_open"; codegraph callees dev_open
echo "-- Q3 callees of timer_fire"; codegraph callees timer_fire
echo "-- Q4 callees of submit"; codegraph callees submit
echo "-- Q5 where is handle_uart"; codegraph query handle_uart
echo "-- extra: callers of uart_open"; codegraph callers uart_open
echo "-- extra: callers of heartbeat"; codegraph callers heartbeat
cat /sys/fs/cgroup/memory.peak | awk '{printf "peak_mb=%d\n", $1/1048576}'
