#!/bin/bash
# Quick check for a specific lesson's problems

if [ -z "$1" ]; then
    echo "Usage: ./check_lesson.sh lesson-N"
    exit 1
fi

LESSON=$1
echo "--- Analysing $LESSON ---"
uv run python xtask.py analyze displacement "$LESSON"
echo ""
echo "--- Dry-run Fixes for $LESSON ---"
uv run python xtask.py fix "$LESSON" --dry-run
