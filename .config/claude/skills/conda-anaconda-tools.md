---
name: conda-anaconda-tools
description: Anaconda enterprise tooling - auth, client, audit, linter, menuinst, constructor
invocation: auto
---

# Anaconda Enterprise Tools

## anaconda-auth (Login/Tokens)

| Variable                                | Description                      |
| --------------------------------------- | -------------------------------- |
| `ANACONDA_AUTH_API_KEY`                 | API key (overrides all auth)     |
| `ANACONDA_AUTH_DOMAIN`                  | Domain (default: anaconda.com)   |
| `ANACONDA_AUTH_PREFERRED_TOKEN_STORAGE` | `system` or `anaconda-keyring`   |
| `ANACONDA_AUTH_SSL_VERIFY`              | `true`/`false` or CA bundle path |
| `ANACONDA_AUTH_USE_DEVICE_FLOW`         | Device flow login (no browser)   |

```bash
anaconda login                    # Browser login
anaconda logout
anaconda whoami --at anaconda.com # REQUIRED --at flag in scripts (no --json flag!)
```

## anaconda-client (Upload/Packages)

| Variable             | Description         |
| -------------------- | ------------------- |
| `ANACONDA_API_TOKEN` | API token for auth  |
| `BINSTAR_API_TOKEN`  | Legacy (deprecated) |

```bash
anaconda upload pkg.tar.bz2
anaconda search pandas
```

## anaconda-anon-usage (Telemetry)

| Variable                    | Values             | Description         |
| --------------------------- | ------------------ | ------------------- |
| `CONDA_ANACONDA_HEARTBEAT`  | `true`/`false`/URL | Heartbeat telemetry |
| `CONDA_ANACONDA_ANON_USAGE` | `true`/`false`     | Anonymous usage     |
| `ANACONDA_ANON_USAGE_DEBUG` | (presence)         | Debug output        |

**Suppress heartbeat during activation (before login):**

```batch
SET "CONDA_ANACONDA_HEARTBEAT=false"
```

## anaconda-audit (CVE Scanning)

```bash
anaconda audit scan                    # Current env
anaconda audit scan --name myenv       # Specific env
anaconda audit scan --json             # JSON output
ANACONDA_AUDIT_API_SITE='site' anaconda audit scan  # Use PSM
```

## conda-repo-cli (PSM)

```bash
conda repo login / logout / whoami
conda repo channel list
conda repo search <pkg>
conda repo upload <file>
conda repo cves
```

Config: `~/.anaconda/config.toml`:

```toml
default_site = "self-hosted"
[sites."self-hosted"]
domain = "psm.company.com"
```

## anaconda-linter (Recipe Validation)

```bash
cd ~/recipes/aggregate/                # Need conda_build_config.yaml
conda-lint -v ../feedstock-name        # Lint recipe
conda-lint --severity ERROR path/      # Only errors
conda-lint -f path/                    # Auto-fix
```

Skip lints in meta.yaml:

```yaml
extra:
  skip-lints: [unknown_selector, invalid_url]
```

## menuinst (Shortcuts)

```python
import menuinst
menuinst.install(r'C:\path\menu.json', prefix=r'C:\Anaconda')
menuinst.install(r'C:\path\menu.json', prefix=r'C:\Anaconda', remove=True)
```

Template vars: `{{ PREFIX }}` `{{ MENU_DIR }}` `{{ PYTHON }}` `{{ BIN_DIR }}`

## constructor (Installer Building)

**extra_files timing gotcha:** Files can be overwritten by package post-link scripts.

```yaml
# construct.yaml - copy to PREFIX root, NOT final location
extra_files:
  - prompt-menu.json: prompt-menu.json # NOT Menu/anaconda_prompt_menu.json
```

```batch
REM post-install.bat - copy AFTER packages installed
IF EXIST "%PREFIX%\prompt-menu.json" (
    COPY /Y "%PREFIX%\prompt-menu.json" "%PREFIX%\Menu\anaconda_prompt_menu.json" >NUL 2>&1
)
```

## Environment Logging

| Variable                  | Values                                      | Description     |
| ------------------------- | ------------------------------------------- | --------------- |
| `ANACONDA_ENV_LOG_ACTION` | `none`/`print`/`local-dir`/`anaconda.cloud` | Log destination |
| `ANACONDA_ENV_LOG_DIR`    | path                                        | Local log dir   |

```bash
conda env-log compliance --name myenv --json  # Check policy
```

## Cloud Storage (FSSpec)

```python
import pandas as pd
df = pd.read_csv('anaconda://owner/project/data.csv')
```

URI: `anaconda://<owner>/<project>[#checkpoint]/path[#revision]`
