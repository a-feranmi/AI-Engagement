#!/usr/bin/env bash
set -euo pipefail
python run_all.py
python -m streamlit run app/app.py
