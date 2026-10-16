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

# BAD (access columns without checking they exist)
mask = df["ATTRIB_TYPE"] == "B login"  # KeyError if column missing
# GOOD
required = {"ATTRIB_TYPE", "EMAILS"}
if not required.issubset(set(df.columns)):
    return df  # or raise with clear message
mask = df["ATTRIB_TYPE"] == "B login"

Rule: before filtering/selecting on specific columns, verify they exist. Especially in
functions that accept arbitrary DataFrames — the caller may pass partial data.

# BAD (fall through with implicit None on unsupported type)
def xpivot(df, ...):
    if isinstance(df, pd.DataFrame):
        return pandas_xpivot(...)
    if isinstance(df, pl.DataFrame):
        return polars_xpivot(...)
    # implicit return None → silent bug
# GOOD
    raise TypeError(f"xpivot expects pandas or polars DataFrame, got {type(df).__name__}")

Rule: type-dispatch functions must have an explicit final branch that raises; implicit None
return propagates silently until it causes an unrelated crash downstream.

# BAD (index empty DataFrame)
step = counts.loc[0, "step"]  # KeyError when len(counts) == 0
# GOOD
if len(counts) == 0:
    return None
step = counts.loc[0, "step"]

Rule: before .loc[0] or .iloc[0], guard against empty DataFrame. Even if the query
"should" return rows, defensive code handles the degenerate case.

# BAD (matplotlib savefig not atomic)
plt.savefig(path, dpi=300)  # crash mid-write leaves corrupt file
# GOOD
tmp_path = f"{path}.tmp"
plt.savefig(tmp_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
os.replace(tmp_path, path)  # atomic on POSIX

Rule: any I/O that writes to a file the caller will later read must be atomic —
write to tmp, then rename. Applies to charts, parquet, pickle, etc.

# BAD (date parsing without explicit error)
threshold = dt.datetime.strptime(s[:10], "%Y-%m-%d").date()  # ValueError escapes
# GOOD
try:
    threshold = dt.datetime.strptime(s[:10], "%Y-%m-%d").date()
except ValueError as e:
    raise ValueError(f"Cannot parse threshold '{s}': {e}") from e

Rule: when parsing user-supplied date strings, catch and re-raise with context.
The raw "time data 'foo' does not match format" is unhelpful without knowing which
parameter was bad.

# BAD (shared cursor across async tasks)
cursor = source._cursor  # single cursor shared by all parallel tasks
tasks = [asyncio.create_task(run_query(cursor, q)) for q in queries]
# GOOD
async def run_query(conn, q):
    cursor = conn.cursor()  # dedicated cursor per query
    try:
        ...
    finally:
        await asyncio.to_thread(cursor.close)

Rule: database cursors are stateful. When running parallel async queries, each task
must have its own cursor; sharing one corrupts results when fetch operations interleave.
Wrap cursor lifetime in try/finally to close on all exit paths.
