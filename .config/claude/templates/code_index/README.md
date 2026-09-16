# Semantic Code Index

A ChromaDB-powered semantic search index for finding methods, classes, and functions in this repository.

## Setup

```bash
# Install ChromaDB (required)
pip install chromadb

# Build the index
python3 .claude/code_index/build_index.py
```

## Usage

```bash
cd .claude/code_index

# Semantic search
python3 query.py search "fetch user data"
python3 query.py search "async http request" --type method
python3 query.py search "validate input" --code  # show source

# List entities
python3 query.py list-classes
python3 query.py list-methods                    # all methods
python3 query.py list-methods UserService        # methods of a class
python3 query.py list-functions

# Inspect specific entity
python3 query.py show UserService.fetch
python3 query.py similar fetch_data              # find similar code

# Index stats
python3 query.py stats
```

## Configuration

Edit `index_config.json` to customize:

```json
{
  "source_patterns": ["**/*.py"],
  "exclude_patterns": ["**/test_*.py", "**/__pycache__/**"],
  "collection_name": "code_entities"
}
```

## Rebuild After Code Changes

```bash
python3 .claude/code_index/build_index.py
```

## Before Writing New Code

1. **Search first**: `python3 query.py search "what you need"`
2. **Check similar**: `python3 query.py similar existing_method`
3. **Review class**: `python3 query.py list-methods ClassName`

Goal: Extend existing code rather than duplicating functionality.
