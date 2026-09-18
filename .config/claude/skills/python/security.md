---
name: python/security
description: Python security patterns - insecure defaults, sharp edges, common vulns
invocation: auto
---

# Python Security

## Insecure Defaults

| Category          | Pattern                              | Fix                               |
| ----------------- | ------------------------------------ | --------------------------------- |
| Fallback secrets  | `env.get('KEY') or 'dev'`            | Fail if missing: `env['KEY']`     |
| Default creds     | `password='admin123'`                | No defaults for secrets           |
| Fail-open         | `getenv('AUTH', 'false')`            | Default to secure: `'true'`       |
| Weak crypto       | `hashlib.md5(password)`              | `hashlib.pbkdf2_hmac` or `bcrypt` |
| Permissive access | `ACL='public-read'`, mode `0o666`    | Explicit restrictive perms        |
| Debug leakage     | `traceback.format_exc()` in response | Generic error messages in prod    |

## Sharp Edges

| Category            | Bad                                   | Good                             |
| ------------------- | ------------------------------------- | -------------------------------- |
| Algorithm selection | `jwt.decode(t, options={"verify":F})` | Always verify, no opt-out        |
| Dangerous defaults  | `timeout=0` (infinite)                | Explicit finite timeout          |
| Primitive APIs      | `encrypt(msg, bytes, bytes)`          | Named params: `key=`, `nonce=`   |
| Config cliffs       | `verify_ssl: false`                   | Per-host exceptions only         |
| Silent failures     | `verify()` returns `False`            | Raise exception on failure       |
| Stringly-typed      | `"admin,write,read"`                  | Enum or set of typed permissions |

## Detection

```bash
# Fallback secrets
rg -n "\.get\(['\"].*['\"],\s*['\"]" --type py

# Weak crypto
rg -n "hashlib\.(md5|sha1)\(" --type py

# Debug in responses
rg -n "traceback\.(format_exc|print_exc)" --type py

# Permissive modes
rg -n "chmod|0o[67][67][67]" --type py

# SSL disabled
rg -n "verify\s*=\s*False|CERT_NONE" --type py
```

## Common Vulns

| Vuln               | Pattern                          | Fix                              |
| ------------------ | -------------------------------- | -------------------------------- |
| SQL injection      | `f"SELECT * WHERE id={x}"`       | Parameterized: `(?, x)`          |
| Command injection  | `os.system(f"cmd {user_input}")` | `subprocess.run([...], shell=F)` |
| Path traversal     | `open(base + user_path)`         | `Path(base).joinpath(p).resolve` |
| SSRF               | `requests.get(user_url)`         | Allowlist hosts/schemes          |
| Pickle RCE         | `pickle.loads(user_data)`        | JSON or protobuf                 |
| YAML RCE           | `yaml.load(data)`                | `yaml.safe_load(data)`           |
| Eval/exec          | `eval(user_input)`               | AST parsing or sandboxed eval    |
| Template injection | `render(user_template)`          | Sandboxed templates              |

## Secrets — VULNERABLE vs SECURE

**Report when:** Default value feeds signing, encryption, session, or token machinery.
**Skip when:** Defaults generated per-boot at random, cache keys, correlation ids.

The decisive question: does the app **run** with it? `env.get(X, Y)` runs; `env[X]` crashes.

```python
# VULNERABLE — app runs with known secret, attacker can forge tokens
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
token = jwt.encode({'user': id}, SECRET_KEY, algorithm='HS256')

# SECURE — fails fast if missing
SECRET_KEY = os.environ['SECRET_KEY']  # Raises KeyError

# SECURE — explicit validation
SECRET_KEY = os.getenv("KEY")
if not SECRET_KEY:
    raise RuntimeError("KEY required")
```

## Crypto — VULNERABLE vs SECURE

**Report when:** Broken primitive for password hashing, token generation, encryption.
**Skip when:** Checksums, ETags, cache keys, dedup hashes, test vectors.

The algorithm alone is never the finding. Trace to the use site before flagging.

```python
# VULNERABLE — MD5 for password (rainbow tables exist)
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# SECURE — MD5 for cache key (not security-sensitive)
def cache_key(data):
    return hashlib.md5(data.encode()).hexdigest()

# SECURE — proper password hashing
import bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

[[python/bugs]] [[python/testing]] [[python/violations]]
