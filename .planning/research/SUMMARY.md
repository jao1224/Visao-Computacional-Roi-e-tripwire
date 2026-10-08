# Project Research Summary

> **[AVISO] OVERRIDE LGPD (2026-10-08, decisao do usuario):** MTMCT, Re-ID, session_traces, sessoes, embeddings de aparencia e qualquer persistencia de track_id/session_id estao **FORA DO ESCOPO para sempre** (LGPD Art. 12, par. 2 - perfil comportamental). Ignore secoes/patterns/roadmap que mencionem rastreamento entre cameras ou trilhas individuais. Permitido apenas: associacao efemera em RAM + metricas agregadas.

**Project:** Visão Computacional para Hotelaria (Analytics de Fluxo)
**Domain:** Real-time people-counting / zone-flow analytics (RTSP → YOLO+ByteTrack → PostgreSQL → FastAPI → dashboard), body-only, LGPD-compliant
**Researched:** 2026-10-08
**Confidence:** HIGH

## Executive Summary

This is a hotel people-flow analytics platform that turns existing CCTV cameras into business sensors: bidirectional counting, per-zone occupancy, dwell time, heatmaps, and (later) cross-camera flow — all with **zero biometrics** (body-only detection, frames never persisted) to stay fully LGPD-compliant. Experts in this domain all converge on the same shape: a strict **hot loop / cold path split** where frames and inferences live only in RAM (≤ 5 ms/frame budget) and only discrete, anonymized events (`ENTROU`/`SAIU`/dwell/session) cross a batched queue into PostgreSQL. The existing `main.py` (YOLO CrowdHuman, ~320 FPS GPU) is the inference seed; everything else is new layers.

The recommended approach builds a vertical single-camera slice first (webcam/sample files → detect → ByteTrack → zone tripwire/dwell → batch upsert → FastAPI read-only → minimal dashboard), then multi-camera RTSP, then analytics depth (heatmaps, O-D flow, queues), and only then MTMCT/Re-ID. Key stack calls, all verified against registries on 2026-10-08: **Python 3.12** (hard requirement of `av` 19.x), **PyAV** instead of `cv2.VideoCapture` for RTSP (OpenCV silently corrupts RTSP frames after 15–35 s), **`trackers.ByteTrackTracker`** instead of the removed `sv.ByteTrack`, **PostgreSQL 18 + asyncpg batch writer**, **FastAPI + WebSocket**, **React 19 + Vite + ECharts**, and **MediaMTX** as a local RTSP server so the production ingestion/reconnect path is exercised from day 1 despite no DVRs being available yet.

The main risks are well-documented and all have known mitigations: (1) RTSP instability and unbounded frame queues → PyAV + drop-oldest bounded queues + staleness watchdog built in from Phase 1; (2) counting semantic failures (double counts, occupancy drift, dwell from track fragments) → count on track-ID state deltas with hysteresis, nightly occupancy reset + clamp, session-level dwell with exit timeouts; (3) LGPD leakage at debug time → enforce "no image bytes on disk" and ephemeral track/embedding lifetimes in code, gated at every phase; and (4) hotel scene physics (glass, reflections, oblique angles, occlusion at peak) → validate against manual ground truth under worst conditions once real feeds exist — accuracy cannot be judged on the webcam demo.

## Key Findings

### Recommended Stack

Full detail in [STACK.md](STACK.md). The stack is unambiguous and fully version-verified; no open version questions remain.

**Core technologies:**
- **Python 3.12 (pinned)** — hard requirement: `av` 19.x ships cp312-abi3 wheels only; adds TaskGroup/asyncio improvements
- **PyAV 19.0.1** — RTSP/FFmpeg decoding with explicit `AVERROR_*` handling and reconnect control; replaces OpenCV capture (silent corruption, blocking reads)
- **Ultralytics 8.4.x** — YOLO inference, already in `main.py`; pipeline wraps, doesn't replace
- **`trackers` (Roboflow) 2.6.x** — ByteTrack multi-object tracking; `sv.ByteTrack` is deprecated (0.28) and removed (0.31)
- **supervision 0.30.x** — `Detections` interchange container + polygon/zone helpers (never for tracking)
- **PostgreSQL 18 + asyncpg 0.32.x** — system of record (doc-06 schema exists); async pool + executemany/COPY for the batch writer
- **SQLAlchemy 2.1 async + Alembic 1.20** — ORM/query layer + migrations
- **FastAPI 0.143 + Uvicorn 0.54 + Pydantic 2.13** — REST + WebSocket push for live occupancy; middleware hook for Marco Civil access logs
- **React 19 + TypeScript + Vite 8 + Tailwind 4 + ECharts 6** — dashboard SPA (time series + heatmaps in one library)
- **MediaMTX v1.21.1** — local RTSP dev server; key enabler since no DVRs exist yet
- **Supporting:** numpy 2.5, structlog 26, prometheus-client 0.26, pydantic-settings 2.15, httpx, pytest 9 + pytest-asyncio, orjson; **no uvloop** (Windows dev host)

**Explicitly banned:** `cv2.VideoCapture` for RTSP, `sv.ByteTrack`, any DB I/O in the video loop, Celery/Redis (single-node problem), SQLite, Streamlit/Dash for production, DeepStream/Triton, frame/snapshot persistence "for debugging", uvloop on Windows.

### Expected Features

Full detail in [FEATURES.md](FEATURES.md).

**Must have (table stakes, v1):**
- Bidirectional people counting (tripwires) — core KPI
- Per-zone counting + zone/ROI configuration (polygon CRUD)
- Real-time occupancy (per zone + global), O(1) updates from zone deltas
- Dwell time per zone (basic: avg/min/max)
- Multi-camera ingest (webcam/sample videos now, RTSP later)
- Multi-object tracking (ByteTrack, body-only) — prerequisite for everything
- Anonymized event stream + LGPD privacy by design (frames discarded, no biometrics)
- PostgreSQL schema + aggregated metrics (doc 06)
- Minimal dashboard (occupancy, counts, dwell)
- 6-month API access logs (Marco Civil Art. 15, if API exposed)

**Should have (differentiators, v1.x):**
- Heatmaps (dwell-weighted, computed from anonymized position history)
- Flow between zones (origin-destination, aggregated transitions)
- Queue analytics (check-in/buffet; length, wait time, threshold alerts)
- MTMCT body-only (cross-camera de-duplication; anonymous appearance features, ephemeral)
- Occupancy trends & time-series, alerts/thresholds, CSV/PDF reports
- Graceful degradation (per-camera reconnect), configurable retention windows

**Defer (v2+):** advanced MTMCT tuning, predictive occupancy, capacity-alert escalation, multi-site aggregation, PMS/BI integrations.

**Anti-features (never build):** face recognition/identification, face embeddings, demographics, access control/turnstiles, video/frame storage, person snapshots, guest/PMS identity linking, cross-site tracking, emotion/intent inference, face blur "for storage", watchlists, license plates.

### Architecture Approach

Full detail in [ARCHITECTURE.md](ARCHITECTURE.md). The load-bearing rule every working production system obeys: **frames and inferences never leave RAM; only discrete events cross into persistence.** Two loops that must never touch: a hot loop (per-camera decode thread → latest-frame slot → shared GPU inference process with cross-camera batching → per-camera tracker → pure zone analytics → event buffer) and a cold path (async queue → 2–5 s batch upsert → PostgreSQL → FastAPI read-only → dashboard). Configuration flows the other way (dashboard → DB → pipeline reload) as the only inverted edge.

**Major components:**
1. **`ingestao/`** (FonteVideo Protocol: webcam → arquivo → RTSP) — connection, reconnect with backoff, frame freshness; owns no model knowledge
2. **`motor/`** — YOLO detector wrapper + **one ByteTrack instance per camera** + frame-to-tracks pipeline (never share tracker state across cameras)
3. **`analytics/`** — pure functions: zone polygons, tripwire with hysteresis, dwell state machine per track_id, heatmap accumulator — the only fully testable-without-GPU layer, and where counting bugs live
4. **`sessoes/`** — MTMCT last: ephemeral body Re-ID embeddings + camera-topology graph → global session_id (TTL ~15 min, RAM only, never touches disk)
5. **`persistencia/`** — doc-06 schema, idempotent batch writer (UUID `evento_id`), rollups — never called from the hot loop
6. **`api/` + `dashboard/`** — FastAPI read-only (REST + WS from in-memory live state) + Marco Civil access logs; React SPA shows freshness and per-camera health on every metric

**Key patterns:** latest-frame-wins capture (thread per camera, drop-oldest), event buffer + batch upsert, per-track_id state machines (count deltas, not per-frame detections; bottom-center anchor; tripwire hysteresis), MTMCT as an offline-tracklet consumer of stable tracks, detector/tracker as swappable registries. Flat pt-BR package layout rooted beside existing `main.py`; `nucleo/` holds CV-free contracts (event dataclasses, queues) so hot/cold boundary is testable.

### Critical Pitfalls

Full detail in [PITFALLS.md](PITFALLS.md) (12 critical pitfalls). Top 5:

1. **`cv2.VideoCapture` for RTSP** — silent frame corruption (ret=True, garbage pixels) after 15–35 s, permanent blocking on reconnect, silent death. *Avoid:* PyAV (or ffmpeg subprocess fallback) with exponential-backoff reconnect state machine, TCP transport, `last_frame_time` staleness watchdog independent of `ret`. Built in from Phase 1, never retrofitted.
2. **Unbounded frame queues → stale "real-time"** — latency creep, not crashes; dashboard shows the past. *Avoid:* bounded queues everywhere with drop-oldest + drop-rate metric + per-camera frame-age p95; measure end-to-end latency, not just inference ms.
3. **Double counting / ID switches** — count accuracy is dominated by tracking continuity, not detector accuracy. *Avoid:* sequence-based counting on track-ID state deltas (`outside→transition→inside`, dedupe per `(track_id, transition)`), debounce (track ≥ 3–5 frames before counting), tripwire hysteresis, per-camera mutually exclusive zones, tuned ByteTrack `track_buffer`.
4. **Occupancy drift** — running `entries − exits` compounds one error per hour into nonsense by night. *Avoid:* nightly reset on known-empty condition, clamp to `[0, capacity]`, re-baseline on zero-detection windows, day-boundary reconciliation alert; keep footfall vs occupancy vs dwell distinct in schema and UI.
5. **LGPD leaks "temporarily"** — debug `imwrite`, snapshot endpoints, persisted track IDs, face libs creeping into requirements. *Avoid:* enforce in code (grep-able ban on image writes outside tests, no image-writing API imported in prod), ephemeral in-frame per-camera track IDs, ephemeral RAM-only embeddings, separate retention regimes (API logs exactly 6 months vs metrics), privacy gate at every phase; exposure for biometric processing is rated up to R$ 50M / 2% revenue.

Also notable: dwell measured from track fragments (Pitfall 5 — session-level with exit timeouts), camera clock skew (Pitfall 6 — capture_ts in UTC, NTP), GPU contention from per-camera inference without batching (Pitfall 7), DB writes in the video loop (Pitfall 8 — ~4.6k rows/s per-row vs ~90k+ batched), stale-looking-live dashboards (Pitfall 9 — freshness field + health strip), hotel scene physics (Pitfall 11 — glass, reflections, oblique angles, minors near pool), and no ground truth/load test (Pitfall 12 — two independent exit gates).

## Implications for Roadmap

Based on the combined research (especially ARCHITECTURE.md's 9-step build order and PITFALLS.md's phase mapping), the suggested phase structure:

### Phase 1: Vertical slice — capture, detect, track, count (1 camera)
**Rationale:** The real uncertainty is "is the counting correct?", answerable only with a visual overlay + deterministic video fixtures — no DB or dashboard needed. Contract-level decisions (timestamps at capture, queue policy, privacy baseline, reconnect) are cheapest at inception and most expensive to retrofit.
**Delivers:** `nucleo/` + `ingestao/` (webcam/arquivo via FonteVideo Protocol) + `motor/` (YOLO wrapper + per-camera ByteTrack) + `analytics/` (tripwire + dwell as pure functions) producing events in RAM with a debug overlay; capture_ts contract (UTC); bounded drop-oldest queues; privacy-by-design baseline (no image writes).
**Addresses (FEATURES):** multi-camera-ready ingest interface (webcam first), body-only tracking, bidirectional counting, dwell state machine, zone configuration primitives.
**Avoids (PITFALLS):** #2 unbounded queues, #3 double counting (hysteresis + state deltas), #5 fragment dwell, #6 clock skew, #10 LGPD baseline. (RTSP specifics land in Phase 4 but the Protocol already anticipates them.)
**Stack:** Python 3.12, Ultralytics 8.4, `trackers` 2.6, supervision 0.30, numpy; multiprocessing spawn guards for Windows.

### Phase 2: Persistence + API + minimal dashboard (single-camera product)
**Rationale:** Doc-06 schema already exists so the cost is low; the queue-based writer cannot be retrofitted and is a prerequisite for multi-camera. API + dashboard before multi-camera delivers a verifiable pilot (1–5 cameras, YuSMP pattern) and returns the most value per effort. Occupancy reset/clamp must exist before any dashboard displays numbers.
**Delivers:** `persistencia/` (schema + idempotent batch writer, size-or-time flush), FastAPI read-only (occupancy, series, zone/camera CRUD) with WebSocket live state from RAM, Marco Civil access-log middleware, minimal React dashboard with freshness/health UI.
**Addresses (FEATURES):** DB schema + aggregates, real-time occupancy, minimal dashboard, zone CRUD, dwell basics, 6-month API logs.
**Avoids (PITFALLS):** #4 occupancy drift (reset + clamp shipped before UI), #8 DB I/O in loop (code-review gate), #9 stale dashboard (freshness field + per-camera health from day one).
**Stack:** PostgreSQL 18, asyncpg, SQLAlchemy 2.1 + Alembic, FastAPI/Uvicorn/Pydantic, React 19 + Vite + ECharts.

### Phase 3: Multi-camera + RTSP ingestion + capacity
**Rationale:** The queue and per-camera-tracker architecture is already in place from Phases 1–2, so this phase only adds capture sources and concurrency. Hotel reality is multi-camera CFTV; MediaMTX lets the exact production reconnect path be exercised before DVRs arrive. Capacity must be benchmarked on real hardware — the 320 FPS micro-benchmark does not transfer.
**Delivers:** `ingestao/rtsp.py` (PyAV, TCP, exponential backoff, staleness watchdog), thread-per-camera decode → shared GPU inference process with cross-camera batching + frame skip, per-camera tracker instances, health endpoint, 24 h soak/load test at target camera count.
**Addresses (FEATURES):** multi-camera ingest (RTSP), graceful degradation/reconnect.
**Avoids (PITFALLS):** #1 RTSP corruption/blocking (cable-pull test as gate), #7 GPU contention (decode/batch split, benchmark camera ceiling).
**Stack:** PyAV 19.0.1, MediaMTX (dev RTSP source), ffmpeg subprocess as documented fallback.

### Phase 4: Analytics depth — heatmaps, time-series, queues, alerts, reports
**Rationale:** Depends on a stable multi-stream pipeline multiplying data volume (Phase 3) and on the aggregation layer (Phase 2). All inputs (dwell-weighted position history, zone transitions, rollups) already exist; this is pure analytics + UI on top.
**Delivers:** heatmap accumulator (event-driven, no per-frame writes), pre-calculated aggregates, queue analytics per zone, configurable threshold alerts (async delivery), CSV/PDF reports, retention-window enforcement.
**Addresses (FEATURES):** heatmaps, occupancy trends, queue analytics, alerts/thresholds, reports, retention enforcement.
**Avoids (PITFALLS):** #9-adjacent trust issues (definitions on-screen), volume traps (rollups, partitioning instead of raw-event scans).

### Phase 5: MTMCT / cross-camera flow (session_id)
**Rationale:** Highest-uncertainty, lowest-impact-on-basic-counting component; every real build history ships single-camera first. Degenerate `session_id = camera_id + track_id` covers the MVP. Depends on stable tracklets from Phase 3.
**Delivers:** tracklet pipeline, ephemeral body appearance embeddings (RAM-only, TTL ~15 min, never on disk), camera-topology + temporal-restriction fusion, aggregated O-D flow metrics, advanced MTMCT evaluation.
**Addresses (FEATURES):** MTMCT body-only, flow between zones (O-D).
**Avoids (PITFALLS):** #10 (embedding persistence = profiling risk Art. 12 §2º — enforce ephemerality), Anti-Pattern 5 (MTMCT as phase 1).

### Phase 6: Production hardening + LGPD audit + hotel-scene validation
**Rationale:** LGPD is an invariant, not a phase, but the formal audit is a gate before a real hotel pilot; hotel-scene accuracy can only be assessed once real RTSP feeds exist. Two independent exit gates: accuracy report (manual ground truth, worst conditions, mean + range) AND 24 h load report.
**Delivers:** LGPD audit (no image bytes on disk, no biometric deps, track-ID lifetime, retention table vs doc 07), formal Marco Civil retention job check, manual ground-truth accuracy campaign (peak hour, glass/reflection zones, written "who counts" definition), capacity plan from load test, monitoring (prometheus, `/health`).
**Addresses (FEATURES):** validation of all P1/P2 features under production conditions.
**Avoids (PITFALLS):** #10 formal audit, #11 hotel scene physics, #12 no ground truth/load test.

### Phase Ordering Rationale

- **Tracking before analytics, analytics before DB, DB before dashboard** — dependency graph from FEATURES.md §4 and every surveyed build history; the only uncertainty that matters early is counting correctness, which needs overlay + fixtures, not infrastructure.
- **Contract-level pitfalls (timestamps, queue policy, privacy, reconnect design) land in Phase 1** — cheapest to fix at inception, most expensive to retrofit (PITFALLS ordering rationale).
- **Pilot-ready single-camera product (Phase 2) before multi-camera (Phase 3)** — verifiable value early; queue architecture prevents retrofit pain.
- **MTMCT penultimate** — maximum uncertainty, minimum effect on zone counting (which works single-camera); degenerate session_id covers MVP.
- **Privacy gates run at every phase transition**, formalized in Phase 6 — the delta between "100% conforme" and a R$ 50M biometric infraction is often a single debug line.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (RTSP/multi-camera):** environment-specific — DVR model behavior, Windows-host PyAV/codec issues, CAP_PROP property names vs pinned OpenCV if fallback is used; capacity benchmark must run on the actual GPU (Pitfalls 1, 2, 7)
- **Phase 4 (hotel-scene analytics):** tripwire geometry, debounce parameters, dwell timeouts cannot be chosen from documentation alone — needs scene footage (Pitfalls 3, 4, 5, 11)
- **Phase 5 (MTMCT):** production practice for online fusion is MEDIUM-confidence; feature-bank design and embedding choice need focused research at phase start (Pitfall 10 ressaiva)
- **Phase 6 (LGPD audit):** legal review of `session_traces` retention (movement data vs Art. 12) — legal interpretation, not technical (Pitfall 10)

Phases with standard patterns (skip research-phase):
- **Phase 2:** batch writer/rollups and freshness UI are well-documented, settled patterns
- **Phase 1 core:** threading + latest-frame-wins + ByteTrack per camera is the convergent pattern across all surveyed projects (still verify PyAV on Windows dev host early)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified directly against PyPI/npm/GitHub registries on 2026-10-08; deprecations (sv.ByteTrack) verified against official docs |
| Features | HIGH | Grounded in PROJECT.md + project docs 01–08 (primary source); market signals from multiple independent vendors corroborate; anti-features are definitive user decisions |
| Architecture | HIGH (pipeline shape) / MEDIUM (MTMCT production practice, build order) | ~12 independent production projects converge on the same shape; MTMCT evidence is peer-reviewed academically but production application is less documented |
| Pitfalls | HIGH (RTSP/OpenCV, DB batching, counting) / MEDIUM (hotel-specific, clock-sync) | Multiple independent sources incl. official OpenCV issues and measured DB benchmarks; hotel scene and NTP specifics rely on fewer/secondary sources |

**Overall confidence:** HIGH — well-researched domain with strong convergence across independent sources, a pre-existing schema (doc 06), and an existing working detector.

### Gaps to Address

- **Real DVR/RTSP behavior:** no DVRs available yet — MediaMTX + sample videos de-risk this, but codec/reconnect behavior must be re-verified when real DVRs arrive (Phase 3).
- **Hotel-scene accuracy:** published model accuracy (~84% CrowdHuman) says nothing about deployed accuracy at peak with glass/reflections/occlusion; validation requires manual ground truth on real feeds (Phase 6 gate) — the webcam demo cannot answer this.
- **Capacity ceiling:** 320 FPS is an inference-only micro-benchmark; the real camera-count ceiling is decode-bound and must be measured on the target GPU (Phase 3).
- **MTMCT production maturity:** academic evidence is strong (HIGH) but online production fusion patterns are MEDIUM — budget deeper research at Phase 5 start; degenerate session_id de-risks the MVP.
- **Legal interpretation of session_traces retention:** movement traces as closest thing to a movement profile (Art. 12 §2º) — needs legal review, not technical (Phase 6).
- **Staff exclusion:** definitional problem (staff inflate counts); decide "who counts" in writing before any manual audit; avoid building any identity database.
- **Docs 01–08 face/catraca residue:** some project docs still mention out-of-scope features — agents/devs must follow PROJECT.md scope, not the stale doc mentions.

## Sources

### Primary (HIGH confidence)
- Project docs `DOCUMENTACAO_PROJETO_E_LGPD/` 01–08 — business goals, architecture, MTMCT design, schema (doc 06), performance rules (doc 08), LGPD opinion (doc 07)
- PROJECT.md — validated scope, constraints, out-of-scope (body-only, no face)
- PyPI JSON API + npm registry + GitHub releases (fetched 2026-10-08) — all stack versions
- supervision.roboflow.com — `sv.ByteTrack` deprecation/removal; `trackers` migration path
- OpenCV issue tracker (#28638, #22677, #25889) — RTSP corruption, blocking, TCP workaround
- Official docs: PyAV, asyncpg, PostgreSQL 18 press kit, Roboflow blog/inference `time_in_zone`, Ultralytics counting docs
- MTMCT literature: LAAM (ICCV'21), ReidTrack (CVPRW'23), AI City CVPRW'24 (feature banks), Ristani & Tomasi (CVPR'18)

### Secondary (MEDIUM confidence)
- Ecosystem reference projects: sid-2672/Video-analytics-pipeline, yolo26-analytics, vision-track, cctv-home-occupancy, Ai-Retail-Footfall-Analytics (9-phase build history), kestrel, countin
- Counting accuracy sources: Ultralytics blog, Camthink, Ariadne, Vemco, Fora Soft, UMATechnology
- DB write benchmarks: willhackett.com, async-concurrency.com (~4.6k rows/s per-row vs ~90k+ batched), myDBA.dev
- NVIDIA TensorRT performance docs / forums — multi-stream batching, exec-context-per-thread
- Market signals: V-Count, DISPL, Ariadne, Verkada; EDPB Guidelines 3/2019 on video devices
- Time sync: Argus (arXiv 2401.14132), BBC R&D WHP191

### Tertiary (LOW confidence)
- The Neural Base RTSP blog — CAP_PROP naming details (partially verified against OpenCV)
- HLD occupancy Substack post — event idempotency design (pattern corroborated elsewhere)
- Markaicode FastAPI inference article — monolith throughput claim

---
*Research completed: 2026-10-08*
*Ready for roadmap: yes*
