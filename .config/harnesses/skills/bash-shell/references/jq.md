# jq (JSON)

```bash
jq '.key'                            # Extract key
jq -r '.name'                        # Raw output (no quotes)
jq '.items[]'                        # Iterate array
jq '.items[] | select(.active)'      # Filter
jq -s '.'                            # Slurp lines → array
jq --arg v "$var" '.key = $v'        # Inject shell var
echo '{}' | jq '.new = "val"'        # Add field
```
