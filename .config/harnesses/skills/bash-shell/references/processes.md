# Processes: xargs/parallel, Signals

## xargs/parallel

```bash
find . -name "*.log" | xargs rm -f             # Batch delete
find . -name "*.sh" -print0 | xargs -0 chmod +x  # Null-delimited (spaces safe)
cat urls.txt | xargs -P4 -I{} curl -sO {}      # Parallel downloads
seq 10 | xargs -P4 -I{} bash -c 'process {}'   # Parallel jobs
```

## Process/Signals

```bash
trap 'rm -f "$tmpfile"; exit' EXIT INT TERM    # Cleanup on exit/ctrl-c
cmd & pid=$!; wait $pid                        # Background + wait
kill -0 $pid 2>/dev/null && echo "running"     # Check if alive
timeout 30 long_cmd                            # Kill after 30s
nohup cmd > out.log 2>&1 &                     # Detach from terminal
```
