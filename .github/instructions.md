Here’s a clear brief you can paste into Copilot. It tells it what to build, how to structure the repo, and includes a GitHub Actions pipeline to publish to PyPI.

---

## Goal

Create a Python package **`itl-k8s-oidc`** that automates developer setup for **Kubernetes OIDC auth via Keycloak** (realm **`itlusions`**), using **kubectl krew** and the **`oidc-login`** plugin. Provide a CLI: `itl-oidc-setup`.

## Key features

* Checks for `kubectl`; auto-installs **krew** (latest) if missing.
* Installs **`oidc-login`** plugin via krew.
* Runs:

  ```
  kubectl oidc-login setup \
    --oidc-issuer-url=<resolved> \
    --oidc-client-id=kubelogin \
    --oidc-extra-scope=openid,profile,email
  ```
* **Issuer resolution precedence:** CLI `--issuer-url` > env `ITL_OIDC_ISSUER_URL` > `~/.config/itl-k8s-oidc/config.json` > baked default.
* **Baked default issuer:** `https://sso.example.com/realms/itlusions` (replaceable later).
* Public OIDC client (PKCE); options: `--device-code`, `--kubeconfig`, `--ca-file`, `--verify`, `--dry-run`, `--save-default`.

## Acceptance criteria

* `pip install .` installs `itl-oidc-setup` console script.
* `itl-oidc-setup --verify` succeeds on hosts with working Keycloak issuer.
* Works on Linux/macOS/Windows (PowerShell).
* Clean error messages; non-zero exit codes on failure.
* README documents usage and overrides.
* CI: build wheels/sdist; publish to **PyPI** on tag.

## Repo scaffold (create these files)

```
.
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ src/itl_k8s_oidc/
│  ├─ __init__.py
│  ├─ defaults.py         # DEFAULT_ISSUER_URL, DEFAULT_CLIENT_ID, DEFAULT_SCOPES
│  ├─ config.py           # load/save ~/.config/itl-k8s-oidc/config.json (or %APPDATA%)
│  ├─ utils.py            # subprocess helpers, OS/arch detect, download/install krew, discovery fetch
│  ├─ krew.py             # ensure krew + plugin
│  ├─ kubelogin.py        # discovery validation, run setup, optional whoami verify
│  └─ cli.py              # argparse, precedence, --save-default
└─ .github/workflows/
   ├─ build.yml
   └─ publish.yml
```

### `pyproject.toml` (hatchling)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "itl-k8s-oidc"
version = "0.1.0"
description = "One-command setup: Kubernetes OIDC via Keycloak + kubelogin (auto-installs krew + oidc-login)."
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [{name="ITlusions", email="noreply@example.com"}]
keywords = ["kubernetes","oidc","keycloak","kubelogin","krew"]
classifiers = [
  "Programming Language :: Python :: 3",
  "Environment :: Console",
  "Operating System :: OS Independent",
  "License :: OSI Approved :: MIT License",
]

[project.scripts]
itl-oidc-setup = "itl_k8s_oidc.cli:main"
```

### `src/itl_k8s_oidc/defaults.py`

```py
DEFAULT_ISSUER_URL = "https://sso.example.com/realms/itlusions"
DEFAULT_CLIENT_ID = "kubelogin"
DEFAULT_SCOPES = "openid,profile,email"
```

### `src/itl_k8s_oidc/config.py`

* Read/write `~/.config/itl-k8s-oidc/config.json` (Linux/macOS) or `%APPDATA%\itl-k8s-oidc\config.json` (Windows) with keys: `issuer_url`, `client_id`, `scopes`.

### `src/itl_k8s_oidc/utils.py`

* `ensure_kubectl_available()`
* OS/arch detect; download **krew** tarball from latest GitHub release; install.
* `ensure_plugin("oidc-login")`
* Fetch OIDC discovery doc and validate `issuer`.
* Run subprocess with robust error reporting.

### `src/itl_k8s_oidc/krew.py`

* `install_krew_and_plugin(env, auto_install_krew=True)`

### `src/itl_k8s_oidc/kubelogin.py`

* `setup_kubelogin(issuer_url, client_id, scopes, kubeconfig=None, ca_file=None, device_code=False, extra_args=None, env=None, dry_run=False, verify=False)`
* If `verify=True`, call `kubectl auth whoami` and return output.

### `src/itl_k8s_oidc/cli.py`

* argparse flags:

  * `--issuer-url` (optional; overrides)
  * `--client-id` (default: `kubelogin`)
  * `--scopes` (default: `openid,profile,email`)
  * `--kubeconfig`, `--ca-file`, `--device-code`, `--verify`, `--dry-run`
  * `--no-install-krew`, `--no-install-plugin`
  * `--extra-arg` (repeatable passthrough)
  * `--save-default` (persist to config file)
* Resolution order for issuer: CLI > env `ITL_OIDC_ISSUER_URL` > config file > baked default.

### `README.md`

* What it does, how it works, examples:

  * Minimal: `itl-oidc-setup --verify`
  * Override: `export ITL_OIDC_ISSUER_URL=...`
  * Persist: `itl-oidc-setup --issuer-url https://sso.itlusions.com/realms/itlusions --save-default`
* Notes on public client + PKCE, device-code mode, custom CA.

### `LICENSE`

* MIT.

---

## CI: GitHub Actions

### Build on PRs (lint & build)

`.github/workflows/build.yml`

```yaml
name: build
on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/*
```

### Publish to PyPI on tag

`.github/workflows/publish.yml`

```yaml
name: publish
on:
  push:
    tags:
      - "v*.*.*"

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # for trusted publishing (recommended)
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip build
      - run: python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@v1.10.3
        with:
          skip-existing: true
          print-hash: true
          # If not using OIDC Trusted Publishing, uncomment and set PYPI_API_TOKEN in repo secrets:
          # password: ${{ secrets.PYPI_API_TOKEN }}
```

> Configure **PyPI Trusted Publishing** or add a repo secret **`PYPI_API_TOKEN`** (from PyPI). Tag releases like `v0.1.0` to trigger publishing.

---

## Final step

Open a PR creating all files above with working code and pipeline. Ensure the baked default issuer is present and overridable. After merge, create a tag `v0.1.0` to publish to PyPI.
