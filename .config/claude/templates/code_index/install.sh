#!/usr/bin/env bash
# Install the semantic code index to a project's .claude folder
#
# Usage:
#   ~/.config/claude/code_index_template/install.sh [TARGET_DIR]
#
# If TARGET_DIR is omitted, installs to current directory's .claude/code_index

set -o errexit -o nounset -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"
DEST="${TARGET_DIR}/.claude/code_index"

if [[ -d "$DEST" ]]; then
    echo "Error: $DEST already exists"
    echo "Remove it first if you want to reinstall"
    exit 1
fi

mkdir -p "$DEST"

cp "$SCRIPT_DIR/build_index.py" "$DEST/"
cp "$SCRIPT_DIR/query.py" "$DEST/"
cp "$SCRIPT_DIR/index_config.json" "$DEST/"
cp "$SCRIPT_DIR/README.md" "$DEST/"

chmod +x "$DEST/build_index.py"
chmod +x "$DEST/query.py"

echo "Installed semantic code index to: $DEST"
echo ""
echo "Next steps:"
echo "  1. Edit $DEST/index_config.json to customize patterns"
echo "  2. pip install chromadb"
echo "  3. python3 $DEST/build_index.py"
echo ""
echo "Add to .gitignore:"
echo "  .claude/code_index/chroma_db/"
