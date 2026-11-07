#!/usr/bin/env bash
set -euo pipefail

find_templates_dir() {
    local candidates=(
        "$HOME/.config/harnesses/conda"
        "${XDG_CONFIG_HOME:-$HOME/.config}/harnesses/conda"
    )
    for dir in "${candidates[@]}"; do
        if [[ -f "$dir/.envrc" && -f "$dir/Makefile" ]]; then
            echo "$dir"
            return 0
        fi
    done
    return 1
}

TEMPLATES_DIR="${TEMPLATES_DIR:-$(find_templates_dir || echo "")}"

usage() {
    cat << 'EOF'
Usage: conda-project-init.sh [name] [options]

Scaffold a conda project with src-layout, direnv, and conda integration.
Runs IN THE CURRENT DIRECTORY (in-place).

Arguments:
  [name]              Package name (default: current directory name, with hyphens → underscores)

Options:
  --kilo-isolated     Enable kilo-only XDG isolation
  --full-xdg          Enable full XDG isolation (all apps)
  -h, --help          Show this help

Creates (in current directory):
  .envrc              # direnv config (auto-activates .conda/dev)
  .condarc            # project-local conda config
  .gitignore          # standard ignores
  Makefile            # make env, make lock, make clean
  environment.yaml    # conda environment spec
  pyproject.toml      # project metadata, ruff, pytest config
  README.md           # project readme
  src/<name>/         # src-layout package
  tests/              # test directory

After creation:
  1. direnv allow     # auto-activates on cd
  2. Edit environment.yaml and pyproject.toml (replace TODO placeholders)
  3. make lock && make env
EOF
    exit 1
}

# Parse arguments
name=""
kilo_isolated=false
full_xdg=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --kilo-isolated) kilo_isolated=true ;;
        --full-xdg) full_xdg=true ;;
        -h|--help) usage ;;
        -*)  echo "Unknown option: $1"; usage ;;
        *)
            if [[ -z "$name" ]]; then
                name="$1"
            else
                echo "Unknown argument: $1"; usage
            fi
            ;;
    esac
    shift
done

# Default name: current directory name with hyphens converted to underscores
if [[ -z "$name" ]]; then
    dir_name=$(basename "$PWD")
    name="${dir_name//-/_}"
fi

# Validate name (must be valid Python package name)
if ! [[ "$name" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "Error: Package name '$name' is not a valid Python package name" >&2
    echo "       (must be lowercase, start with letter, only letters/numbers/underscores)" >&2
    exit 1
fi

if [[ -z "$TEMPLATES_DIR" ]] || [[ ! -d "$TEMPLATES_DIR" ]]; then
    echo "Error: Templates directory not found" >&2
    echo "       Expected at: ~/.config/harnesses/conda/" >&2
    echo "       Run install.sh to set up symlinks" >&2
    exit 1
fi

# Check if already scaffolded
if [[ -f "pyproject.toml" ]]; then
    echo "Error: pyproject.toml already exists in current directory" >&2
    exit 1
fi

# Copy templates (in-place, current directory)
cp "$TEMPLATES_DIR/.envrc" .
cp "$TEMPLATES_DIR/.condarc" .
cp "$TEMPLATES_DIR/Makefile" .
cp "$TEMPLATES_DIR/environment.yaml" .
cp "$TEMPLATES_DIR/pyproject.toml" .
cp "$TEMPLATES_DIR/.gitignore.template" .gitignore

# Create .conda/.gitignore to self-manage
mkdir -p .conda
echo '**/*' > .conda/.gitignore

# Replace PROJECT_NAME placeholder with actual name
sed -i '' "s/PROJECT_NAME/$name/g" environment.yaml pyproject.toml

# Create src-layout structure
mkdir -p "src/$name"
cat > "src/$name/__init__.py" << EOF
"""$name package."""

__version__ = "0.1.0"
EOF

# Create tests directory
mkdir -p tests

cat > "tests/test_version.py" << EOF
"""Test package version."""

from $name import __version__


def test_version() -> None:
    assert __version__ == "0.1.0"
EOF

# Create README
cat > "README.md" << EOF
# $name

TODO: Add project description.

## Setup

\`\`\`bash
direnv allow   # auto-activates .conda/dev

# Or manually:
make env
\`\`\`

## Development

\`\`\`bash
# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Update environment
make lock
\`\`\`
EOF

# Apply XDG isolation if requested
if $full_xdg; then
    sed -i '' 's/^#export XDG_CONFIG_HOME/export XDG_CONFIG_HOME/' .envrc
    sed -i '' 's/^#export XDG_DATA_HOME/export XDG_DATA_HOME/' .envrc
    sed -i '' 's/^#export XDG_STATE_HOME/export XDG_STATE_HOME/' .envrc
    sed -i '' 's/^#export XDG_CACHE_HOME/export XDG_CACHE_HOME/' .envrc
    sed -i '' 's/^#mkdir -p "\$XDG_CONFIG_HOME/mkdir -p "$XDG_CONFIG_HOME/' .envrc
elif $kilo_isolated; then
    sed -i '' 's/^#export KILO_CONFIG_DIR/export KILO_CONFIG_DIR/' .envrc
    sed -i '' 's/^#mkdir -p "\$KILO_CONFIG_DIR/mkdir -p "$KILO_CONFIG_DIR/' .envrc
fi

# Initialize git if not already a repo
if [[ ! -d ".git" ]]; then
    git init --quiet
fi

# Allow direnv if available
if command -v direnv >/dev/null 2>&1; then
    direnv allow
fi

echo "Created conda project: $name"
echo ""
echo "Next steps:"
echo "  direnv allow   # if not already allowed"
echo "  # Edit environment.yaml and pyproject.toml (replace TODO placeholders)"
echo "  make lock && make env"
