#!/bin/bash
# second-round experiments: complete the k=2 supplementary tables (Montana, Idaho, West Virginia), then k>=6 pilot
cd "$(dirname "$0")/.."
export PYTHONPATH=src
LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py sweep 2 5 120 2,3,4 ID MT WV > logs/sweep2.log 2>&1
EPS=1/200 LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py eps05 2 5 120 k-1 MT > logs/eps05_mt.log 2>&1
EPS=1/50 LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py eps2 2 5 120 k-1 MT > logs/eps2_mt.log 2>&1
LB_SECONDS=40 MAX_UNKNOWN=2 python scripts/run_jobs.py main6 2 5 120 k-1 KY > logs/main6_ky.log 2>&1
