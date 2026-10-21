#!/bin/bash
# Block main-thread Python edits unless explicitly allowed.
#
# This hook enforces the Python skill pipeline by requiring all .py edits
# to go through subagents (which have the pipeline baked in).
#
# To bypass (for subagents): set CLAUDE_SUBAGENT_ID env var
# To bypass (manual override): set ALLOW_DIRECT_PYTHON_EDIT=1

# Check if we're in a subagent (subagents have this env var set)
if [[ -n "$CLAUDE_SUBAGENT_ID" ]]; then
    exit 0
fi

# Check for explicit override
if [[ -n "$ALLOW_DIRECT_PYTHON_EDIT" ]]; then
    exit 0
fi

# Block with informative message
echo ""
echo "=========================================="
echo "BLOCKED: Main thread cannot edit .py files directly"
echo "=========================================="
echo ""
echo "When Python skill is loaded, main agent is orchestrator only."
echo "Delegate to a subagent:"
echo ""
echo '  Agent({'
echo '    subagent_type: "code-hygiene",  # trivial fix'
echo '    # OR'
echo '    subagent_type: "bug",           # full pipeline'
echo '    prompt: "Apply this change: ...",'
echo '  })'
echo ""
echo "See: handoff-contract.md § Python File Edits"
echo "=========================================="
exit 1
