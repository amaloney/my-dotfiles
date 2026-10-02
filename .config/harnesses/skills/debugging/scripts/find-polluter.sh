#!/usr/bin/env bash
# Bisect test files to find which creates unwanted files/state.
# Usage: find-polluter.sh <pollution_path> <test_glob> [test_command]
# Example: find-polluter.sh '.git' 'src/**/*.test.ts'
# test_command defaults to auto-detect: package.json -> npm test; pytest.ini/pyproject.toml -> pytest

set -o errexit -o nounset -o pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <pollution_path> <test_glob> [test_command]"
  echo "Example: $0 '.git' 'src/**/*.test.ts'"
  exit 1
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"
TEST_CMD="${3:-}"

if [ -z "$TEST_CMD" ]; then
  if [ -f package.json ]; then
    TEST_CMD="npm test --"
  elif [ -f pytest.ini ] || [ -f pyproject.toml ]; then
    TEST_CMD="pytest"
  else
    echo "Cannot auto-detect test command; pass one explicitly." >&2
    exit 1
  fi
fi

echo "Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo "Test command: $TEST_CMD"

# find -path can't match '**/' against zero directory levels; also try with '**/' collapsed
TEST_PATTERN="${TEST_PATTERN#./}"
TEST_FILES=$(find . \( -path "./$TEST_PATTERN" -o -path "./${TEST_PATTERN//\*\*\//}" \) | sort -u)
TOTAL=$(printf '%s\n' "$TEST_FILES" | grep -c . || true)

echo "Found $TOTAL test files"

COUNT=0
for TEST_FILE in $TEST_FILES; do
  COUNT=$((COUNT + 1))

  if [ -e "$POLLUTION_CHECK" ]; then
    echo "Pollution already exists before test $COUNT/$TOTAL; skipping: $TEST_FILE"
    continue
  fi

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"
  $TEST_CMD "$TEST_FILE" > /dev/null 2>&1 || true

  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "FOUND POLLUTER"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    ls -la "$POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  $TEST_CMD $TEST_FILE    # Run just this test"
    exit 1
  fi
done

echo "No polluter found - all tests clean!"
exit 0
