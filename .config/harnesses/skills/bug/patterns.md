# bug pattern memory

# BAD

try: data = json.loads(resp.read()) info = parse_rate_limit(dict(resp.headers), prefix) # raises ValueError on malformed
values except (OSError, json.JSONDecodeError): # int("abc") escapes; fetcher crashes ...

# GOOD

except (OSError, ValueError): # ValueError covers JSONDecodeError AND int() parse failures

Rule: fetch + json + int() → catch (OSError, ValueError). ValueError subsumes JSONDecodeError.

# BAD

normalized = re.sub(r"[-_.]+", "-", name).lower() normalized = re.sub(r"[-_.]+", "-", name).lower() # duplicated line

# GOOD

normalized = re.sub(r"[-_.]+", "-", name).lower() # once

Rule: check verbatim duplicated consecutive assignments — lint misses same-value re-assignment.

# BAD (new write path bypasses the module's own writer and drops its preconditions)

# spool.write_cache() did cdir.mkdir(parents=True, exist_ok=True); the ported

# streaming path wrote pq.ParquetWriter(cdir / key) directly -> FileNotFoundError

# on any not-yet-existing cache dir.

# GOOD

out_path.parent.mkdir(parents=True, exist_ok=True) # right before the streaming write rows = await
execute_to_parquet(..., out_path, ...)

Rule: new write path must re-establish preconditions (mkdir, tmp+rename) the original writer did.

# BAD (cache key misses a result-affecting parameter baked into SQL text)

key = hash(query_name, domains, da, dz, variant, ips, asn) # but SQL has LIMIT {desired_rows}

# GOOD

key = hash(..., extra=str(desired_rows)) # every result-affecting input keys the cache

Rule: cache key must include formatted literals (LIMIT, dates), not just bound params.

# BAD (access columns without checking they exist)

mask = df["ATTRIB_TYPE"] == "B login" # KeyError if column missing

# GOOD

required = {"ATTRIB_TYPE", "EMAILS"} if not required.issubset(set(df.columns)): return df # or raise with clear message
mask = df["ATTRIB_TYPE"] == "B login"

Rule: verify columns exist before filtering — caller may pass partial DataFrame.

# BAD (fall through with implicit None on unsupported type)

def xpivot(df, ...): if isinstance(df, pd.DataFrame): return pandas_xpivot(...) if isinstance(df, pl.DataFrame): return
polars_xpivot(...) # implicit return None → silent bug

# GOOD

    raise TypeError(f"xpivot expects pandas or polars DataFrame, got {type(df).__name__}")

Rule: type-dispatch must raise on unhandled type — implicit None propagates silently.

# BAD (index empty DataFrame)

step = counts.loc[0, "step"] # KeyError when len(counts) == 0

# GOOD

if len(counts) == 0: return None step = counts.loc[0, "step"]

Rule: guard .loc[0]/.iloc[0] against empty DataFrame.

# BAD (matplotlib savefig not atomic)

plt.savefig(path, dpi=300) # crash mid-write leaves corrupt file

# GOOD

tmp_path = f"{path}.tmp" plt.savefig(tmp_path, dpi=300, bbox_inches="tight", facecolor="white") plt.close()
os.replace(tmp_path, path) # atomic on POSIX

Rule: writes must be atomic — tmp then rename. Applies to charts, parquet, pickle.

# BAD (date parsing without explicit error)

threshold = dt.datetime.strptime(s[:10], "%Y-%m-%d").date() # ValueError escapes

# GOOD

try: threshold = dt.datetime.strptime(s[:10], "%Y-%m-%d").date() except ValueError as e: raise ValueError(f"Cannot parse
threshold '{s}': {e}") from e

Rule: date parsing — catch and re-raise with context (which parameter).

# BAD (shared cursor across async tasks)

cursor = source._cursor # single cursor shared by all parallel tasks tasks = [asyncio.create_task(run_query(cursor, q))
for q in queries]

# GOOD

async def run_query(conn, q): cursor = conn.cursor() # dedicated cursor per query try: ... finally: await
asyncio.to_thread(cursor.close)

Rule: parallel async queries need dedicated cursors — shared cursor corrupts on interleave.
