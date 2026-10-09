#!/usr/bin/env bash
# =============================================================================
# profile.sh - Rust project recon; emit .harness/code_index/profile.json
#
# Usage: run from the repo (or workspace) root
#   ~/.config/harnesses/skills/rust/recon/scripts/profile.sh
#
# Reads `cargo metadata --no-deps`, writes the profile.json skeleton populating
# cheaply-detectable fields (name, type, edition, rust_version, toolchain,
# workspace members, targets, features). Other fields stay null/empty for
# agent review. Re-run to overwrite.
# =============================================================================
set -o errexit -o nounset -o pipefail

for tool in cargo jq; do
  command -v "$tool" >/dev/null || { echo "error: $tool required" >&2; exit 1; }
done
[[ -f Cargo.toml ]] || { echo "error: no Cargo.toml in $PWD" >&2; exit 1; }

out_dir=".harness/code_index"
out_file="$out_dir/profile.json"
mkdir -p "$out_dir"

metadata="$(cargo metadata --format-version 1 --no-deps)"

# rust-toolchain.toml channel (or legacy rust-toolchain file), else null
toolchain="null"
if [[ -f rust-toolchain.toml ]]; then
  channel="$(sed -nE 's/^[[:space:]]*channel[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' rust-toolchain.toml | head -1)"
  [[ -n "$channel" ]] && toolchain="\"$channel\""
elif [[ -f rust-toolchain ]]; then
  toolchain="\"$(head -1 rust-toolchain)\""
fi

jq \
  --arg generated "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg dirname "$(basename "$PWD")" \
  --argjson toolchain "$toolchain" \
  '
  def kinds: [.packages[].targets[].kind[]] | unique;
  def deps: [.packages[].dependencies[].name] | unique;
  (.packages | length) as $member_count
  | (if $member_count == 1 then .packages[0].name else $dirname end) as $name
  | (kinds) as $kinds
  | (deps) as $deps
  | {
      version: "1.0",
      language: "rust",
      generated: $generated,
      project: {
        name: $name,
        type: (
          if $member_count > 1 then "workspace"
          elif ($kinds | index("proc-macro")) then "proc-macro"
          elif ($deps | any(. == "axum" or . == "actix-web" or . == "rocket" or . == "warp")) then "webapp"
          elif ($deps | any(. == "clap" or . == "argh")) or (($kinds | index("bin")) and ($kinds | index("lib") | not))
            then "cli"
          else "library" end
        ),
        edition: ([.packages[].edition] | unique | if length == 1 then .[0] else join(",") end),
        rust_version: ([.packages[].rust_version // empty] | unique | first // null),
        toolchain: $toolchain,
        workspace_members: [.packages[] | {name, manifest_path: (.manifest_path | ltrimstr($ENV.PWD + "/"))}],
        targets: [.packages[] | .name as $pkg | .targets[] | {package: $pkg, name, kind: .kind[0]}],
        features: [.packages[] | {package: .name, features: (.features | keys)}]
      },
      structure: { src_dirs: [], test_dirs: [], bench_dirs: [], example_dirs: [], entry_points: [] },
      patterns: { config_rs_path: null, constants_locations: [], scattered_constants: [], error_crate: null },
      testing: { runner: null, frameworks: [], property: null },
      linting: { clippy_config: null, rustfmt_config: null, lints_table: null }
    }
  ' <<<"$metadata" >"$out_file"

echo "wrote $out_file - review and fill null/empty fields per rust/recon SKILL.md"
