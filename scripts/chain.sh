#!/bin/bash
# wait for first batch then launch k>=4 batch
cd "$(dirname "$0")/.."
while ! (grep -q "DONE ('NM', 'R'" logs/main2_k23.log && grep -q "DONE ('NM', 'D'" logs/main2_k23.log); do sleep 20; done
PYTHONPATH=src LB_SECONDS=40 MAX_UNKNOWN=2 python scripts/run_jobs.py main 2 5 120 k-1 IA MS NV CT UT AR OK KS > logs/main2_k45.log 2>&1
