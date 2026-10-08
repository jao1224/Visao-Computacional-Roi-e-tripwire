# Stack Research

**Domain:** Real-time people-counting / flow analytics platform (RTSP multi-camera → YOLO+ByteTrack → PostgreSQL → FastAPI → dashboard)
**Researched:** 2026-10-08
**Confidence:** HIGH (versions verified directly against PyPI / npm / GitHub registries on 2026-10-08; architecture patterns verified against current official docs and 2025–2026 ecosystem projects)

> Scope: NEW layers only (ingestion, tracking, queues, DB, API, dashboard). Existing detector (`main.py`, YOLO CrowdHuman) is out of scope per milestone context.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | **3.12+** (pin 3.12) | Runtime | Hard requirement: `av` (PyAV) 19.x ships `cp312-abi3` wheels only (requires ≥3.12), `sqlalchemy` 2.1 requires ≥3.11. 3.12 also gives `TaskGroup`, improved asyncio. Verified on PyPI 2026-10-08. **HIGH** |
| PyAV (`av`) | **19.0.1** | RTSP/FFmpeg decoding (ingestion layer) | FFmpeg bindings with explicit error handling (`AVERROR_TIMEOUT`, `AVERROR_EOF`, `AVERROR_INVALIDDATA`) and controllable reconnect — the missing pieces in OpenCV's capture. Prebuilt `win_amd64` abi3 wheels exist (Windows dev OK). Community consensus (StackOverflow, 2026 OpenCV issue thread): "use PyAV, error handling is much better." **HIGH** |
| Ultralytics | **8.4.x** (8.4.174, released 2026-10-06) | YOLO inference (existing detector + new pipeline) | Already in use in `main.py`; active releases (~weekly). Keep as the inference front-end; pipeline wraps it, doesn't replace it. **HIGH** |
| `trackers` (Roboflow) | **2.6.x** (2.6.1, released 2026-09-25) | ByteTrack multi-object tracking | Successor to `sv.ByteTrack`, which is **deprecated since supervision 0.28.0 and removed in 0.31.0**. Apache-2.0, detector-agnostic, speaks `supervision.Detections` natively, one interface across SORT/ByteTrack/OC-SORT/BoT-SORT if we later swap algorithms. `ByteTrackTracker().update(detections)` per camera instance. **HIGH** |
| supervision | **0.30.x** (0.30.8) | `Detections` container, geometry/zone helpers, annotation (debug views) | De-facto interchange format between detector and tracker; polygon/point-in-polygon utilities for zone ROI logic. Use `trackers` for tracking, **never `sv.ByteTrack`** (deprecated). **HIGH** |
| PostgreSQL | **18** (GA 2025-09-25); 17 acceptable | System of record: zonas, cameras, sessões, session_traces, metricas_fluxo_zona | Doc 06 schema is already specified for Postgres. PG 18 adds async I/O (up to 3× read throughput), `uuidv7()`, skip-scan — helps time-series/occupancy queries. `JSONB` natively stores zone polygons (doc 02). **HIGH** |
| asyncpg | **0.32.x** | Async Postgres driver for batch writer + API | Native protocol, no libpq; `create_pool()` built in (no PgBouncer needed at this scale); `executemany` / `copy_records_to_table` make the "batch upsert every few seconds" pattern from doc 02 trivial and fully non-blocking. **HIGH** |
| SQLAlchemy | **2.1.x** (2.1.4, async core) + Alembic **1.20.x** | ORM/query layer + schema migrations | 2.x async-first (`create_async_engine` + asyncpg driver). Alembic tracks the doc-06 schema evolution. Batch writer may bypass ORM and use Core `insert().values([...])` (executemany path) for throughput. **HIGH** |
| FastAPI | **0.143.x** + Uvicorn **0.54.x** | REST API + WebSocket hub | Spec'd in docs 02/08. Native WebSocket support pushes live occupancy to dashboard without polling; Pydantic **2.13.x** schemas for request/response; middleware hook for the Marco Civil 6-month access log (IP, port, timestamp). **HIGH** |
| React 19 + TypeScript + Vite | React **19.3.0**, Vite **8.3.4**, TS, Tailwind **4.3.x** | Dashboard SPA | The consistent 2025–2026 pattern across comparable open-source people-counting/occupancy projects (FastAPI + WebSocket + React/Vite). Vite dev server is fast, single `npm run dev` alongside Python. **HIGH** |
| ECharts | **6.1.x** | Charts: time series + heatmaps | Native heatmap series + smooth large time-series — covers occupancy trends AND heat-map views in one library. Canvas renderer handles thousands of points. **MEDIUM** (lib choice, not domain-critical) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | **2.5.x** | Frame math, heatmap grid accumulation, polygon tests | Everywhere in the vision/analytics layer |
| opencv-python | **5.0.x** (or whatever `main.py` already pins) | Image ops, drawing debug overlays | Only for frame manipulation — **never for RTSP capture** (see What NOT to Use) |
| structlog | **26.1.x** | JSON structured logging | All services; logs carry `camera_id`, `track_id`, latency fields |
| prometheus-client | **0.26.x** | Metrics: FPS, inference ms, queue depth, reconnects | Expose `/metrics` from FastAPI + workers (pattern used by comparable 2025/26 CV analytics projects) |
| pydantic-settings | **2.15.x** | Config from `.env`/YAML (cameras, RTSP URLs, thresholds) | Single config source for workers and API |
| httpx | **0.28.x** | Async HTTP client | Tests against FastAPI (`httpx.ASGITransport`), webhook calls if ever needed |
| pytest **9.1.x** + pytest-asyncio **1.4.x** | — | Test harness | Async API tests, queue/writer unit tests |
| MediaMTX | **v1.21.1** (2026-09-20) | Local RTSP server for development | **Key enabler:** user has no DVRs yet — publish sample MP4s as `rtsp://localhost:8554/...` and exercise the real PyAV ingestion/reconnect path from day 1 instead of discovering RTSP bugs only at deployment |
| orjson | **3.13.x** | Fast JSON serialization | WebSocket payload serialization (optional) |

### Architecture-Implied Concurrency Stack (no extra libs needed)

| Mechanism | Purpose | Why |
|-----------|---------|-----|
| `threading.Thread` (1 per camera) + PyAV | Decode loop | PyAV releases the GIL during decode; 8–16 camera decodes are fine as threads |
| `multiprocessing.Queue(maxsize=1)` drop-oldest ("latest frame wins") | Frame handoff decode → inference | Backpressure-proof: old frames are stale by definition; verified pattern in comparable real-time CV projects (2025/2026) |
| Dedicated **inference process** (GPU), batching frames across cameras | Keeps ≤5 ms/frame budget isolated from API/GIL | Torch releases GIL but Python-side post-processing doesn't; process isolation also survives a CUDA crash |
| Per-camera `ByteTrackTracker` instance inside inference process | Intra-camera association | Tracker state must never be shared across cameras |
| `asyncio.Queue` + 2–5 s flush task (executemany/COPY) | DB batch writer | Doc 02/08 mandate: **zero DB I/O inside the video loop** |
| FastAPI lifespan task | Owns the writer + WebSocket broadcaster | Single-process control plane; workers are separate processes |

---

## Installation

```bash
# Python (3.12+)
pip install ultralytics==8.4.* av==19.0.1 supervision==0.30.* trackers==2.6.*
pip install fastapi==0.143.* uvicorn==0.54.* pydantic==2.13.* pydantic-settings==2.15.*
pip install "sqlalchemy[asyncio]==2.1.*" alembic==1.20.* asyncpg==0.32.*
pip install structlog==26.* prometheus-client==0.26.* httpx pytest pytest-asyncio

# Dev tooling
pip install ruff

# Dev RTSP source (no DVRs available yet) — release binary from
# https://github.com/bluenviron/mediamtx/releases (v1.21.1)

# Dashboard
npm create vite@latest dashboard -- --template react-ts
npm install echarts axios
npm install -D tailwindcss @tailwindcss/vite
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PyAV for RTSP | **ffmpeg subprocess** (`-rtsp_transport tcp -f rawvideo pipe:0`) | If PyAV wheel/codec issues appear with a specific DVR codec — ffmpeg subprocess showed 0 corrupted frames in the same test where OpenCV failed; slightly coarser control but rock solid. Good fallback. |
| PyAV for RTSP | **GStreamer (PyGObject)** | Only if HW decode (NVDEC) per-stream becomes CPU-bound at 16 cameras — GStreamer adds NVDEC but heavy system dependency; premature at 8–16 sub-1080p streams |
| PyAV for RTSP | **ffmpegcv** | API-compatible with OpenCV, low-latency RTSP mode — but README itself flags stream reading as *experimental*; not production-grade signal |
| `trackers.ByteTrackTracker` | **Ultralytics built-in** `model.track(tracker="bytetrack.yaml")` | Acceptable shortcut for the first spike (zero extra deps, already have ultralytics). Downsides: tracker config hidden in YAML, couples tracking to the ultralytics model API, harder to swap algorithms. Prefer `trackers` for the real pipeline |
| `trackers.ByteTrackTracker` | **OC-SORT / BoT-SORT** (same `trackers` package) | Drop-in if ByteTrack underperforms in hotel occlusion scenes (lobby queues, restaurant tables) — one-line swap thanks to uniform interface |
| asyncpg batch writer | **Redis + Celery/arq workers** | Only when scaling to multiple API nodes. Single GPU node with in-process queues doesn't justify a broker (extra ops, no throughput need) |
| PostgreSQL 18 | **TimescaleDB extension** | Only if doc-06 tables grow huge *and* we need continuous aggregates/retention policies. Current scale (zones × cameras × 1–5 s rollups) is plain SQL + indexes; schema is already fixed in doc 06 |
| React + Vite SPA | **Grafana** | Grafana for *ops* views (pipeline health, FPS, reconnects) is a great free add-on later; it can't deliver the hotel-facing zone/heatmap UX |
| React + Vite + ECharts | **Next.js** | Next.js only if SSR/SEO mattered — it doesn't for an internal dashboard; Vite is simpler to build/deploy |
| FastAPI WebSocket push | **Polling REST** | Polling acceptable for v1 history views; use WebSocket only for live occupancy (dashboard "instant" requirement) |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **`cv2.VideoCapture` for RTSP** | Silent corruption after 15–30 min of continuous RTSP with `ret=True` (opencv/opencv#28638, 2026-03); `.read()` blocks indefinitely on stalled streams; no real timeout/reconnect story. Directly threatens the ≤5 ms real-time budget and adds invisible production failures | **PyAV** (`av.open(url)` + explicit `AVERROR_*` handling + backoff reconnect), or ffmpeg subprocess as fallback |
| **`sv.ByteTrack` (supervision)** | Deprecated in supervision 0.28.0, **removed in 0.31.0** — code written today breaks on the next minor upgrade | `trackers.ByteTrackTracker` (`pip install trackers`) |
| **DB I/O (any driver) inside the capture/inference loop** | Violates doc 08 rule #1; a 50 ms DB hiccup = 10 dropped frames and broken dwell-time math | `asyncio.Queue` + periodic batch flush (executemany/COPY) |
| **Celery + Redis/RabbitMQ** | Broker operational cost for what is a single-node, in-memory producer/consumer problem; adds failure modes (broker down = counters stop) | `multiprocessing.Queue` → asyncio batch writer in FastAPI process |
| **SQLite as the platform DB** | Concurrent writers (batch writer + API + migrations), no `JSONB`, schema in doc 06 targets Postgres | PostgreSQL 18 |
| **Streamlit / Dash for the production dashboard** | Single-user-ish model, session-per-browser, awkward WebSocket control, poor fit for a multi-view hotel ops console; Dash is Plotly-heavy for what are mostly simple occupancy views | React + Vite + ECharts (fastpath: Streamlit OK as a throwaway spike only) |
| **DeepStream / Triton / Triton-adjacent GPU servers** | Enterprise inference-server complexity far beyond 8–16 cameras on one RTX GPU; steep install, Docker/CUDA pinning | Single inference process with Ultralytics + batched frames |
| **Storing frames/snapshots "just for debugging"** | LGPD: frames are volatile by design (PROJECT.md Out of Scope; doc 08 §2). Debug views must be ephemeral (annotated frame → JPEG → RAM/window only, never disk/DB) | Annotated overlay on a bounded in-memory ring buffer, opt-in, auto-expiring |
| **`uvloop`** | Not available on Windows (dev machine is win32) — importing it breaks local runs | Default asyncio event loop; add uvloop later only in the Linux deploy image if profiling shows need |

---

## Stack Patterns by Variant

**If developing on Windows (current reality) + webcam/sample videos:**
- Same stack — PyAV reads local MP4/webcam too; MediaMTX serves samples over RTSP locally so ingestion code is production-identical from day 1.
- `multiprocessing` uses **spawn** on Windows: guard all worker entrypoints with `if __name__ == "__main__":`.
- No uvloop; asyncio default loop.

**If 1 GPU + 8–16 cameras (target):**
- Decode threads → shared inference process with cross-camera batching + frame skipping (process every Nth frame per camera; 320 FPS budget ÷ 16 cams ≈ 20 FPS/cam — plenty).
- Trackers live inside the inference process; only *events* (enter/exit/dwell/rollup) leave it — queue payloads are tiny.

**If moving to production RTSP (DVRs arrive):**
- Only the ingestion config changes (RTSP URLs, TCP transport, sub-stream 720p @ 15 FPS per doc 02). PyAV path + reconnect backoff already exercised against MediaMTX.

**If API must be exposed (internet):**
- Add access-log middleware writing IP/port/timestamp with 180-day retention (Marco Civil Art. 15) — table added via Alembic, written **asynchronously** (never blocking a request path on a synchronous insert).

---

## Version Compatibility

| Package | Constraint | Notes |
|---------|-----------|-------|
| `av==19.0.1` | Python ≥ 3.12 | abi3 wheels for win_amd64/linux/macos; verified on PyPI 2026-10-08 |
| `sqlalchemy==2.1.x` | Python ≥ 3.11 | async engine requires `greenlet` (pulled in automatically) |
| `supervision==0.30.x` | Python ≥ 3.10 | Do NOT bump to ≥0.31 without replacing `sv.ByteTrack` usage (removed) — with `trackers` this is a non-issue |
| `trackers==2.6.x` | Python ≥ 3.10 | Depends on `supervision` for the `Detections` type |
| `numpy==2.5.x` | Python ≥ 3.12 | OpenCV 5.x and torch 2.14 support numpy 2.x; avoid mixing with any legacy numpy-1-only cv2 build |
| `asyncpg==0.32.x` | Python ≥ 3.9 | async-only API — don't accidentally use it in sync code paths |
| PostgreSQL driver | `asyncpg` ↔ PG 17/18 | asyncpg supports PG 12+; no issue with PG 18 |
| Windows + `multiprocessing` | spawn start method | Every worker module must be import-safe (no side effects at module top level) |

---

## Sources

- PyPI JSON API (`/pypi/<pkg>/json`) — all Python versions fetched 2026-10-08 (HIGH): `ultralytics 8.4.174`, `supervision 0.30.8`, `trackers 2.6.1`, `av 19.0.1`, `fastapi 0.143.0`, `uvicorn 0.54.0`, `asyncpg 0.32.0`, `sqlalchemy 2.1.4`, `alembic 1.20.0`, `pydantic 2.13.5`, `pydantic-settings 2.15.0`, `opencv-python 5.0.0.93`, `numpy 2.5.3`, `torch 2.14.1`, `structlog 26.1.0`, `prometheus-client 0.26.0`, `pytest 9.1.1`, `orjson 3.13.0`
- npm registry `dist-tags.latest` — fetched 2026-10-08 (HIGH): `react 19.3.0`, `vite 8.3.4`, `tailwindcss 4.3.3`, `echarts 6.1.0`, `recharts 3.10.1`
- GitHub releases API (HIGH): `ultralytics` v8.4.174 (2026-10-06), `roboflow/trackers` 2.6.1 (2026-09-25), `bluenviron/mediamtx` v1.21.1 (2026-09-20)
- https://supervision.roboflow.com/latest/trackers/ — `sv.ByteTrack` deprecation (0.28.0 → removal 0.31.0), `trackers` migration path (HIGH, official docs)
- https://github.com/roboflow/trackers — Apache-2.0, `supervision.Detections`-native, algorithm roster (HIGH, official repo)
- https://github.com/opencv/opencv/issues/28638 — silent RTSP frame corruption with `cv2.VideoCapture`, ffmpeg comparison (MEDIUM: single issue thread, 2026-03, but on official repo with reproducible test)
- https://stackoverflow.com/questions/76863423 — community RTSP stability answer recommending PyAV (MEDIUM, corroborates issue above)
- https://pyav.org/docs/stable/ — PyAV API/threading docs (HIGH, official)
- https://magicstack.github.io/asyncpg/current/usage.html — pool + async API (HIGH, official)
- https://www.postgresql.org/about/press/presskit18/ — PostgreSQL 18 GA 2025-09-25, AIO/uuidv7/skip-scan (HIGH, official)
- Ecosystem reference projects (2025–2026, MEDIUM — pattern corroboration, not authoritative): `kestrel` (FastAPI + ByteTrack-style + WebSockets + Next.js people/traffic analytics), `p-tracking-system` (per-camera `Queue(maxsize=1)` latest-frame-wins, Redis-optional, React 19 + Vite dashboard), `countin` (FastAPI + PostgreSQL + WebSocket occupancy hub), `vision-ai-surveillance` (FastAPI + YOLO + React RTSP counting)

---
*Stack research for: hotel people-flow analytics platform (RTSP → YOLO+ByteTrack → PostgreSQL → FastAPI → dashboard)*
*Researched: 2026-10-08*
