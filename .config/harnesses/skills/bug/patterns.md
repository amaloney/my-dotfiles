# bug pattern memory

# BAD
try:
    data = json.loads(resp.read())
    info = parse_rate_limit(dict(resp.headers), prefix)  # raises ValueError on malformed values
except (OSError, json.JSONDecodeError):  # int("abc") escapes; fetcher crashes
    ...
# GOOD
except (OSError, ValueError):  # ValueError covers JSONDecodeError AND int() parse failures

Rule: when a fetch try-block contains both json parsing and any int()/float() conversion of
untrusted wire data, catch (OSError, ValueError) — ValueError subsumes JSONDecodeError, and
malformed-header ValueErrors otherwise escape "always-return" fetcher contracts.

# BAD
normalized = re.sub(r"[-_.]+", "-", name).lower()
normalized = re.sub(r"[-_.]+", "-", name).lower()  # duplicated line
# GOOD
normalized = re.sub(r"[-_.]+", "-", name).lower()  # once

Rule: check for verbatim duplicated consecutive assignments — copy/paste residue that lint
(F811 only flags redefinition of imports/names, not same-value re-assignment) does not catch.

# BAD (new write path bypasses the module's own writer and drops its preconditions)
# spool.write_cache() did cdir.mkdir(parents=True, exist_ok=True); the ported
# streaming path wrote pq.ParquetWriter(cdir / key) directly -> FileNotFoundError
# on any not-yet-existing cache dir.
# GOOD
out_path.parent.mkdir(parents=True, exist_ok=True)  # right before the streaming write
rows = await execute_to_parquet(..., out_path, ...)

Rule: when a port adds a second write path to a destination the original writer used to
prepare (mkdir, tmp+rename, fsync), the new path must re-establish those preconditions.
Grep for every writer of the same directory, not just the canonical one.

# BAD (cache key misses a result-affecting parameter baked into SQL text)
key = hash(query_name, domains, da, dz, variant, ips, asn)   # but SQL has LIMIT {desired_rows}
# GOOD
key = hash(..., extra=str(desired_rows))  # every result-affecting input keys the cache

Rule: when SQL text is built with formatted literals (LIMIT, dates) alongside qmark params,
audit the cache key against BOTH the bound params and the formatted literals — key-only-what's-
bound silently returns stale results when a formatted literal changes.
