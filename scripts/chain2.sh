#!/bin/bash
# stage runner: waits for main4 batch, then runs supplementary experiments sequentially
cd "$(dirname "$0")/.."
export PYTHONPATH=src
wait_done() { # $1 log file
  local total
  while ! grep -q "jobs," "$1" 2>/dev/null; do sleep 20; done
  total=$(grep -m1 "jobs," "$1" | sed -E 's/.*, ([0-9]+) to run.*/\1/')
  while [ "$(grep -c '^DONE' "$1")" -lt "$total" ]; do sleep 30; done
}
wait_done logs/main4_k45.log
# S1 ablation (no budget) for the remaining states
python scripts/ablation_nobudget.py abl 2 MT NE NM IA KS AR MS NV UT CT OK > logs/abl_rest.log 2>&1
# S2 budget sweep on k=2 states
LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py sweep 2 5 120 2,3,4 NH ME RI > logs/sweep.log 2>&1
# S3 tolerance sensitivity
EPS=1/200 LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py eps05 2 5 120 k-1 NH ME RI ID WV > logs/eps05.log 2>&1
EPS=1/50 LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py eps2 2 5 120 k-1 NH ME RI ID WV > logs/eps2.log 2>&1
# S4 robust scenario sets (all statewide contests, up to 3)
CONTESTS=ALL3 LB_SECONDS=30 MAX_UNKNOWN=2 python scripts/run_jobs.py robust 2 5 120 k-1 NH ME RI ID WV MT > logs/robust.log 2>&1
# S5 resolution ladder
python scripts/resolution_ladder.py ladder 2 NH ME RI > logs/ladder.log 2>&1
