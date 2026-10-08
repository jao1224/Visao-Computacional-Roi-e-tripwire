# Coding Conventions

**Analysis Date:** 2026-10-08

## Naming Patterns

**Files:**
- `snake_case.py` for all Python files, but names are **mixed language**: English for pipeline scripts (`run_pipeline.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `scripts/download_and_convert_crowdhuman.py`) and Portuguese for root-level/training scripts (`treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`)
- Rule of thumb: keep existing file names as-is; name **new** files in English `snake_case` when adding to `scripts/`
- Config: `data.yaml` (root) for Ultralytics dataset config
- No test files exist anywhere (see `TESTING.md`)

**Functions:**
- `snake_case` everywhere: `main()`, `download_file()`, `extract_zip()`, `flatten_directory()`, `convert_odgt_to_yolo()`
- Every runnable script exposes a single `main()` entry guarded by `if __name__ == "__main__":` (see `main.py:87`, `run_pipeline.py:22`, `scripts/train_body.py:45`, `scripts/validate_body.py:41`, `treinar_crowdhuman.py:145`)
- Small helpers defined **nested inside `main()`** when only used there (`extract_zip`, `convert_odgt` at `treinar_crowdhuman.py:70,86`) or at module scope when shared (`download_and_convert_crowdhuman.py:27-150`)
- `scripts/setup_colab_ssh.py` is the one script with **no** `main()` — it is pure top-level procedural code

**Variables:**
- `camelCase` for local/path variables: `base_dir`, `weightsPath`-style never used; actual style is `weights_path`, `train_img_dir`, `val_lbl_dir`, `modelo_path`, `downloaded`
- `UPPER_SNAKE_CASE` for module-level constants only: `BASE_DIR`, `DATASET_DIR`, `CACHE_DIR`, `HF_BASE_URL`, `FILES_TO_DOWNLOAD` (`scripts/download_and_convert_crowdhuman.py:12-25`)
- Deviation: `treinar_crowdhuman.py:20-23` uses `UPPER_SNAKE_CASE` for **local** variables inside `main()`; `main.py:7` and `scripts/train_body.py:5` use lowercase `base_dir` for the same value. Prefer lowercase `base_dir`/`root_dir` for locals in new code; keep `UPPER_SNAKE_CASE` for true module constants.
- Portuguese identifiers appear for domain variables: `candidatos`, `modelo_path`, `num_pessoas`, `webcam` (`main.py:11-28`). Match the surrounding file's language.

**Types:**
- Not applicable — codebase is untyped Python (no type annotations anywhere)

## Code Style

**Formatting:**
- No formatter configured (no `black`, `ruff format`, `.prettierrc` equivalent). Match manual style: 4-space indent, ~100-120 char lines
- Quotes are **inconsistent**: single quotes dominant for paths/short strings (`'resultados'`, `'best.pt'`), double quotes in `download_and_convert_crowdhuman.py` f-strings and notebook. Prefer single quotes for new code unless the line contains apostrophes/inner single quotes
- Trailing commas not used; blank line separates numbered steps

**Linting:**
- None configured (no `.flake8`, `.pylintrc`, `ruff`/`black`/`mypy` in any config file; no `requirements.txt`, `pyproject.toml`, or `setup.cfg`)
- If introducing a linter, add `ruff` with a `pyproject.toml` at repo root rather than layering multiple tools

## Import Organization

**Order:**
1. Standard library (`os`, `sys`, `json`, `time`, `zipfile`, `shutil`, `subprocess`, `urllib`)
2. Third-party (`cv2`, `requests`, `urllib3`, `torch`, `PIL.Image`, `huggingface_hub`, `ultralytics`)
3. Local (none — the project has **no local module imports**; scripts never import each other)

**Grouping:**
- One block, stdlib first then third-party, no blank lines between groups (`treinar_crowdhuman.py:1-11`)
- Inline imports occur mid-function when lazily needed: `import shutil` at `treinar_crowdhuman.py:41`; notebook cells import per-cell (`treinar_crowdhuman_colab.ipynb` cells 1, 3, 4). Acceptable in notebooks; put imports at top in `.py` files.

**Path Aliases:**
- None. All paths resolved with `os.path.join` relative to `os.path.dirname(os.path.abspath(__file__))`

## Error Handling

**Patterns:**
- Fail-soft / continue-on-error: broad `try/except Exception` that prints a warning and proceeds (`treinar_crowdhuman.py:115-116`, `download_and_convert_crowdhuman.py:35-39,116-120`, notebook cell 4)
- Guard-clause early returns for fatal conditions with a printed message and `return` — never raised exceptions (`main.py:19-22` missing model, `main.py:29-31` webcam open failure)
- Fallback chains instead of exceptions: candidate-path list resolved with `next((p for p in candidatos if os.path.exists(p)), None)` (`main.py:11-19`) or `if not os.path.exists(...)` fallback to base weights with `[Aviso]` print (`scripts/train_body.py:9-12`, `scripts/validate_body.py:9-13`)
- Subprocess steps use `check=True` so failures abort the pipeline (`run_pipeline.py:13,20`)
- HTTP: `response.raise_for_status()` after `requests.get` (`download_and_convert_crowdhuman.py:52`)
- No custom exception classes; no exceptions re-raised; almost never caught exceptions are logged with context beyond the message string

**Error Types:**
- Fatal (return early): missing model weights, camera failure, subprocess failure
- Recoverable (print `[Aviso]`/`[AVISO]` and continue): missing optional files, download/extract issues, unreadable images (skip row: `except Exception: continue` at `download_and_convert_crowdhuman.py:119-120`)
- Never use exceptions for control flow in data loops — use `continue`

## Logging

**Framework:**
- `print()` only — no `logging` module anywhere

**Patterns:**
- Bracketed status tags as a pseudo-level system: `[OK]` success, `[Aviso]`/`[AVISO]` warning, `[STATUS]` progress, `[GPU ATIVA]` context, `-->` step announcements, `[Erro: ...]` fatal (`main.py:21,30`)
- ASCII banners of `=` chars around major stage headers (`run_pipeline.py:9-11`, `scripts/train_body.py:17-23`, `scripts/validate_body.py:33-39`)
- `flush=True` on every `print` in `treinar_crowdhuman.py` and the Colab notebook (keeps output ordered in Colab/CI logs); other scripts omit it
- Console progress for downloads with `end='\r'` percentage line (`download_and_convert_crowdhuman.py:66`)
- Match tag vocabulary exactly when adding messages: `[OK]`, `[Aviso]`, `-->`, banners for stages

## Comments

**When to Comment:**
- Comments are in **Portuguese (pt-BR)** and mark numbered pipeline stages: `# 1. Hardware Check`, `# 4. Configurar data.yaml` (`treinar_crowdhuman.py:27,118`)
- Rationale comments for non-obvious choices: `# workers=0  # Compatível com Windows`, `# 640px para capturar corpo inteiro...` (`scripts/train_body.py:32,39`)
- One inline English comment slips in (`main.py:57`); prefer Portuguese for consistency
- Avoid restating code; do document *why* a fallback/quirk exists

**Docstrings:**
- One-line Portuguese docstrings only in `scripts/download_and_convert_crowdhuman.py` (`"""Download resiliente com suporte a retomar download e bypass SSL."""` at line 28). Use this style (one-line, Portuguese, imperative) for new helper functions; not enforced elsewhere

**TODO Comments:**
- Not used (no TODO/FIXME/HACK markers in the codebase)

## Function Design

**Size:**
- Tolerance is high: `main()` runs 100+ lines end-to-end (`treinar_crowdhuman.py:16-143`, `main.py:6-85`). Existing convention is one long `main()` per script with numbered comment stages
- Extract helpers only for reusable units (download, zip extraction, annotation conversion) — prefer a top-level `snake_case` function with a one-line docstring

**Parameters:**
- 2-4 positional parameters typical (`convert_odgt_to_yolo(odgt_path, images_dir, labels_output_dir)`); no options-dict/kwargs patterns
- Paths are always explicit parameters or derived from `BASE_DIR` module constants

**Return Values:**
- CLI scripts return `None` and signal failure via printed message + `return`
- Helpers return a status/counter: `bool` for download/extract success (`download_file`, `extract_zip`), `int` count for conversion (`convert_odgt_to_yolo` returns `converted_count`)
- Guard-clause early returns preferred over nested else blocks

## Module Design

**Exports:**
- No packages, no `__init__.py`, no imports between project files — each script is standalone and re-derives paths from `__file__`
- Scripts compose only through `subprocess`: `run_pipeline.py` invokes `scripts/download_and_convert_crowdhuman.py` then `scripts/train_body.py` via `subprocess.run([sys.executable, script], check=True)` (`run_pipeline.py:12-20`). Follow this: cross-script reuse = subprocess, not `import`

**Barrel Files:**
- Not applicable

---

*Convention analysis: 2026-10-08*
*Update when patterns change*
