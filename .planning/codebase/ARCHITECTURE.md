# Architecture

**Analysis Date:** 2026-10-08

## Pattern Overview

**Overall:** Script-based ML Pipeline (flat collection of standalone Python scripts, orchestrated by subprocess)

**Key Characteristics:**
- No package/module structure: every `.py` file is a self-contained executable with its own `main()` and `if __name__ == "__main__"` guard
- Linear 4-stage pipeline: dataset download → annotation conversion → training → validation → real-time inference
- Orchestration via `subprocess.run()` (`run_pipeline.py`), not imports — stages communicate only through the filesystem
- All state lives on disk (dataset folders, YOLO run artifacts, `.pt` weight files); no database, no in-memory shared state
- Duplicate/parallel implementations: a modular path (`scripts/`) and a monolithic path (`treinar_crowdhuman.py` + `treinar_crowdhuman_colab.ipynb`) do the same job
- Paths resolved at runtime relative to `__file__` (`os.path.dirname(os.path.abspath(__file__))`), but `data.yaml` embeds an absolute path from a different machine

## Layers

**Entry/Orchestration Layer:**
- Purpose: User-facing commands that kick off pipeline stages or run inference
- Location: `main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`
- Contains: `main()` functions, model candidate-path resolution, subprocess orchestration, OpenCV webcam loop
- Depends on: `ultralytics.YOLO`, `cv2`, `subprocess`, filesystem layout
- Used by: Human operator via `python <script>`

**Pipeline Stage Layer:**
- Purpose: One script per pipeline stage (download/convert, train, validate, environment setup)
- Location: `scripts/`
- Contains: `scripts/download_and_convert_crowdhuman.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `scripts/setup_colab_ssh.py`
- Depends on: `ultralytics`, `requests`/`urllib3`, `PIL`, `os`/`json`/`zipfile`
- Used by: `run_pipeline.py` (spawns via subprocess) or run directly per `README.md`

**Configuration Layer:**
- Purpose: Declare dataset layout and class ontology for Ultralytics
- Location: `data.yaml` (root), hyperparameters are hard-coded inline in each training script (not externalized)
- Depends on: Absolute `path:` pointing at `dataset/`
- Used by: `scripts/train_body.py`, `scripts/validate_body.py`, `treinar_crowdhuman.py`

**Artifact/State Layer:**
- Purpose: Filesystem locations where each stage reads inputs and writes outputs
- Location: `dataset/` (created at runtime, currently absent), `runs/detect/`, `resultados/`, `models/`
- Contains: YOLO training runs (`runs/detect/train_crowdhuman_body/`), copied weights (`resultados/best.pt`), base weights (`models/base_face_weights.pt`, `yolo26n.pt`)
- Depends on: nothing (pure data)
- Used by: every other layer

**Notebook/Remote Layer:**
- Purpose: Cloud (Colab) variant of the training pipeline for GPU execution
- Location: `treinar_crowdhuman_colab.ipynb`, assisted by `scripts/setup_colab_ssh.py` (cloudflared SSH tunnel config)
- Depends on: `huggingface_hub.snapshot_download`, `torch`, `ultralytics`
- Used by: Manual notebook execution; mirrors `treinar_crowdhuman.py` logic cell-by-cell

## Data Flow

**Training Pipeline (`run_pipeline.py` → `scripts/`):**

1. `run_pipeline.py:12-13` spawns `scripts/download_and_convert_crowdhuman.py`
2. Download stage fetches 6 files from HuggingFace (`annotation_*.odgt`, `CrowdHuman_*.zip`) into `dataset/downloads_cache/` (`scripts/download_and_convert_crowdhuman.py:16-25`)
3. Zips extracted into `dataset/images/{train,val}/`; nested `Images/` folders flattened (`flatten_directory`, line 82)
4. `convert_odgt_to_yolo()` (line 95) reads ODGT JSON-lines, keeps `tag == 'person'` full-body boxes (`fbox`), writes normalized YOLO labels `0 x_center y_center w h` to `dataset/labels/{train,val}/`
5. `run_pipeline.py:19-20` spawns `scripts/train_body.py` → loads `models/base_face_weights.pt` (transfer learning) → `model.train(data=data.yaml, epochs=300, imgsz=640, batch=8, ...)` → writes `runs/detect/train_crowdhuman_body/` including `weights/best.pt`
6. Validation (manual step): `scripts/validate_body.py` loads `runs/detect/train_crowdhuman_body/weights/best.pt`, runs `model.val(split='val')`, prints mAP/P/R/F1 to stdout
7. Inference: `main.py` probes an ordered candidate list of weight paths (lines 11-17), takes the first that exists, runs 5 FPS webcam detection with `conf=0.25, iou=0.60`

**Alternative Monolithic Flow (`treinar_crowdhuman.py`):**

1. GPU check via `torch.cuda` (line 28)
2. Seed weights: `models/base_face_weights.pt`, falling back to `../runs/detect/train-14/weights/best.pt` (copied in) or `'yolo26n.pt'` (lines 37-45)
3. `snapshot_download(repo_id='sshao0516/CrowdHuman')` then inline (duplicated) extract/flatten/convert logic (lines 63-116)
4. **Rewrites `data.yaml`** with the local absolute dataset path (lines 119-122)
5. Batch size auto-selected 8 vs 32 by VRAM (line 125); trains to `runs/detect/train_crowdhuman_body`

**State Management:**
- Purely filesystem-based; each script is stateless between runs
- Idempotency is ad-hoc: download stage skips files whose local size matches `content-length`; `exist_ok=True` overwrites the same run directory
- `dataset/` and `runs/.../weights/` are currently absent in this checkout — scripts recreate them on first run

## Key Abstractions

**Model Candidate Resolution:**
- Purpose: Find a usable `.pt` weight without hard failure
- Examples: `main.py:11-19` (5-path priority list), `scripts/train_body.py:8-12`, `scripts/validate_body.py:8-13`
- Pattern: first-match-wins `next((p for p in candidatos if os.path.exists(p)), None)` with console warning fallback to base `yolo26n.pt`

**ODGT → YOLO Converter:**
- Purpose: Transform CrowdHuman JSON-lines annotations into YOLO normalized `.txt` labels
- Examples: `convert_odgt_to_yolo()` in `scripts/download_and_convert_crowdhuman.py:95-150`; duplicated inline as `convert_odgt()` in `treinar_crowdhuman.py:86-109`
- Pattern: standalone function over plain files; two divergent copies (no shared module)

**YOLO Training Harness:**
- Purpose: Configure and launch Ultralytics training
- Examples: `scripts/train_body.py:29-43`, `treinar_crowdhuman.py:128-142`
- Pattern: direct call to `ultralytics.YOLO.train()` with hyperparameters inline (no config file, no CLI args)

**Pipeline Orchestrator:**
- Purpose: Chain stages as subprocesses
- Examples: `run_pipeline.py:12-20`
- Pattern: `subprocess.run([sys.executable, script], check=True)` — failure of stage 1 aborts stage 2 via `CalledProcessError`

**Weight Artifact Copy:**
- Purpose: Promote a trained run to a stable path
- Examples: `resultados/best.pt` (manual copy of a run's `best.pt`), `models/base_face_weights.pt` (isolated copy of face weights so training never mutates the original)
- Pattern: plain file duplication; no versioning metadata

## Entry Points

**Real-time inference:**
- Location: `main.py`
- Triggers: `python main.py`
- Responsibilities: resolve weights, open webcam `cv2.VideoCapture(0)`, run YOLO inference at capped 5 FPS, draw boxes/HUD, exit on `q`

**Full pipeline:**
- Location: `run_pipeline.py`
- Triggers: `python run_pipeline.py`
- Responsibilities: run dataset stage then training stage as subprocesses (validation is *not* included)

**Individual stages:**
- Location: `scripts/download_and_convert_crowdhuman.py`, `scripts/train_body.py`, `scripts/validate_body.py`
- Triggers: `python scripts/<name>.py` (documented in `README.md` steps 1-3)
- Responsibilities: one stage each; recompute `base_dir = dirname(dirname(abspath(__file__)))` to locate the project root

**Monolithic/local+Colab trainer:**
- Location: `treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`
- Triggers: `python treinar_crowdhuman.py` or notebook cell execution
- Responsibilities: everything in one file — GPU check, weight seeding, download, conversion, `data.yaml` regeneration, training

**Environment setup:**
- Location: `scripts/setup_colab_ssh.py`
- Triggers: `python scripts/setup_colab_ssh.py`
- Responsibilities: download `cloudflared.exe` to `~/.ssh`, append a `ProxyCommand` block to `~/.ssh/config` for `*.trycloudflare.com`

## Error Handling

**Strategy:** Fail-fast with console messages; no exceptions raised to a top-level handler, no logging framework, no non-zero exit codes (scripts `print` and `return` on failure).

**Patterns:**
- Existence checks before acting: `main.py:19-22` prints `"Erro: Nenhum modelo encontrado."` and returns
- `run_pipeline.py` uses `check=True` so a failing stage raises `subprocess.CalledProcessError` (uncaught traceback)
- Broad `try/except` swallowing errors during dataset download: `treinar_crowdhuman.py:115-116` prints `[Aviso download]` and continues to training anyway
- Per-record skips in conversion: missing images or unreadable PIL files are silently `continue`d (`scripts/download_and_convert_crowdhuman.py:114,120`)
- SSL verification deliberately disabled: `urllib3.disable_warnings()` + `verify=False` (`scripts/download_and_convert_crowdhuman.py:10,51`)

## Cross-Cutting Concerns

**Logging:**
- Plain `print()` to stdout, messages in Portuguese, bracketed status tags (`[OK]`, `[Aviso]`, `-->`, `[STATUS]`); training progress delegated to Ultralytics' own console output (`verbose=True` in `main.py:48`)

**Validation:**
- No input validation layer; correctness enforced implicitly by Ultralytics (it reads `data.yaml` and the label files). Annotation numeric clamping to `[0,1]` happens inline in the converter (`scripts/download_and_convert_crowdhuman.py:136-139`)

**Configuration:**
- Split between external (`data.yaml`) and hard-coded (epochs/batch/loss weights in each training script — values differ between `scripts/train_body.py` and `treinar_crowdhuman.py`)
- `data.yaml` contains a machine-specific absolute `path:` (`C:\Users\fern\...`), so it must be rewritten (as `treinar_crowdhuman.py:119-122` does) or edited on any new machine

**Artifact Discovery:**
- Implicit contract on directory names: training always writes to `runs/detect/train_crowdhuman_body`, and downstream consumers (`main.py`, `scripts/validate_body.py`) hard-code that same name

**Reproducibility:**
- Ultralytics `seed: 0`, `deterministic: true` recorded in `runs/detect/train_crowdhuman_body/args.yaml`; no lockfile or requirements file pins the Python environment

---

*Architecture analysis: 2026-10-08*
*Update when major patterns change*
