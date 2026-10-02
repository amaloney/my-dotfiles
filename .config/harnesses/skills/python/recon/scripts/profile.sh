#!/usr/bin/env bash
# =============================================================================
# profile.sh - Python project recon; emit .harness/code_index/profile.json
#
# Usage: run from the repo root
#   ~/.config/harnesses/skills/python/recon/scripts/profile.sh
#
# Scans the repo (python/recon steps 1-4), writes the profile.json skeleton,
# populating cheaply-detectable fields (name, type, python_version, src_layout).
# Other fields stay null/empty for agent review. Re-run to overwrite.
# =============================================================================
set -o errexit -o nounset -o pipefail

for tool in fd rg; do
  command -v "$tool" >/dev/null || { echo "error: $tool required" >&2; exit 1; }
done

out_dir=".harness/code_index"
out_file="$out_dir/profile.json"
mkdir -p "$out_dir"

py=""
[[ -f pyproject.toml ]] && py="$(cat pyproject.toml)"
dep() { grep -Eiq "(^|[\"' ,])($1)[][ >=<~^=\"',]" <<<"$py"; }

# Step 1: detect project type
ptype="library"
if dep 'flask|django|fastapi|starlette'; then ptype="webapp";
elif dep 'click|typer|fire' || compgen -G "*/__main__.py" >/dev/null || compgen -G "*/cli.py" >/dev/null; then ptype="cli";
elif dep 'pandas|numpy|scipy|jupyter' || compgen -G "*.ipynb" >/dev/null; then ptype="datascience";
fi
if [[ $(fd -H '^pyproject\.toml$' --min-depth 2 2>/dev/null | wc -l) -gt 0 ]]; then ptype="monorepo"; fi

# Step 2: name + python_version + src_layout
name="$(basename "$PWD")"
pyver="null"
if [[ -n "$py" ]]; then
  n="$(rg -oN '^name\s*=\s*"([^"]+)"' -r '$1' pyproject.toml | head -1 || true)"
  [[ -n "$n" ]] && name="$n"
  v="$(rg -oN 'requires-python\s*=\s*"([^"]+)"' -r '$1' pyproject.toml | head -1 || true)"
  [[ -n "$v" ]] && pyver="\"$v\""
fi
layout="flat"
if [[ -d src ]]; then layout="src";
elif compgen -G "*/__init__.py" >/dev/null; then layout="packages";
fi

cat >"$out_file" <<EOF
{
  "version": "1.0",
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project": {
    "name": "$name",
    "type": "$ptype",
    "python_version": $pyver,
    "src_layout": "$layout"
  },
  "structure": { "src_dirs": [], "test_dirs": [], "config_files": [], "entry_points": [] },
  "patterns": { "config_py_path": null, "constants_locations": [], "scattered_constants": [] },
  "testing": { "framework": null, "fixtures_in": [] },
  "linting": { "tool": null, "type_checker": null }
}
EOF

echo "wrote $out_file - review and fill null/empty fields per python/recon SKILL.md"
