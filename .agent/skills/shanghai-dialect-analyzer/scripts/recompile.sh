#!/bin/bash
# Recompile the project and verify PDF meta

echo "Compiling project..."
uv run python xtask.py compile

if [ $? -eq 0 ]; then
    echo "Done! Output: shanghai-dialect-exercises.pdf"
else
    echo "Compilation failed."
fi
