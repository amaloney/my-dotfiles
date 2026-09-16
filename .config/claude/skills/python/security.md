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

## Secrets

```python
# Bad
API_KEY = os.getenv("KEY", "default-key")

# Good - fail if missing
API_KEY = os.environ["KEY"]

# Good - explicit check
API_KEY = os.getenv("KEY")
if not API_KEY:
    raise RuntimeError("KEY required")
```

## Crypto

```python
# Bad
hashlib.md5(password.encode()).hexdigest()

# Good
import secrets
from hashlib import pbkdf2_hmac

salt = secrets.token_bytes(16)
hash = pbkdf2_hmac('sha256', password.encode(), salt, 100000)
```

[[python/bugs]] [[python/testing]] [[python/violations]]
