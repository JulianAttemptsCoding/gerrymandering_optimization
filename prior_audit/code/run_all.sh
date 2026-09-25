#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
{
  echo "== iter1 =="; python3 qc_checks.py
  echo "== iter2 =="; python3 qc_checks_iter2.py
  echo "== iter3 =="; python3 qc_checks_iter3.py
} 2>&1 | tee ../results/run_log.txt
