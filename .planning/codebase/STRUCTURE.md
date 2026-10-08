# Codebase Structure

**Analysis Date:** 2026-10-08

## Directory Layout

```
scriptvisaocomput/
├── main.py                     # Webcam real-time inference entry point
├── run_pipeline.py             # 2-stage pipeline orchestrator (subprocess)
├── treinar_crowdhuman.py       # Monolithic end-to-end training script
├── treinar_crowdhuman_colab.ipynb  # Colab notebook variant of the trainer
├── data.yaml                   # Ultralytics dataset config (class: person)
├── README.md                   # Portuguese step-by-step guide
├── yolo26n.pt                  # Base YOLOv26-nano weights (5.3 MB)
├── scripts/                    # Pipeline stage scripts
│   ├── download_and_convert_crowdhuman.py  # Stage 1: dataset download + ODGT→YOLO
│   ├── train_body.py          # Stage 2: transfer-learning training
│   ├── validate_body.py       # Stage 3: formal val-split metrics
│   └── setup_colab_ssh.py     # Utility: cloudflared SSH config for Colab
├── models/                     # Isolated seed/base weights
│   └── base_face_weights.pt   # Copy of face-model weights for transfer learning
├── resultados/                 # Promoted trained weights (manual copies)
│   ├── best.pt
│   └── best (1).pt
├── runs/                       # Ultralytics run output (generated)
│   └── detect/train_crowdhuman_body/
│       ├── args.yaml          # Full hyperparameter record of last run
│       ├── train_batch*.jpg, labels.jpg  # Training preview plots
│       └── weights/           # (empty in this checkout — best.pt lives elsewhere)
├── test/                       # Sample media, NOT unit tests
│   └── gemini_generated_video_8d21d35f.mp4
├── .planning/codebase/         # GSD codebase analysis docs (this file)
└── .git/                       # Repo initialized, no commits yet
```

Not present but created at runtime: `dataset/` (with `images/{train,val}`, `labels/{train,val}`, `downloads_cache/`) — referenced by `data.yaml` and `scripts/download_and_convert_crowdhuman.py:13-14`.

## Directory Purposes

**scripts/:**
- Purpose: One script per ML pipeline stage, each independently runnable
- Contains: `*.py` stage scripts (snake_case, verb-first names)
- Key files: `download_and_convert_crowdhuman.py` (HuggingFace download + ODGT→YOLO conversion), `train_body.py` (Ultralytics training), `validate_body.py` (metrics), `setup_colab_ssh.py` (dev-environment SSH tunnel setup)
- Subdirectories: none (flat)

**models/:**
- Purpose: Isolated base/seed weights used to start transfer learning
- Contains: `*.pt` PyTorch checkpoints
- Key files: `base_face_weights.pt` — a *copy* of face-detection weights so training never mutates the original (per `scripts/train_body.py:7-8` comment)
- Note: scripts also fall back to a sibling-directory path `../models/yolo26n.pt` (`scripts/train_body.py:11`, `main.py:15`), which does not exist here

**resultados/:**
- Purpose: Stable, human-curated location for promoted trained weights ("resultados" = results)
- Contains: `best.pt`, `best (1).pt` (duplicate download/copy artifacts)
- Consumed by: `main.py:12` (first candidate in weight-resolution list)

**runs/:**
- Purpose: Ultralytics YOLO training/validation output (framework-generated)
- Contains: `detect/train_crowdhuman_body/` with `args.yaml` (116-line hyperparameter record), preview JPGs, `weights/` subdirectory
- Key files: `runs/detect/train_crowdhuman_body/args.yaml` — authoritative record of the last training run, including absolute paths from the original machine
- Subdirectories: `runs/detect/val_results/` is created by `scripts/validate_body.py:18` but is not present yet

**test/:**
- Purpose: Holds a single generated sample video (`gemini_generated_video_8d21d35f.mp4`, ~6 MB)
- Contains: media only — no test framework, no `*.test.py`/`*.spec.*` files anywhere in the repo
- Not a testing directory in the conventional sense

**Root (project root):**
- Purpose: Entry-point scripts and top-level config/documentation
- Contains: `main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`, `data.yaml`, `README.md`, `yolo26n.pt`

## Key File Locations

**Entry Points:**
- `main.py`: Real-time webcam body detection (`python main.py`, press `q` to quit)
- `run_pipeline.py`: Orchestrates dataset prep then training via `subprocess.run(..., check=True)`
- `treinar_crowdhuman.py`: Self-contained local training (download + convert + train in one file)
- `treinar_crowdhuman_colab.ipynb`: Same flow as a Colab notebook for GPU execution

**Configuration:**
- `data.yaml`: Ultralytics dataset spec (`path`, `train`, `val`, `nc: 1`, `names: ['person']`) — `path` is a hard-coded absolute path from another machine and must be updated per host
- `runs/detect/train_crowdhuman_body/args.yaml`: Generated record of every training hyperparameter
- Hyperparameters are otherwise hard-coded inline: `scripts/train_body.py:29-43` (epochs=300, imgsz=640, batch=8, box=8.5, cls=0.8, dfl=2.0) vs `treinar_crowdhuman.py:128-142` (box=10.0, cls=0.7, adaptive batch 8/32)
- No `requirements.txt`, `pyproject.toml`, `.gitignore`, or lint/format config exists

**Core Logic:**
- `scripts/download_and_convert_crowdhuman.py`: Dataset acquisition and label conversion (`download_file`, `extract_zip`, `flatten_directory`, `convert_odgt_to_yolo`)
- `scripts/train_body.py`: Training stage with weight fallback resolution
- `scripts/validate_body.py`: Validation stage printing mAP@0.5, mAP@0.5:0.95, P, R, F1
- `main.py:11-19`: Weight candidate-path resolution (5 ordered fallbacks)
- `treinar_crowdhuman.py`: Duplicated converter + `data.yaml` regeneration + GPU-aware batch sizing

**Testing:**
- No test files exist. `test/` contains only a sample MP4. Testing gap documented in the quality/concerns analysis.

**Documentation:**
- `README.md`: Portuguese guide with the 4-step usage flow (download → train → validate → webcam)

## Naming Conventions

**Files:**
- `snake_case.py` for all Python files, verb-first for actions: `train_body.py`, `validate_body.py`, `run_pipeline.py`, `download_and_convert_crowdhuman.py`
- Mixed languages: English technical terms in `scripts/`, Portuguese in root-level names (`treinar_crowdhuman.py`, `resultados/`)
- Notebooks: `{task}_{context}_{platform}.ipynb` — `treinar_crowdhuman_colab.ipynb`
- UPPERCASE for docs: `README.md`
- Artifact copies may contain spaces/parens: `resultados/best (1).pt` (avoid this pattern for new files)

**Directories:**
- Lowercase singular/plural, no separators: `scripts/`, `models/`, `runs/`, `test/`, `resultados/`
- Framework-generated hierarchy preserved: `runs/detect/{task}_{name}/` per Ultralytics convention

**Code:**
- Every script: `def main():` + `if __name__ == "__main__": main()` guard
- Path resolution idiom: `base_dir = os.path.dirname(os.path.abspath(__file__))` at root, `os.path.dirname(os.path.dirname(...))` inside `scripts/`
- Console status tags: `[OK]`, `[Aviso]`, `-->`, `====` banner separators; messages in Portuguese

## Where to Add New Code

**New Pipeline Stage:**
- Implementation: `scripts/{verb}_{noun}.py` with a `main()` guard
- Invocation: wire it into `run_pipeline.py` as an additional `subprocess.run([sys.executable, ...], check=True)` step
- Docs: add a numbered step to `README.md`

**New Entry-Point Script (user-facing):**
- Primary code: project root (e.g., next to `main.py`), following the candidate-path fallback pattern for locating weights

**Shared Helper Logic:**
- No shared module exists today. Prefer extracting a common module (e.g., `scripts/common.py` or `utils/`) rather than adding a third copy — the ODGT converter is already duplicated in `scripts/download_and_convert_crowdhuman.py:95` and `treinar_crowdhuman.py:86`
- Utility/environment scripts: `scripts/` (see `setup_colab_ssh.py`)

**New Configuration:**
- Dataset/class config: `data.yaml` (single file, root)
- Hyperparameters: currently inline in the training script; if externalizing, add a YAML next to `data.yaml` and reference it from `scripts/train_body.py`

**Trained Weights:**
- Keep framework output in `runs/detect/{run_name}/weights/best.pt`; promote a stable copy to `resultados/` or `models/` when it should be consumed by `main.py`

**Generated/Model Artifacts (do not hand-edit):**
- `runs/**`, `dataset/**`, `*.pt` checkpoints, `yolo26n.pt`

## Special Directories

**runs/**
- Purpose: Ultralytics-generated training/validation artifacts
- Source: Written by `scripts/train_body.py` (`project=runs/detect`, `name=train_crowdhuman_body`, `exist_ok=True` — reruns overwrite)
- Committed: Yes (currently tracked in git status as untracked-but-present; contains large preview JPGs)

**resultados/**
- Purpose: Manually promoted trained weights
- Source: Human copy of a run's `best.pt`
- Committed: Yes (untracked; ~5 MB per `.pt` file)

**dataset/** (absent)
- Purpose: CrowdHuman images + YOLO labels + `downloads_cache/`
- Source: Created by `scripts/download_and_convert_crowdhuman.py` or `treinar_crowdhuman.py`
- Committed: Not present in this checkout; referenced by `data.yaml`

**.planning/**
- Purpose: GSD planning/codebase analysis documents
- Source: Generated by `/gsd-map-codebase` and related commands
- Committed: Yes

**.git/**
- Purpose: Version control (repo initialized on `master`, zero commits, no `.gitignore`)
- Source: `git init`
- Committed: Everything currently untracked; large binaries (`*.pt`, MP4, JPG) will be committed unless ignored

---

*Structure analysis: 2026-10-08*
*Update when directory structure changes*
