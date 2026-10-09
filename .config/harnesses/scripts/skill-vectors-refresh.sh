#!/usr/bin/env bash
# Deprecated shim — staleness logic moved into the CLI:
#   llm-skills-network build --skill-vectors --if-stale
set -o nounset

echo "deprecated: use llm-skills-network build --skill-vectors --if-stale" >&2
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/llm-skills-network" build --skill-vectors --if-stale "$@"
