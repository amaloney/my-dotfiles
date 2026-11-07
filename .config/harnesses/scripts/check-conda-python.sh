#!/usr/bin/env bash
# PreToolUse hook: block if Python is system Python (not conda-managed).
# Exit 0 = allow, Exit 2 = block

set -euo pipefail

# Check if command contains python
cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null || echo "")
if [[ -z "$cmd" ]]; then
    exit 0
fi

# Only check commands that invoke python
if ! echo "$cmd" | grep -qE '(^|[[:space:]/])python[0-9.]*([[:space:]]|$)'; then
    exit 0
fi

# Find which python would be used
python_path=$(which python3 2>/dev/null || which python 2>/dev/null || echo "")
if [[ -z "$python_path" ]]; then
    echo "No python found on PATH" >&2
    exit 2
fi

# Resolve symlinks
real_python=$(realpath "$python_path" 2>/dev/null || readlink -f "$python_path" 2>/dev/null || echo "$python_path")

# Check if it's a conda-managed Python
if [[ "$real_python" == *"/conda/"* ]] || [[ "$real_python" == *"/miniforge/"* ]] || [[ "$real_python" == *"/anaconda/"* ]] || [[ "$real_python" == *"/miniconda/"* ]] || [[ "$real_python" == *"/.conda/"* ]]; then
    exit 0
fi

# Check CONDA_PREFIX (indicates active conda env)
if [[ -n "${CONDA_PREFIX:-}" ]]; then
    exit 0
fi

# System Python detected
echo "BLOCKED: System Python detected at $real_python" >&2
echo "Use 'scripts/crun' or activate a conda environment first." >&2
echo "Run: conda activate <env> OR use scripts/crun <command>" >&2
exit 2
