#!/bin/sh
# Rebuilds the corpus and the questions from world.py, then checks them.
set -e
cd "$(dirname "$0")"
PY="${PYTHON:-../.venv/bin/python}"
rm -rf ../corpus && mkdir -p ../corpus/sales ../corpus/operations ../corpus/suppliers ../corpus/finance ../corpus/hr ../corpus/meetings ../corpus/products ../corpus/support
$PY render_text.py
$PY render_visual.py
$PY questions.py
$PY ../scripts/verify.py
