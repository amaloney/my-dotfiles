#!/usr/bin/env bash
# Deprecated shim — the graph logic moved to Python:
#   llm-skills-network build --graph [--check | --dependents <skill> | --output <path>]
set -o errexit -o nounset -o pipefail

echo "deprecated: use llm-skills-network build --graph ..." >&2
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/llm-skills-network" build --graph "$@"
