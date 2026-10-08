# External Integrations

**Analysis Date:** 2026-10-08

## APIs & External Services

**ML/Dataset Registries:**
- Hugging Face Hub - CrowdHuman pedestrian dataset (`sshao0516/CrowdHuman`), the only data source the code actually fetches.
  - SDK/Client (primary): `huggingface_hub.snapshot_download(repo_id='sshao0516/CrowdHuman', repo_type='dataset', allow_patterns=['*.zip','*.odgt'])` in `treinar_crowdhuman.py:63-67`
  - SDK/Client (alternate): raw HTTP streaming via `requests.get(..., stream=True)` in `scripts/download_and_convert_crowdhuman.py:51`; base URL `https://huggingface.co/datasets/sshao0516/CrowdHuman/resolve/main` (`scripts/download_and_convert_crowdhuman.py:16`)
  - Auth: none - public dataset, no HF token used anywhere (no token/env var references in the repo)
  - Files fetched: `annotation_train.odgt`, `annotation_val.odgt`, `CrowdHuman_val.zip`, `CrowdHuman_train01-03.zip` (`scripts/download_and_convert_crowdhuman.py:18-25`)
  - Cache: `dataset/downloads_cache/` (`scripts/download_and_convert_crowdhuman.py:14`); HF's own cache is reused by `snapshot_download`
  - Note: TLS verification is disabled for this integration - `verify=False` on `requests.head`/`requests.get` (`scripts/download_and_convert_crowdhuman.py:36,51`) with `urllib3.disable_warnings()` (`scripts/download_and_convert_crowdhuman.py:10`, `treinar_crowdhuman.py:14`) as a proxy/local-cert workaround.

**Downloads:**
- GitHub Releases (Cloudflare) - fetches `cloudflared-windows-amd64.exe` from `https://github.com/cloudflare/cloudflared/releases/latest/download/...`
  - Client: stdlib `urllib.request.urlretrieve` (`scripts/setup_colab_ssh.py:11`)
  - Auth: none
  - Destination: `~/.ssh/cloudflared.exe` (`scripts/setup_colab_ssh.py:6`)

**Manual/Documented (not automated):**
- crowdhuman.org and Roboflow Universe - alternative manual dataset sources mentioned in `README.md:43`, no code integration.

## Data Storage

**Databases:**
- None - no SQL/NoSQL client, ORM, or connection string anywhere in the codebase.

**File Storage:**
- Local filesystem only - everything is read/written relative to the project directory:
  - `dataset/` (created at runtime): `images/{train,val}`, `labels/{train,val}` - produced by `scripts/download_and_convert_crowdhuman.py:158-166`
  - `dataset/downloads_cache/` - raw zips/odgt (`scripts/download_and_convert_crowdhuman.py:14`)
  - `runs/detect/train_crowdhuman_body/` - Ultralytics checkpoints, `results.csv`, plots (`scripts/train_body.py:40-42`)
  - `runs/detect/val_results/val_body/` - validation output (`scripts/validate_body.py:18`)
  - `resultados/`, `models/` - final weights (`best.pt`, `base_face_weights.pt`, `yolo26n.pt`)
- Google Drive (Colab only) - run artifacts saved to `/content/drive/MyDrive/yolo_crowdhuman_treinamento/runs` when mounted, else `/content/runs` (`treinar_crowdhuman_colab.ipynb`)

**Caching:**
- None (no Redis/Memcached). Only filesystem-level download caching as above.

## Authentication & Identity

**Auth Provider:**
- None - no users, no login, no sessions, no tokens. Every external call is anonymous/public.

**OAuth Integrations:**
- None

**SSH Access (remote training box):**
- `scripts/setup_colab_ssh.py` configures outbound SSH from Windows to Colab over a Cloudflare Tunnel: appends a `Host *.trycloudflare.com` block with `ProxyCommand cloudflared access ssh --hostname %h` to `~/.ssh/config` (`scripts/setup_colab_ssh.py:18-24`), `User root`, `Port 22`.
  - Credentials: whatever SSH key already exists in `~/.ssh/` (none generated/managed by this repo).

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Datadog/etc.)

**Analytics:**
- None

**Logs:**
- stdout only - `print(...)` with `[OK]`/`[Aviso]`/`[STATUS]` prefixes, `flush=True` in `treinar_crowdhuman.py`
- Ultralytics writes its own training metrics to `runs/detect/train_crowdhuman_body/results.csv` and plot JPGs (`runs/detect/train_crowdhuman_body/*.jpg`)

## CI/CD & Deployment

**Hosting:**
- None - no Dockerfile, no cloud deployment config.
- Google Colab - interactive GPU training via `treinar_crowdhuman_colab.ipynb`; runtime detection via `'google.colab' in sys.modules or os.path.exists('/content')`

**CI Pipeline:**
- Not detected - no `.github/workflows/`, no pre-commit, no test runner. (Repo has a `.git/` directory but all files are currently untracked.)

## Environment Configuration

**Required env vars:**
- None. The project reads no environment variables.

**Secrets location:**
- None present - no `.env*`, no credential files, no API keys referenced in code (grep for `api_key|token|secret` only matches Colab runtime detection).

**Environment-specific differences:**
- Local Windows: full pipeline (`run_pipeline.py`), webcam inference (`main.py`)
- Colab: same training logic in `treinar_crowdhuman_colab.ipynb` with Drive persistence and `!pip install -q ultralytics huggingface_hub pillow`
- Staging/Production: not applicable

**Portability caveat:**
- `data.yaml:1` and `runs/detect/train_crowdhuman_body/args.yaml:3-4,15,116` embed absolute paths from a different machine (`C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\...`). Only `treinar_crowdhuman.py:118-122` rewrites `data.yaml` before training; `scripts/train_body.py`/`scripts/validate_body.py` consume it unchanged.

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-10-08*
*Update when adding/removing external services*
