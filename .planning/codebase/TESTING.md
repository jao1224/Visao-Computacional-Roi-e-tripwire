# Testing Patterns

**Analysis Date:** 2026-10-08

## Test Framework

**Runner:**
- **None configured.** No pytest, unittest, or nose tests exist; no `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, `pyproject.toml`, or `requirements.txt`
- `pytest` is not installed in the environment (Python 3.11.9)
- No CI config (no `.github/`, no workflow files) — nothing runs tests automatically

**Assertion Library:**
- Not applicable (no tests). If adding tests, use `pytest` built-in `assert`

**Run Commands:**
```bash
python -m pytest                        # would be the standard entry (once added)
python scripts/validate_body.py         # current de-facto "test": YOLO validation metrics
python main.py                          # current de-facto "test": webcam smoke test (press q to quit)
python run_pipeline.py                  # end-to-end pipeline check (download + train, check=True aborts on failure)
```

## Test File Organization

**Location:**
- No test files. `test/` at repo root contains **only a sample asset** — `test/gemini_generated_video_8d21d35f.mp4` (6.3 MB). It is data, not a test suite, despite the directory name
- Do **not** put tests in `test/` without first renaming/clearing it — the directory is ambiguous

**Naming (recommended to match Python norms):**
- Unit tests: `tests/test_<module>.py` (new `tests/` directory at repo root)

**Structure:**
```
scriptvisaocomput/            # (current)
├── main.py
├── run_pipeline.py
├── treinar_crowdhuman.py
├── scripts/
│   ├── download_and_convert_crowdhuman.py
│   ├── train_body.py
│   ├── validate_body.py
│   └── setup_colab_ssh.py
├── test/                     # NOT tests - holds gemini_generated_video_8d21d35f.mp4
└── (no tests/, no conftest.py)
```

## Test Structure

**Suite Organization:**
- No existing suite pattern to copy. Recommended pattern for new tests (pytest style):
```python
# tests/test_convert_odgt.py
def test_convert_odgt_writes_yolo_labels(tmp_path):
    # arrange
    ...
    # act
    count = convert_odgt_to_yolo(odgt_path, images_dir, labels_dir)
    # assert
    assert count == 1
    assert "0 0.500000 0.500000 0.250000 0.500000" in (labels_dir / "img1.txt").read_text()
```

**Patterns:**
- Setup: pytest fixtures (`tmp_path` for dataset dirs) — no `beforeEach`/`setUp` precedent
- Teardown: rely on `tmp_path`/`monkeypatch` auto-cleanup; nothing global to restore
- Structure: arrange/act/assert with explicit comments (matches the codebase's numbered-comment habit)

## Mocking

**Framework:**
- None in use. Standard choice: `pytest` + `unittest.mock` (`monkeypatch`, `patch`)

**Patterns:**
```python
# Recommended for this codebase: patch network + filesystem boundaries
from unittest.mock import patch, MagicMock

@patch("scripts.download_and_convert_crowdhuman.requests.get")
def test_download_file_writes_chunks(mock_get, tmp_path):
    mock_get.return_value.iter_content.return_value = [b"a" * 1024, b"b" * 1024]
    mock_get.return_value.headers = {"content-length": "2048"}
    assert download_file("f.zip", str(tmp_path / "f.zip")) is True
```

**What to Mock:**
- Network: `requests.get` / `requests.head` (`scripts/download_and_convert_crowdhuman.py:36,51`), `huggingface_hub.snapshot_download` (`treinar_crowdhuman.py:63`)
- Ultralytics model: `ultralytics.YOLO` (constructor, `.train()`, `.val()`) — training is GPU-hours long
- Webcam/OpenCV: `cv2.VideoCapture` (`main.py:28`) for any `main.py` test
- `torch.cuda.is_available()` for hardware-dependent branches (`treinar_crowdhuman.py:28`, `train_body.py` device selection)
- `subprocess.run` when testing `run_pipeline.py`

**What NOT to Mock:**
- Pure functions: `convert_odgt_to_yolo`, `flatten_directory`, `extract_zip` — test against real files in `tmp_path`
- JSON/zip parsing logic (use tiny fixture files)

## Fixtures and Factories

**Test Data:**
```python
# Recommended: minimal ODGT fixture (one line of CrowdHuman JSON)
ODGT_LINE = '{"ID": "img1", "gtboxes": [{"tag": "person", "fbox": [100, 50, 200, 400]}]}'

# YOLO label expected output for a 640x400 image:
# "0 0.250000 0.562500 0.312500 1.000000"  (clamped by max/min guards)
```
- A tiny `.jpg` can be generated with `PIL.Image.new("RGB", (640, 400))` in the fixture rather than shipping binaries

**Location:**
- No fixtures exist. Recommended: `tests/fixtures/` for static `.odgt`/`.jpg` samples; inline factories in the test file for generated data

## Coverage

**Requirements:**
- None enforced (no coverage tool, no CI gate, no target)

**Configuration:**
- Not configured. If added: `pytest-cov` with `--cov=scripts --cov=main` and exclusions for `treinar_crowdhuman_colab.ipynb`

**View Coverage:**
```bash
python -m pytest --cov=scripts --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Scope (recommended): annotation conversion math (`convert_odgt_to_yolo`, clamping at `download_and_convert_crowdhuman.py:136-139`), download resume/size-check logic (`download_file`, `:33-44`), path fallback resolution (`main.py:11-19`, `scripts/train_body.py:9-12`)
- Mocking: network + filesystem only; feed real small files via `tmp_path`
- Speed: must run without GPU/model weights

**Integration Tests:**
- Not present. Closest equivalents are script runs with real data:
  - `python run_pipeline.py` — full download→train orchestration, aborts on first failure (`check=True`)
  - Ultralytics emits its own training artifacts to `runs/detect/train_crowdhuman_body/` (`args.yaml`, batch images) — inspect these for sanity checks

**E2E Tests:**
- Not used. Manual verification only:
  - `python main.py` — human-in-the-loop webcam check (HUD shows FPS + person count, `q` to quit; `main.py:73-82`)
  - `python scripts/validate_body.py` — prints mAP@0.5, mAP@0.5:0.95, P, R, F1 from `model.val()` (`validate_body.py:33-39`)
  - Notebook `treinar_crowdhuman_colab.ipynb` cell 1 is labeled "Teste de Conexao e Deteccao de GPU" — connectivity/GPU smoke check only

## Common Patterns

**Async Testing:**
- Not applicable — codebase is fully synchronous

**Error Testing:**
```python
# No precedent in repo. Recommended targets for failure-path tests:
def test_missing_model_returns_early(capsys, monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda p: False)   # all candidates missing
    main()
    assert "Erro: Nenhum modelo encontrado" in capsys.readouterr().out   # main.py:21
```

**Snapshot Testing:**
- Not used

**Metric Regression Checks (the domain's version of assertions):**
- Validated via `model.val()` metrics object: `metrics.box.map50`, `metrics.box.map`, `metrics.box.mp`, `metrics.box.mr` (`scripts/validate_body.py:34-38`)
- F1 computed inline with `1e-16` epsilon guard (`validate_body.py:38`)
- If automating: assert thresholds (e.g., `metrics.box.map50 >= 0.50`) after training; results live in `runs/detect/train_crowdhuman_body/results.csv`

---

*Testing analysis: 2026-10-08*
*Update when test patterns change*
