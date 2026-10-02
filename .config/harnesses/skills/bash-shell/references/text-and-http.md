# Text & HTTP: curl, awk/sed

## curl

```bash
curl -sSfL "$url"                              # Silent, fail on error, follow redirects
curl -X POST -H "Content-Type: application/json" -d '{"k":"v"}' "$url"
curl -o file.zip -w "%{http_code}" "$url"      # Save + print status
curl --retry 3 --retry-delay 2 "$url"          # Retry logic
```

## awk/sed

```bash
awk '{print $2}'                               # 2nd column
awk -F: '{print $1}'                           # Custom delimiter
awk '/pattern/ {print}'                        # Filter lines
sed 's/old/new/g'                              # Replace all
sed -i.bak 's/old/new/g' file                  # In-place with backup
sed -n '10,20p' file                           # Print lines 10-20
```
