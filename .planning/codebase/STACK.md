# Technology Stack

**Analysis Date:** 2026-10-08

## Languages

**Primary:**
- Python 3.11.9 - All application code (`main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`, `scripts/*.py`). No `.python-version`/`pyproject.toml` pin exists; 3.11.9 is the interpreter on the analysis machine.

**Secondary:**
- Jupyter Notebook / IPython (Google Colab flavor) - GPU training variant: `treinar_crowdhuman_colab.ipynb`
- YAML - Dataset and run configuration only: `data.yaml`, `runs/detect/train_crowdhuman_body/args.yaml`

## Runtime

**Environment:**
- CPython 3.11 on Windows (local training/inference; `cv2.VideoCapture(0)` webcam access, `workers=0` set explicitly "Compatível com Windows" in `scripts/train_body.py:39`)
- Google Colab (Linux, CUDA GPU) - alternate training runtime via `treinar_crowdhuman_colab.ipynb`
- CUDA/PyTorch GPU optional - `treinar_crowdhuman.py:28-33` probes `torch.cuda.is_available()` and falls back to CPU; `scripts/validate_body.py:27` hardcodes `device=0` (GPU required for validation)

**Package Manager:**
- pip (system Python)
- Lockfile: **missing** - no `requirements.txt`, `pyproject.toml`, `environment.yml`, `Pipfile`, or `poetry.lock` anywhere in the repo. Dependencies are only implied by imports.

## Frameworks

**Core:**
- Ultralytics YOLO `8.3.169` - object detection training, validation, and inference (YOLOv26 nano architecture, base weights `yolo26n.pt`). Used in `main.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `treinar_crowdhuman.py`
- PyTorch `2.6.0` (+ `torchvision 0.21.0`) - tensor/GPU backend under Ultralytics; direct use in `treinar_crowdhuman.py:8,28-31,125,138`
- OpenCV (`opencv-python 4.12.0.88`) - webcam capture, drawing, HUD overlay, display window in `main.py`
- Hugging Face Hub (`huggingface-hub 0.34.1`) - dataset download via `snapshot_download` in `treinar_crowdhuman.py:10,63-67`

**Testing:**
- Not detected - no test framework, no `*.test.*`/`*.spec.*` files, no pytest/unittest config.

**Build/Dev:**
- Not detected - no build step, no linter/formatter config (no `.eslintrc`, `ruff`, `black`, `flake8`, `mypy`).
- Google Colab notebook acts as the de-facto dev/CI environment for GPU runs (`treinar_crowdhuman_colab.ipynb` installs via `!pip install -q ultralytics huggingface_hub pillow`).

## Key Dependencies

**Critical:**
- `ultralytics` 8.3.169 - Everything: model loading, `.train()`, `.val()`, inference. Version matters: the "YOLOv26" model naming (`yolo26n.pt`) only exists in recent 8.3.x releases.
- `torch` 2.6.0 / `torchvision` 0.21.0 - Training engine, CUDA kernels, AMP (`amp: true` in `runs/detect/train_crowdhuman_body/args.yaml:29`).
- `opencv-python` 4.12.0.88 - Real-time webcam loop in `main.py`.
- `huggingface-hub` 0.34.1 - CrowdHuman dataset fetch (alt path to raw HTTP).
- `requests` 2.32.4 + `urllib3` 2.6.3 - Streaming dataset download with resume/size checks and TLS-warning suppression (`scripts/download_and_convert_crowdhuman.py:5,10`).
- `pillow` 11.0.0 - Reading image dimensions during `.odgt` → YOLO label conversion (`scripts/download_and_convert_crowdhuman.py:117`, `treinar_crowdhuman.py:95`).

**Infrastructure:**
- Python stdlib only for orchestration - `subprocess` (`run_pipeline.py:13,20`), `zipfile`, `json`, `os`, `urllib.request` (`scripts/setup_colab_ssh.py:2`).
- `numpy` 2.1.3 (transitive, required by ultralytics/opencv).

**Model artifacts (binary, committed):**
- `yolo26n.pt` (5.3 MB) - YOLOv26-nano base weights
- `models/base_face_weights.pt` (5.3 MB) - isolated copy of face-trained weights used as transfer-learning init (`scripts/train_body.py:8`)
- `resultados/best.pt`, `resultados/best (1).pt` (5.2 MB each) - trained body detectors; first candidate loaded by `main.py:12`

## Configuration

**Environment:**
- No environment variables and no `.env` files - the project is entirely self-configuring from file paths.
- Configuration is path-based: every script computes `base_dir` via `os.path.dirname(os.path.abspath(__file__))` and resolves assets relative to it.

**Build/Run config files:**
- `data.yaml` - Ultralytics dataset config: single class `person`, `train: images/train`, `val: images/val`. **Hardcodes an absolute path from another machine** (`path: C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\dataset`); `treinar_crowdhuman.py:118-122` rewrites it at runtime, but `scripts/train_body.py` and `scripts/validate_body.py` read it as-is.
- `runs/detect/train_crowdhuman_body/args.yaml` - Ultralytics-generated snapshot of the last training run (hyperparameters: `epochs: 300`, `imgsz: 640`, `batch: 8`, `patience: 50`, `cos_lr: true`, `box: 8.5`, `cls: 0.8`, `dfl: 2.0`). Also contains the foreign absolute paths.
- `scripts/train_body.py:29-43` - the authoritative hyperparameter source for the pipeline path.
- `treinar_crowdhuman.py:128-142` - a second, divergent hyperparameter set (`box: 10.0`, `cls: 0.7`, dynamic `batch`, `device=0`).

## Platform Requirements

**Development:**
- Windows 10/11 with Python 3.11+, a webcam for `main.py`
- Any platform for dataset prep/training except: `scripts/validate_body.py` requires a CUDA GPU (`device=0`)
- Optional: Google account for Colab GPU training (`treinar_crowdhuman_colab.ipynb`)
- Optional: SSH client + `cloudflared.exe` for the Colab SSH bridge (`scripts/setup_colab_ssh.py`)

**Production:**
- No deployment target - this is a local research/CLI project. Entry points are run manually:
  - `python run_pipeline.py` (download + train, via `subprocess`)
  - `python main.py` (webcam inference)
  - `python scripts/validate_body.py` (metrics)
- Google Colab + Google Drive for cloud training persistence (`/content/drive/MyDrive/yolo_crowdhuman_treinamento/runs` in `treinar_crowdhuman_colab.ipynb`)
- No Docker, no CI, no packaging metadata.

---

*Stack analysis: 2026-10-08*
*Update after major dependency changes*
