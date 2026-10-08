# Codebase Concerns

**Analysis Date:** 2026-10-08

Scope: full repo at `C:\Users\Windows\Desktop\scriptvisaocomput` (YOLO/CrowdHuman full-body detection pipeline). Python 3.11.9, `ultralytics 8.3.169`, `torch 2.6.0`, `opencv-python 4.12.0.88` installed. Git repo exists with **zero commits** and **no `.gitignore`**.

## Tech Debt

**No dependency manifest:**
- Issue: No `requirements.txt`, `pyproject.toml`, `environment.yml`, or lockfile anywhere in the repo; every third-party package is implicit.
- Files: repo root (absent); imports spread across `main.py:3-4`, `treinar_crowdhuman.py:6-11`, `scripts/download_and_convert_crowdhuman.py:5-7`
- Why: scripts were written to run on a machine where the env was already provisioned (a sibling `.venv` exists at `C:\Users\Windows\Desktop\visao computacional\.venv`)
- Impact: Setup is unreproducible; a fresh machine cannot install the project; CI/Colab runs drift from local behavior; `YOLO('yolo26n.pt')` behavior depends on the exact `ultralytics` build
- Fix approach: Add `requirements.txt` (or `pyproject.toml`) pinning `ultralytics`, `torch`, `torchvision`, `opencv-python`, `huggingface_hub`, `requests`, `pillow`; document the install step in `README.md`

**No `.gitignore` with ~29 MB of binaries staged for first commit:**
- Issue: Repo has no commits yet and no ignore rules; `git status` shows `models/`, `resultados/`, `runs/`, `test/`, `yolo26n.pt` as untracked
- Files: `yolo26n.pt` (5.5 MB), `models/base_face_weights.pt` (5.5 MB), `resultados/best.pt` (5.4 MB), `resultados/best (1).pt` (5.4 MB), `test/gemini_generated_video_8d21d35f.mp4` (6.2 MB), `runs/detect/train_crowdhuman_body/*.jpg` (~2.1 MB)
- Why: weights and artifacts were kept next to the code for convenience
- Impact: First commit bloats the repo permanently; future training output (`runs/`, `dataset/downloads_cache/` — CrowdHuman zips are GB-scale) will also be committed; repo becomes un-clonable
- Fix approach: Add `.gitignore` covering `dataset/`, `runs/`, `resultados/`, `models/*.pt`, `*.pt`, `test/*.mp4`, `__pycache__/`; decide explicitly which single canonical weight file (if any) is tracked via Git LFS

**Dataset download/convert logic duplicated three times:**
- Issue: The CrowdHuman download + `odgt → YOLO` conversion exists in three independent copies that have already diverged
- Files: `scripts/download_and_convert_crowdhuman.py:27-150` (requests + `verify=False`), `treinar_crowdhuman.py:61-116` (huggingface_hub `snapshot_download`), `treinar_crowdhuman_colab.ipynb` cell 4 (copy of the notebook version)
- Why: notebook → script → standalone pipeline evolution without extraction
- Impact: A bug fix in one copy does not propagate; the three copies use different download sources (direct HTTP vs HF hub cache) and different extraction behavior
- Fix approach: Extract one module (e.g. `scripts/dataset.py`) with `download_and_convert(...)`, `extract_zip(...)`, `convert_odgt_to_yolo(...)`; have `.py` scripts and the notebook import it (notebook: add repo root to `sys.path`)

**Training hyperparameters hardcoded in three places, already inconsistent:**
- Issue: Training config is inline in each entrypoint with different values
- Files: `scripts/train_body.py:29-43` (`box=8.5, cls=0.8, batch=8, workers=0`) vs `treinar_crowdhuman.py:128-142` (`box=10.0, cls=0.7, batch=auto 8/32`, no `workers`) vs `treinar_crowdhuman_colab.ipynb` cell 6 (`box=10.0, cls=0.7`)
- Impact: Results are not comparable between runs; it is impossible to tell which config produced `resultados/best.pt` (see `runs/detect/train_crowdhuman_body/args.yaml:84-87` — last recorded run used `box=8.5, cls=0.8`, i.e. `train_body.py`)
- Fix approach: Single config source (a `train_config.yaml` or shared constants module) consumed by all three entrypoints

**`data.yaml` is both generated output and tracked input:**
- Issue: `treinar_crowdhuman.py:118-122` and notebook cell 5 *overwrite* `data.yaml` at runtime, while `scripts/train_body.py:14` and `scripts/validate_body.py:17` *read* the checked-in copy
- Files: `data.yaml`
- Impact: File churn/diff noise; which version is authoritative depends on which script ran last (this is the direct cause of the broken pipeline bug below)
- Fix approach: Generate into `dataset/data.yaml` (inside the gitignored dataset dir) or resolve paths programmatically at runtime instead of persisting absolute paths

**Weight initialization depends on a directory outside the repo:**
- Issue: `treinar_crowdhuman.py:37-45` and notebook cell 3 fall back to `../runs/detect/train-14/weights/best.pt` (a face-detection run in a sibling project) and then to the bare relative path `'yolo26n.pt'` (CWD-dependent)
- Files: `treinar_crowdhuman.py:38,45`; `treinar_crowdhuman_colab.ipynb` cell 3; `scripts/train_body.py:8-12`
- Why: transfer learning started from a face model (`models/base_face_weights.pt`) and the lineage was never vendored
- Impact: On any other machine the primary init path is missing; the relative `'yolo26n.pt'` fallback silently depends on the shell's current directory (Ultralytics will attempt an internet download if it is not found)
- Fix approach: Vendor the intended init weights under `models/` (or explicitly download them) and resolve all fallbacks relative to `__file__`

## Known Bugs

**`run_pipeline.py` fails out of the box (stale absolute dataset path):**
- Symptoms: Stage 2 aborts with a Ultralytics dataset-path error after stage 1 completes successfully
- Trigger: Run `python run_pipeline.py` on a fresh clone — stage 1 (`scripts/download_and_convert_crowdhuman.py`) downloads to `./dataset/`, then stage 2 (`scripts/train_body.py:14`) loads the checked-in `data.yaml`, whose `path:` points at `C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\dataset` (`data.yaml:1`)
- Root cause: `data.yaml` is only regenerated by `treinar_crowdhuman.py`, which `run_pipeline.py` never calls
- Workaround: Manually run `python treinar_crowdhuman.py` once (it rewrites `data.yaml`), or edit `data.yaml:1` to `path: <repo>/dataset`
- Fix: Generate `data.yaml` inside the download step (`scripts/download_and_convert_crowdhuman.py:152`) so it is always in sync with where the data actually landed

**`scripts/validate_body.py` cannot run on this machine (missing weights + hard CUDA):**
- Symptoms: `FileNotFoundError` from `YOLO(...)`, or a CUDA device error
- Trigger: `python scripts/validate_body.py` — `runs/detect/train_crowdhuman_body/weights/` exists but is **empty** (no `best.pt`, no `results.csv`), so the fallback at `scripts/validate_body.py:9-13` resolves to `C:\Users\Windows\Desktop\models\yolo26n.pt`, which does not exist; even if it did, `scripts/validate_body.py:27` hardcodes `device=0`
- Root cause: trained weights live only in `resultados/best.pt`; fallback chain assumes a sibling `../models/` folder; device is not detected
- Workaround: Point `scripts/validate_body.py:8` at `resultados/best.pt` and change `device=0` to `device=0 if torch.cuda.is_available() else 'cpu'`
- Fix: Unify weight discovery (same candidate-list logic as `main.py:11-19`) and detect device

**Download script claims resume support it does not implement:**
- Symptoms: interrupted downloads restart from byte 0; dead code sits next to the request
- Files: `scripts/download_and_convert_crowdhuman.py:28` (docstring says "suporte a retomar download"), `scripts/download_and_convert_crowdhuman.py:47-49` (`headers = {}`, `mode = 'wb'`, `initial_pos = 0` — never used, no `Range` header)
- Impact: re-downloading the multi-hundred-MB CrowdHuman zips after a dropped connection; misleading docstring
- Fix: Either implement `Range`-based resume with a `.part` temp file + rename, or correct the docstring

**Whole-stage download errors swallowed, training then starts on an empty dataset:**
- Symptoms: `[Aviso download] ...` printed, then Ultralytics fails later with a confusing "image not found" / zero-length dataset error (or trains on a handful of images)
- Trigger: any network/auth failure during the HF snapshot step
- Files: `treinar_crowdhuman.py:62-116` (one `try/except Exception` wraps download **and** conversion; handler at `:115-116` only prints), then `treinar_crowdhuman.py:128` starts training unconditionally; same pattern in notebook cell 4
- Workaround: check for `[OK] Dataset pronto!` before trusting a training run
- Fix: re-raise after logging, or verify `len(os.listdir(train_img_dir)) > 0` before calling `model.train(...)`

**`flatten_directory` fails on re-runs in the `treinar_crowdhuman.py` copy:**
- Symptoms: `FileExistsError` (Windows) when `Images/` still holds files whose destination already exists; caught by the blanket handler above, silently truncating the dataset
- Files: `treinar_crowdhuman.py:80-84` (`os.rename` with no destination check) — note the standalone version at `scripts/download_and_convert_crowdhuman.py:89-93` correctly guards with `if not os.path.exists(dst)`
- Fix: port the guarded version (another symptom of the triplicated logic)

**Misleading terminal output in the download script:**
- Symptoms: prints `Iniciando treinamento automaticamente...` and exits without starting anything
- File: `scripts/download_and_convert_crowdhuman.py:196-198`
- Fix: remove the message or actually chain into training (delegating to `run_pipeline.py`)

**Webcam handle leaks on error in `main.py`:**
- Symptoms: camera stays claimed by the process after an exception (must kill Python to release it); window never closes
- Trigger: any exception inside the loop (e.g. model inference error, window closed externally)
- Files: `main.py:39-85` — `webcam.release()` / `cv2.destroyAllWindows()` at `:84-85` only run on normal loop exit; no `try/finally`
- Fix: wrap the loop in `try/finally`

**Duplicate weight artifact:**
- Symptoms: two identical 5.4 MB files; which one is "current" is unknowable from the name
- Files: `resultados/best.pt` and `resultados/best (1).pt` (SHA-256 identical: `E6C59F44…`)
- Fix: delete `best (1).pt`; never hand-copy weights — promote them from `runs/.../weights/` via a script step

## Security Considerations

**TLS certificate verification disabled for all dataset downloads:**
- Risk: machine-in-the-middle can substitute CrowdHuman images *and* labels — poisoned annotations directly steer the trained model; zip payloads are also attacker-controlled
- Files: `scripts/download_and_convert_crowdhuman.py:10` (`urllib3.disable_warnings(...)`), `:36` (`requests.head(..., verify=False)`), `:51` (`requests.get(..., verify=False)`); `treinar_crowdhuman.py:14` (`urllib3.disable_warnings()`)
- Current mitigation: none (comment at `scripts/download_and_convert_crowdhuman.py:9` cites proxy/local certs as the reason)
- Recommendations: verify TLS by default and allow opting out via an env var (`CROWDHUMAN_INSECURE=1`); if a corporate proxy is the real cause, install the proxy CA instead of disabling verification globally

**Zip extraction without path validation (zip-slip) on unverified downloads:**
- Risk: a crafted zip can write files outside the dataset directory (arbitrary file write, incl. startup folders / SSH config)
- Files: `scripts/download_and_convert_crowdhuman.py:77-78` (`zip_ref.extractall(...)`), `treinar_crowdhuman.py:73-74`, notebook cell 4 — compounding the `verify=False` issue above
- Current mitigation: files come from a known HuggingFace repo (but over unverified TLS)
- Recommendations: validate member paths (`os.path.realpath` must stay under the destination) before extraction, or use `zipfile` member filtering

**`scripts/setup_colab_ssh.py` widens SSH trust and installs an unsigned binary:**
- Risk: (a) downloads `cloudflared.exe` from `releases/latest` with no checksum/signature pinning (`scripts/setup_colab_ssh.py:10-11`); (b) appends a wildcard rule to the user's `~/.ssh/config` — `Host *.trycloudflare.com` with `User root` and a `ProxyCommand` (`scripts/setup_colab_ssh.py:18-24`) — so *any* host matching that wildcard is contacted as `root` through the tool
- Current mitigation: config entry is only written if the marker string is absent (`scripts/setup_colab_ssh.py:31`); the ProxyCommand still requires Cloudflare access credentials to authenticate
- Recommendations: pin the cloudflared version + SHA-256; narrow the `Host` pattern to the specific tunnel hostname; document in `README.md` that this script mutates `~/.ssh/config`

**Untrusted pickle deserialization of model weights:**
- Risk: `.pt` files are torch pickles; loading a tampered weight file executes arbitrary code. Weight provenance is untracked (see Tech Debt), and one file is literally a duplicate with a copy-paste name
- Files: `resultados/best.pt`, `resultados/best (1).pt`, `models/base_face_weights.pt`, `yolo26n.pt` — loaded at `main.py:25`, `scripts/train_body.py:26`, `scripts/validate_body.py:21`, `treinar_crowdhuman.py:48`
- Current mitigation: `torch 2.6.0` defaults `weights_only=True` for `torch.load`, and Ultralytics honors it on recent versions; `ultralytics` is **unpinned**, so this mitigation is not guaranteed
- Recommendations: pin `ultralytics`/`torch`, record a checksum for each accepted weight file, prefer official released weights over hand-copied artifacts

**Path/username disclosure in tracked config artifacts:**
- Risk: low — leaks the original author's username and directory layout (`C:\Users\ferna\...`) to anyone with repo access
- Files: `data.yaml:1`, `runs/detect/train_crowdhuman_body/args.yaml:3-4,15,116`
- Recommendations: regenerate `data.yaml` per machine (see Tech Debt); gitignore `runs/` artifacts

**Secrets scan:** No `.env` files, API keys, tokens, or credentials detected anywhere in the repo. Not applicable beyond the items above.

## Performance Bottlenecks

**Single-worker dataloader during training:**
- Problem: `workers=0` forces in-process, serial sample loading/augmentation
- Files: `scripts/train_body.py:39`
- Cause: Windows multiprocessing compatibility workaround (comment: `# Compatível com Windows`)
- Improvement path: use `workers=2..4` (Ultralytics handles Windows spawn); note the other entrypoints (`treinar_crowdhuman.py`, notebook) omit `workers` entirely and take the default of 8 — behavior is inconsistent, not just slow

**Serial, non-resumable dataset download:**
- Problem: six files downloaded one at a time, 1 MB chunks, one `HEAD` request per file before starting
- Files: `scripts/download_and_convert_crowdhuman.py:169-171` (loop), `:56-66` (chunk loop)
- Cause: `requests` streaming with no concurrency; no resume (see Known Bugs)
- Improvement path: implement resume + optional `concurrent.futures` parallel downloads; skip the `HEAD` when a checksum manifest is available

**Real-time inference loop capped and verbose:**
- Problem: every frame logged by Ultralytics (`verbose=True`) plus per-box drawing at a self-imposed 5 FPS target
- Files: `main.py:35-36` (`target_fps = 5`), `main.py:48` (`verbose=True`)
- Cause: console I/O and `cv2.waitKey` throttle dominate; no frame skipping (`stream=True` unused) and no HALF/INT8 export
- Improvement path: set `verbose=False`, consider `model(frame, stream=True)`, and export to ONNX/TensorRT if higher FPS is required

**Progress printing spams the terminal:**
- Problem: `int(pct) % 10 == 0` is true for *every* chunk spanning that integer, so the percentage line re-prints hundreds of times per file
- Files: `scripts/download_and_convert_crowdhuman.py:65-66`
- Fix: print only when the integer percent changes (`last_pct` tracking)

## Fragile Areas

**Model-path resolution (four different ad-hoc fallback chains):**
- Files: `main.py:11-19` (candidate list), `scripts/train_body.py:8-12`, `scripts/validate_body.py:8-13`, `treinar_crowdhuman.py:37-45`
- Why fragile: each chain points at different locations, two of them reach **outside** the repo (`../models/yolo26n.pt` does not exist on this machine; `../runs/detect/train-14` does not exist), one uses a CWD-relative path
- Common failures: silent fallback to a *base, untrained* model (validation then reports meaningless mAP — `scripts/validate_body.py:13` only prints a warning), or a hard crash
- Safe modification: do not add a fifth chain; consolidate into one resolver (e.g. `resolve_weights()` returning a path + provenance string) and make the caller fail loudly instead of falling back
- Test coverage: none

**Three diverging copies of the same pipeline:**
- Files: `scripts/*` (pipeline), `treinar_crowdhuman.py` (all-in-one), `treinar_crowdhuman_colab.ipynb` (notebook)
- Why fragile: fixes must be applied 3×; they already disagree on hyperparameters, `workers`, `os.rename` safety, and download source
- Common failures: "works in the notebook, fails in the script" reports
- Safe modification: change one copy only after checking the other two, or invest in the shared-module refactor first
- Test coverage: none

**Training artifacts directory is in a partial, inconsistent state:**
- Files: `runs/detect/train_crowdhuman_body/` — contains `args.yaml` + 4 result JPGs, but `weights/` is empty and `results.csv` (documented in `README.md:31`) is missing
- Why fragile: `exist_ok=True` in every training call (`scripts/train_body.py:42`, `treinar_crowdhuman.py:141`, notebook cell 6) overwrites the previous run in place; the current state is the aftermath of such an overwrite (weights deleted, plots left behind)
- Common failures: losing the previous model on retrain; readers assuming `weights/best.pt` exists because the folder does
- Safe modification: set `exist_ok=False` (or timestamped `name=`) and treat `runs/` as fully disposable/gitignored
- Test coverage: none

**Generated `data.yaml` and `runs/**/args.yaml` are treated as source:**
- Files: `data.yaml`, `runs/detect/train_crowdhuman_body/args.yaml`
- Why fragile: absolute paths from another machine (`C:\Users\ferna\...`); any script that reads them on a different host breaks
- Safe modification: never edit these by hand — regenerate (`treinar_crowdhuman.py:118-122`) or gitignore them
- Test coverage: none

## Scaling Limits

**Single-GPU / single-machine training:**
- Current capacity: batch heuristic at `treinar_crowdhuman.py:125` — batch 32 only if VRAM > 15 GB, else batch 8 at `imgsz=640`, 300 epochs, `patience=50`
- Limit: CrowdHuman train is ~15k images; on a smaller GPU the run is hours-to-days, and `workers=0` (in `scripts/train_body.py:39`) leaves CPU I/O as the ceiling
- Symptoms at limit: CUDA OOM (Ultralytics reduces batch only when `batch=-1`, not here), or extremely low GPU utilization from the single-worker loader
- Scaling path: use auto batch (`batch=-1`), enable the dataloader workers, or move the run to Colab (the notebook is the existing path for that)

**Local-only inference:**
- Current capacity: 1 webcam, index hardcoded to `0` (`main.py:28`), 5 FPS target (`main.py:35`)
- Limit: no multi-camera/stream support; every frame is drawn and displayed synchronously
- Scaling path: parameterize the source (`sys.argv`/config), batch multiple streams through one model instance, drop to ONNX/TensorRT export

**Disk budget:**
- Current capacity: repo currently occupies ~29 MB excluding `.git`; CrowdHuman download cache adds several hundred MB (`dataset/downloads_cache/`, `scripts/download_and_convert_crowdhuman.py:14`), extracted images more
- Limit: unknown free space not checked; nothing cleans `downloads_cache/`
- Scaling path: gitignore `dataset/`, add a `--clean` flag that deletes zips after successful extraction

## Dependencies at Risk

**`ultralytics` (installed 8.3.169, unpinned):**
- Risk: the project is branded "YOLOv26" throughout (`README.md`, `scripts/train_body.py:18`, `main.py:76`) but the installed package ships architecture YAMLs only for `v3–v12, v10, rt-detr` — no `26/` config; `yolo26n.pt` loads today only because the weight checkpoint carries its own config, and the package is not version-locked
- Impact: any `pip install -U ultralytics` can change trainer defaults, drop the `yolo26` weights URL, or alter `data.yaml` schema handling — training/validation breaks with no code change
- Migration plan: pin `ultralytics==8.3.169` (or whichever version is validated) in the new requirements file; confirm `YOLO26` support explicitly before upgrading

**`opencv-python` 4.12.0.88 + `opencv-python-headless` 5.0.0.93 both installed:**
- Risk: two packages provide the same `cv2` module at different major versions; whichever sits last on `sys.path` wins
- Impact: `main.py` uses GUI functions (`cv2.imshow` at `main.py:76`) which **do not exist** in the headless build; import order determines whether the webcam demo works
- Migration plan: keep exactly one — `opencv-python` for this repo; uninstall the headless build from the shared environment (or isolate the project in its own venv, which is also the fix for the missing dependency manifest)

**HuggingFace dataset mirror (`sshao0516/CrowdHuman`):**
- Risk: third-party re-upload of CrowdHuman; `snapshot_download` at `treinar_crowdhuman.py:63-67` and the raw URL base at `scripts/download_and_convert_crowdhuman.py:16` both depend on it staying available and unchanged
- Impact: stage 1 of the pipeline stops working; no local mirror or checksum fallback
- Migration plan: cache the zips (already the role of `dataset/downloads_cache/`) and record file hashes; keep the official crowdhuman.org download documented in `README.md:43` as the alternate source

**CrowdHuman dataset licensing:**
- Risk: CrowdHuman is distributed under research/non-commercial terms; nothing in the repo records acceptance or the intended use of `resultados/best.pt`
- Impact: compliance gap if the model is shipped commercially
- Migration plan: add a note to `README.md` stating the dataset license and the intended use of the trained weights

**`requests` / `urllib3` used only with `verify=False`:**
- Risk: the sole use of these libraries in the repo is TLS-disabled fetching (see Security)
- Migration plan: if verification cannot be restored, consider whether `huggingface_hub`'s downloader (which verifies TLS) should be the only download path

## Missing Critical Features

**Dependency/environment definition:**
- Problem: no `requirements.txt`/`pyproject.toml` (see Tech Debt)
- Current workaround: copy package list from a working machine or read imports by hand
- Blocks: clean onboarding, CI, reproducible Colab runs
- Implementation complexity: Low (one file + a pinned list)

**`.gitignore` and artifact policy:**
- Problem: nothing excludes weights, datasets, runs, or the stray `test/gemini_generated_video_8d21d35f.mp4`
- Current workaround: careful manual `git add`
- Blocks: the first safe commit; any future collaboration
- Implementation complexity: Low

**Model promotion/provenance step:**
- Problem: no script copies `runs/detect/train_crowdhuman_body/weights/best.pt` → `resultados/best.pt`, so the deployed weight's training run, metrics, and config are unrecorded (and `runs/.../weights/` is currently empty)
- Current workaround: manual copy (which produced the `best (1).pt` duplicate)
- Blocks: reproducibility, regression comparison between model versions, trusting validation numbers
- Implementation complexity: Low–Medium (a `promote_weights.py` that also records mAP from `results.csv`)

**CLI arguments / configuration:**
- Problem: camera index (`main.py:28`), thresholds (`main.py:48`: `conf=0.25, iou=0.60`), device (`scripts/validate_body.py:27`), epochs/batch/loss weights are all hardcoded
- Current workaround: edit source
- Blocks: running against a video file, CPU-only validation, tuning without code changes
- Implementation complexity: Low (`argparse` per script)

**Validation gate before training/inference:**
- Problem: nothing checks that the dataset is non-empty before `model.train(...)` (`treinar_crowdhuman.py:128`) or that weights are trained (not the COCO base) before `main.py` inference
- Current workaround: read the console warnings
- Blocks: silent bad runs (training on an empty dir; demoing an untrained model)
- Implementation complexity: Low (assert counts/paths before the call)

**Logging and run tracking:**
- Problem: `print()` only (no `logging`, no CSV/metrics export beyond Ultralytics' own `runs/` output, and `results.csv` is missing from the committed run dir)
- Current workaround: scroll terminal output
- Blocks: diagnosing a failed overnight training run; comparing experiments
- Implementation complexity: Medium (stdlib `logging` + keep Ultralytics' `results.csv` under versioned experiment metadata)

## Test Coverage Gaps

**Entire codebase — zero automated tests:**
- What's not tested: everything; there is no test framework, no `tests/` directory, and no test files (`*.test.*` / `*.spec.*` / `test_*.py`) anywhere
- Files: all (`main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`, `scripts/*.py`)
- Risk: the annotation converter (coordinate normalization at `scripts/download_and_convert_crowdhuman.py:136-139`) can silently produce wrong labels — the failure mode is a worse model, not an exception
- Priority: High for pure functions (conversion, path resolution), Medium elsewhere
- Difficulty to test: no dependency manifest makes test env setup impossible today (fix that first); converter is however trivially testable with a tiny inline `odgt` fixture

**End-to-end pipeline (`run_pipeline.py`):**
- What's not tested: stage 1 → stage 2 handoff, `data.yaml` generation, fallback weight resolution
- Risk: the known broken handoff above shipped without detection and would recur after any refactor
- Priority: High
- Difficulty to test: needs a mocked/small dataset (CrowdHuman download is too large for CI); a `--smoke` mode with a 10-image fixture would make this feasible

**Model quality regression:**
- What's not tested: no baseline mAP is recorded anywhere; `scripts/validate_body.py` cannot even run in the current state (see Known Bugs)
- Risk: a retrained model that is worse than `resultados/best.pt` is indistinguishable from one that is better
- Priority: Medium
- Difficulty to test: requires the validation dataset to be present; store the last-known mAP next to each weight file

**Webcam demo (`main.py`):**
- What's not tested: no way to run headless (no video-file input), so it can only be verified manually with a camera
- Risk: regressions in drawing/FPS logic are only found by a human watching the window
- Priority: Low
- Difficulty to test: add `--source path.mp4` and assert the loop terminates + writes a frame

---

*Concerns audit: 2026-10-08*
*Update as issues are fixed or new ones discovered*
