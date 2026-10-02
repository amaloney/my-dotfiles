# Tools

## conda-build CLI

```bash
conda build recipe/ [options]
  --error-overlinking      # fail on overlinking
  --error-overdepending    # fail on overdepending
  -c <channel>             # add channel
  --croot <dir>            # build root
  --output-folder <dir>    # where to put packages
```

## conda-recipe-manager (crm)

```bash
# Bump version
crm bump-recipe -t <new-version> recipe/meta.yaml

# Increment build number only
crm bump-recipe --build-num recipe/meta.yaml

# Convert V0 (meta.yaml) to V1 (recipe.yaml)
crm convert recipe/meta.yaml
```

## Verification

```bash
# View package metadata
conda search <package> -c local -i

# Check linkages (Linux)
conda inspect linkages <package>

# Check imported packages (Python)
conda inspect objects <package>
```
