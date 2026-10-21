# Domain Pitfalls Research

> **⚠️ DOCUMENTO DE PESQUISA — DATADO (2026-10-08) E PARCIALMENTE SUPERADO.**
> Preservado como **registro de referência técnica**, não como plano. Índice, mapa de validade e
> equivalências da numeração antiga: [`README.md`](README.md) (nesta pasta).
> - **Roadmap canônico:** [`../ROADMAP.md`](../ROADMAP.md) — **9 fases**. O roadmap de fases sugerido neste documento é de **6** e **não** é o plano.
> - **Vetos definitivos (mantidos):** MTMCT, Re-ID, `session_traces`/`sessoes`, embeddings de aparência e qualquer persistência de `track_id`/`session_id` estão **fora do escopo para sempre** (LGPD art. 12 §2º). Ignore as seções/patterns/fases que os mencionem. Permitido: associação efêmera em RAM + métricas agregadas.
> - **Escopo e requisitos:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · **estado:** [`../STATE.md`](../STATE.md).

**Domain:** Real-time video analytics / people counting / RTSP pipelines (hotel flow analytics, LGPD-constrained)
**Researched:** 2026-10-08
**Confidence:** MEDIUM-HIGH (HIGH on RTSP/OpenCV, DB batching and counting failure modes — multiple independent sources incl. official docs/issues; MEDIUM on hotel-specific and clock-sync specifics — fewer direct sources)

> Project context: greenfield evolution of an existing `main.py` (YOLO CrowdHuman, ~320 FPS GPU) into a 5-layer
> architecture (ingestão RTSP → YOLO+ByteTrack → sessões/filas → PostgreSQL → FastAPI/dashboard).
> Hard constraints: **no face detection at all (LGPD)**, frames never persisted, latency ≤ 5 ms/frame on GPU,
> **no DB I/O inside the video loop** (doc 08), API access logs retained 6 months (Marco Civil Art. 15).

---

## Critical Pitfalls

### Pitfall 1: `cv2.VideoCapture` RTSP treated as a reliable, non-blocking reader

**What goes wrong:**
The pipeline stalls or silently degrades within minutes of going live. Three distinct failure modes, all documented in
OpenCV's own issue tracker:
1. **Silent frame corruption** — `cap.read()` returns `ret=True` but delivers corrupted frames (bottom-left artifact,
   mean brightness collapse) after 15–35 s of continuous H.264 RTSP. No exception, no warning. Counting runs happily
   on garbage pixels.
2. **Permanent block** — `.read()` or `VideoCapture(url)` hangs indefinitely (30 s+) when the camera is unreachable or
   recovers mid-connect. Takes down the whole thread/process; `cap.isOpened()` can return `True` while `.read()` blocks forever.
3. **Silent death** — OpenCV does *not* raise on RTSP close; it returns `ret=False` once and the naive loop exits or spins.

**Why it happens:**
Developers test with webcam/file sources (`cv2.VideoCapture(0)`), which behave nothing like RTSP. H.264 is stateful —
decoder state accumulates and a dropped packet poisons subsequent frames. The code has no reconnection state machine
because the demo never needed one.

**How to avoid:**
- One `VideoCapture` object per RTSP source, owned by exactly **one** dedicated capture thread. Never share across threads.
- Reconnection state machine with **exponential backoff** (3s → 6s → 12s, cap 60s), not a fixed sleep. Release before reconnect.
- Timeouts at open: `cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MILLISEC, ...)` (note: full word `MILLISEC`, OpenCV ≥ 4.8; the
  commonly-copied `..._MSEC` does not exist and fails silently). Wrap `VideoCapture(url)` in a thread/process with a
  hard timeout for older OpenCV.
- Force `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)` right after open — otherwise OpenCV buffers frames and you process 2–25 s old data.
- Prefer TCP transport for RTSP (`OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp"`) — UDP drops packets and H.264 cannot
  recover mid-GOP. Verify ffmpeg/h264 build support once at startup via `cv2.getBuildInformation()`.
- Consider bypassing OpenCV for ingestion entirely (ffmpeg subprocess / GStreamer `appsink drop=true`) — continuous ffmpeg
  produced 0 corrupted frames where OpenCV corrupted at 15 s in the same test.
- **Health check independent of `ret`:** track `last_frame_time` per stream; if `now - last_frame_time > 1.5 * (1/fps)`,
  declare the stream dead and reconnect. A stream can be "open" and dead for minutes.

**Warning signs:**
- Counts freeze but CPU stays at 100% (spinning on `ret=False`).
- Occasional absurd detections in a burst, then normal — classic corrupted-frame windows.
- Occupancy plateaus exactly when a camera reboots.
- Latency between capture and processing grows over hours ("it was fine this morning").

**Phase to address:** Phase 1 (Ingestão RTSP) — must be built in from the first RTSP line, never retrofitted.

---

### Pitfall 2: Unbounded frame queues → processing stale video (latency creep, not crashes)

**What goes wrong:**
The system never *fails* — it quietly falls behind. OpenCV's internal buffer fills, then the app's own queue fills,
and inference runs on frames that are 5–30 seconds old. Dashboard says "tempo real" while showing the past. Under load
(queue grows faster than the GPU drains it) memory grows without bound until OOM.

**Why it happens:**
"Real-time" is assumed rather than measured. The buffer-size default is unbounded-ish, and `queue.put()` without a
`maxsize` is the path of least resistance. Teams optimize inference latency (5 ms) while ignoring *end-to-end* latency
(capture → count visible on dashboard).

**How to avoid:**
- Bounded queues everywhere (capture→inference, inference→DB writer). **Drop oldest, never newest** — stale frames are
  worthless for live analytics. Log the drop rate; a drop rate of 0 under overload is itself a bug (means you're lagging).
- Measure and store **frame age** (`time.time() - frame_capture_ts`) as a first-class metric per camera. Alert when
  p95 frame age > 1 s.
- Do not backpressure the capture thread into blocking — dropping is correct behavior for a real-time system
  (freshness > completeness).
- Separate `CAP_PROP_BUFFERSIZE=1` (camera/OpenCV side) from the app queue bound (your side). Both needed.

**Warning signs:**
- `queue.qsize()` monotonically climbing.
- Heatmap timestamps on the dashboard lag wall-clock by more than a few seconds.
- RAM growth over hours with a steady camera count.

**Phase to address:** Phase 1 (Ingestão) for the queue policy; Phase 5 (Dashboard/metrics) for the frame-age metric & alert.

---

### Pitfall 3: Double counting / ID switches — the tracker, not the detector, decides accuracy

**What goes wrong:**
The same person is counted twice (entry counted again after a brief occlusion), or a single visit is split into two
shorter visits by an ID switch — corrupting both the count and dwell-time distribution. Published detector accuracy
(~84% CrowdHuman) says **nothing** about this; count accuracy is dominated by tracking continuity, not detection.

**Why it happens:**
- Counting on *detections* instead of *track crossings* (or counting every frame a box touches the line).
- A track lost for 3 frames is dropped immediately → person re-enters as a new ID → counted again.
- A track kept alive too long → ID merges two people → undercount.
- Tripwire logic is position-based with no direction memory: someone loitering on the line oscillates and generates
  repeated crossings.
- Zones of adjacent/overlapping cameras are not mutually exclusive → same person counted by two cameras.

**How to avoid:**
- **Sequence-based zone counting**, not raw line touches: require `outside → transition → inside` for an entry, and mark
  each `(track_id, transition)` pair as already-counted so it can only fire once.
- Debounce/persistence rules: a track must exist ≥ N frames (e.g. 3–5) before it counts; hysteresis on the tripwire
  (must clear the line by X pixels before a reverse crossing is valid). *This layer — not the model — is where most
  accuracy improvement comes from (Ultralytics).*
- Tune ByteTrack `track_buffer` (lost-track keep-alive) against the actual occlusion length of the scene; the doc's
  ≤15 s tracker buffer is an upper bound, not a target.
- Count only when a track *transitions*, never when it *occupies* a line region. Track state per ID: `last_zone`,
  `crossed_flag`, `direction`.
- Define mutually exclusive zone polygons per camera; for overlapping FoVs, hand off or exclude the overlap.
- Track-ID must be scoped per camera + per session and **discarded when the person leaves the frame** (this is also an
  LGPD requirement — see Pitfall 10).

**Warning signs:**
- Manual count vs system count diverges more at peak than at quiet hours (occlusion-driven).
- Dwell-time histogram has a suspicious spike at very short durations (split visits).
- Same track ID seen entering twice without an intervening exit event.

**Phase to address:** Phase 2 (Motor de detecção/tracking + contagem por zona). Must be validated before any dashboard work.

---

### Pitfall 4: Occupancy derived as "entries − exits" drifts into nonsense over a day

**What goes wrong:**
Live occupancy starts at 0, looks plausible at 10:00, and by 22:00 reads 14 when the lobby is empty — or negative.
A *single* directional error per hour compounds for 16 hours. This is the single most common "the dashboard is wrong"
complaint in people counting, and it is a bookkeeping failure, not a model failure.

**Why it happens:**
Running sums accumulate every error with no correction term. Missed exit (occlusion) → +1 forever. Ghost track (false
positive on a reflection/mannequin) → +1 forever. Reconnection gap → both entry and exit missed → count preserved but
state may be wrong anyway.

**How to avoid:**
- **Nightly reset on a known-empty condition** (hotel zones empty after checkout/lights-out): force occupancy → 0 and
  log the correction. This is standard practice in production counters.
- Clamp occupancy to `[0, zone_capacity]` — a negative value is a bug signal, not a number to display.
- Periodic re-baseline: if a zone has had zero detections for N minutes *and* no open tracks, reconcile to 0.
- Reconcile at the day boundary: compare cumulative `entries − exits` to final occupancy; alert if the delta > threshold.
- Distinguish *footfall* (cumulative crossings), *occupancy* (current presence) and *dwell* (per-visit duration) in the
  schema and in the UI labels — they are three different measurements with different failure modes, and conflating them
  in naming ("contagem") guarantees misinterpretation.

**Warning signs:**
- Occupancy never returns to 0 overnight.
- Negative values anywhere.
- `entries - exits` at 23:59 doesn't match the closing occupancy reading.
- Two zones with wildly different in/out asymmetry (one is leaking).

**Phase to address:** Phase 2 (state model for sessions/occupancy) — the reset/clamp logic must exist before Phase 4 dashboard shows it.

---

### Pitfall 5: Dwell time measured from track fragments instead of a visit

**What goes wrong:**
Reported average dwell is far shorter than reality because one 20-minute visit became three 6-minute "visits" after
occlusions split the track — or far longer because a stale track never got an exit event and lingers for hours.
Averaging raw dwell hides this: a few multi-hour zombie tracks distort the mean badly.

**Why it happens:**
Dwell needs **track continuity**; a directional counter doesn't. Teams reuse the counting pipeline for dwell without
handling track loss, zone-exit timeouts, or the difference between "track ended" and "person left the zone".

**How to avoid:**
- Dwell = `exit_ts − entry_ts` on a *session* entity (zone_id, entry event, exit event), not on raw track lifetime.
  Bridge short track gaps: if a track dies and a new track appears within K frames near the same position/zone, treat
  as the same session (relink) rather than closing + reopening.
- Hard **zone-exit timeout**: a session with no detection for T seconds (e.g. 30–60 s) is force-closed as `incomplete`
  — flagged, not silently merged. Never leave a session open indefinitely.
- On camera disconnect/reconnect, force-close all open sessions for that camera as `incomplete` — otherwise dwell
  includes the outage.
- Report dwell as **distribution/percentiles**, plus counts of completed vs incomplete tracks. Mean alone is misleading
  (Camthink/Ultralytics both flag this).
- Define what dwell *means* operationally before measuring: a guest waiting 4 min at reception is not the same event
  as a guest sitting 4 min in the lounge. Zone semantics belong in the schema, not in a comment.

**Warning signs:**
- Dwell p99 in the hours range while max track lifetime equals camera uptime.
- High ratio of incomplete sessions.
- Average dwell drops sharply on days with heavy occlusion/event traffic.

**Phase to address:** Phase 2 (sessions/dwell logic) with reconnection interactions revisited in Phase 1 integration.

---

### Pitfall 6: Camera clock skew and frame timestamps ignored

**What goes wrong:**
Cross-zone or cross-camera metrics are subtly wrong: a guest "teleports" between zones, a dwell that spans two cameras
has negative or absurd duration, time-series from different cameras don't line up so a corridor-then-lobby journey
looks impossible. DVR/NVR clocks in hotels are frequently minutes off, and drift accumulates.

**Why it happens:**
Each stream is timestamped with `time.time()` *at processing time*, not at capture — so frame age (Pitfall 2) silently
becomes timestamp error. Different cameras are never NTP-checked. Frame *numbers* are used instead of timestamps, which
breaks the moment a stream drops frames or runs at a non-constant FPS.

**How to avoid:**
- **Timestamp every frame at capture** (`capture_ts`) and carry it through the pipeline; never re-stamp downstream.
  Use `capture_ts` for all dwell/occupancy/time-series math.
- Sync all ingestion hosts and (where the DVR allows) the cameras to NTP; monitor offset. NTP on a wired CCTV LAN
  reaches ~1 ms after convergence; research systems treat <3 ms as "synchronized". Consumer DVRs are worse — measure,
  don't assume.
- If cross-camera journeys ever matter, record per-camera clock offset and correct; treat sub-second alignment as the
  requirement, not "same day".
- Use **timestamps, not frame indices**, everywhere (variable FPS after drops is the norm, not the exception).
- Store timestamps as UTC (`timestamptz`) in PostgreSQL; convert to hotel local time only at display. DST transitions
  otherwise corrupt duration math.

**Warning signs:**
- Same event recorded at different times by two cameras by more than ~1 s.
- Duration fields that go negative.
- Time-series charts with visible gaps/overlaps at DST or after DVR restart.

**Phase to address:** Phase 1 (timestamp contract) — cheapest to fix at ingestion, expensive to fix later.

---

### Pitfall 7: GPU contention — one inference call per camera, no batching, decode on the critical path

**What goes wrong:**
Adding the 3rd or 4th camera collapses per-stream FPS. Not because the GPU is "full" — usually because the pipeline is
serialized: decode → preprocess → infer → postprocess → DB, one frame at a time, one camera at a time, in a Python
loop. GPU sits idle 70–90% of the wall clock waiting for CPU decode; Python GIL serializes the rest. Naively spawning
more threads makes it *worse* (context switching + GPU lock contention), and TensorRT multi-context without one
context+stream per thread crashes or serializes.

**Why it happens:**
The 320 FPS figure from `main.py` is a micro-benchmark of *inference only* on a pre-loaded frame. Real throughput is
decode-bound. Teams size hardware from the benchmark, then discover 8 cameras × 25 fps = 200 frames/s of *decode* they
never budgeted.

**How to avoid:**
- **Separate stages into pipelines:** thread (or process) per camera doing only decode → bounded queue → **single GPU
  consumer** that **batches frames across cameras** into one model call → fan out postprocess per stream.
- Batching across streams beats per-stream calls: batch 8–16 frames of mixed cameras per `model(batch)` call. TensorRT
  engines must be built with the intended batch (`batch=8` at export) or you get `input size not equal to max model size`.
- Decode never inline with inference; profile until the bottleneck is the GPU, not decode/IO.
- Under overload: drop frames (Pitfall 2), do not queue.
- Rule of thumb for sizing (single T4/A10, 640×640, FP16, 5–10 fps/stream): nano ~50–80 streams, small ~25–40, medium
  ~12–20. **Benchmark on the actual hardware with the real camera count before committing to a camera list.**
- If going to TensorRT: one execution context + one CUDA stream per worker thread; engine built under representative
  contention (`kWEIGHTS_ONLY`/limited-SM profiling) or runtime kernels will be suboptimal. Consider Ultralytics
  `model.track(sources=[...], stream=True)` for ≤ ~16 streams before building custom fan-out.
- Cap concurrent cameras in config with an explicit "max streams" budget, not "add a camera and hope".

**Warning signs:**
- GPU utilization low (<40%) while per-stream FPS drops as cameras are added → decode/serialization bound.
- Frame drop rate rises sharply at a specific camera count — that's your real capacity number.
- `nvidia-smi` shows memory near-full but SM utilization low → engine/buffer bloat, not compute.

**Phase to address:** Phase 1 (pipeline shape) for the decode/batch split; Phase 5 (multi-câmera/produção) for capacity benchmarking.

---

### Pitfall 8: Database writes inside (or coupled to) the video loop

**What goes wrong:**
Frame latency spikes every time Postgres has a checkpoint/autovacuum hiccup; then the video queue backs up
(Pitfall 2), then frames drop. Or: one `INSERT` per crossing event saturates the connection pool — measured ceilings
are ~4,600 rows/s for per-row writes vs ~90,000–150,000 rows/s for batched `executemany`/COPY on the same hardware.
At 3am a migration can't get a write lock because every connection is blocked on single-row INSERTs.

**Why it happens:**
The natural code is `if crossed: db.execute(INSERT...)` right where the crossing is detected. Doc 08 explicitly
forbids this, but "just one small insert" creeps back in during debugging.

**How to avoid:**
- **Rule (doc 08, non-negotiable): no DB/disk I/O inside the capture/inference loop.** Vision module emits events to
  an in-memory queue; a separate writer task drains it.
- Batch: flush on **whichever comes first — size (500–2000 rows) or time (≤ 1–5 s)**. Size-only flushing gives
  multi-second p99 latency at low event rates; the time limit must start when the *first* item of the batch arrives.
- Use `psycopg.extras.execute_values` / multi-row INSERT for upserts; plain `COPY` is fastest but can't `ON CONFLICT`
  (stage-then-merge if needed).
- Bounded writer queue with drop/oldest policy for events under overload, plus a **counter of dropped events** — losing
  a crossing event silently is worse than a late one.
- Connection pool sized as a small fraction of `max_connections`; never one connection per camera.
- Pre-aggregate for dashboards: raw events → 1-minute rollups (`metricas_fluxo_zona` style), dashboard reads rollups,
  never scans raw rows. Partition by time; drop partitions instead of `DELETE`.
- `session_traces` / per-track point trails are the highest-volume table — decide retention up front (they are the
  closest thing to a movement profile; see Pitfall 10 on Art. 12).

**Warning signs:**
- Dashboard queries slow while video is running → reads competing with writes (add rollups / replica).
- `pg_stat_activity` shows many `INSERT` waits; pool exhausted.
- Event queue depth climbing; flush reason always "size" (near ceiling) or always "time" with tiny batches.

**Phase to address:** Phase 3 (sessões/filas + PostgreSQL).

---

### Pitfall 9: Dashboard that looks live but is stale (or lies about being live)

**What goes wrong:**
Ops staff stop trusting the dashboard within a week: occupancy shown is minutes old, no one can tell, and a decision
gets made on frozen data. After a camera outage the dashboard silently shows the last known value forever. This kills
adoption faster than any accuracy problem.

**Why it happens:**
"Live" is implied by the UI (big number, spinner) but never *stated*: no data-freshness timestamp, no per-camera health,
no distinction between "current value" and "recovered from delayed data".

**How to avoid:**
- Every displayed metric carries **data freshness**: "atualizado há Xs" + source timestamp. Stale beyond threshold →
  visually distinct (grey/amber), never render an old number as current.
- Per-camera health strip: connected / reconnecting / last frame age / frames dropped in last minute. An occupancy
  number without the camera's health is uninterpretable.
- Show metric *definition* and exclusions in the UI (crossing count vs occupancy vs dwell; staff included or not) —
  a dashboard that doesn't say what it counts will be "wrong" no matter how correct it is.
- Push updates (WebSocket/SSE) from a live state store rather than polling heavy SQL; keep a fast in-memory "current
  occupancy" source of truth and let Postgres be history.
- Never show a value you can't attribute to a timestamp.

**Warning signs:**
- Users ask "is this live?" or open a second window to check.
- Values identical across two refreshes during active traffic.
- No visual difference between a healthy camera and one that reconnected 40 minutes ago.

**Phase to address:** Phase 4 (FastAPI + Dashboard).

---

### Pitfall 10: LGPD leaks introduced "temporarily" — debug snapshots, face crops, persistent track IDs

**What goes wrong:**
Compliance is decided at design time but broken at debug time. The system ships 100% body-only, then someone adds
`cv2.imwrite("debug/frame.jpg")` "just for this week", a bounding-box overlay video gets committed to a folder, an
exception handler dumps the offending frame to disk, a test writes detections to a CSV with a track_id column that
later gets joined across days — and the project is now processing personal data (arguably sensitive biometric data if
any face crop/embedding exists) with no legal basis. Doc 07 rates biometric processing without consent as **INFRAÇÃO
GRAVE, até R$ 50M / 2% faturamento**; body-only analytics is rated 100% conforme. The delta between those two rows is
often a single debug line.

**Why it happens:**
Privacy rules are written in docs 07/08 but not enforced in code. Frame persistence is the default debugging tool for
CV engineers. Also: the repo docs still mention face/catraca in places (PROJECT.md Context) — an agent or new dev
"restoring" a removed feature is a live risk.

**How to avoid:**
- **Enforce in code, not in policy:** frames live only in RAM, are dropped after inference, and there is *no* code path
  that writes image bytes to disk. Grep-able ban: no `imwrite`/`imsave`/`tofile`/`pickle(frame)` outside tests that
  never run against real streams. Consider a startup assertion that no image-writing API is imported in production mode.
- If a diagnostic capture is ever truly needed (incident review), it must be an explicit, off-by-default, TTL-purged
  feature with faces/body areas handled per doc 07 — **not** a debug print. Default OFF.
- **Track IDs are ephemeral**: valid only while the person is in frame, scoped per camera, never persisted beyond the
  visit, never reused to re-identify across days or cameras. Persisting anonymous track traces is fine *as metrics*;
  persisting an identity-like sequence that reconstructs one person's route is `Art. 12 §2º` profiling territory.
- No face detection, no embeddings, no age/gender from faces — scope decision is definitive (PROJECT.md Out of Scope).
  Any library call that enables it (Ultralytics face models, RetinaFace, InsightFace) must not be in `requirements.txt`.
- Watch for *accidental* faces: they will appear in frames regardless — the mitigation is that frames are never stored,
  so a face in a transient frame is not "processing for identification". What matters: no persistence, no biometric
  extraction, no cross-day linkage.
- Data-flow diagram in the repo showing "video in → metrics out, nothing to disk" (doc 08/EDPB practice) and a
  retention table (doc 07 §4) checked at each phase gate.
- API access logs: IP/port/timestamp retained exactly 6 months under sigilo (Marco Civil Art. 15) — a *separate*
  retention regime from metrics; don't mix them into one "logs" table with one TTL.
- Pool/lazer cameras capture minors (doc 07 Art. 14): body-only + no persistence is what keeps these zones legal.
  Treat any future feature touching those zones as requiring re-review.

**Warning signs:**
- Any `*.jpg`/`*.png`/`*.mp4` appearing under the app's working directory in production.
- Disk usage growing on the inference host.
- A `track_id` column in a table with a retention period longer than the visit.
- Someone adds a "snapshot for evidence" endpoint without an off-by-default TTL.
- `requirements.txt` growing a face/biometrics library.

**Phase to address:** Phase 1 (privacy-by-design baseline) and re-audited at every phase gate; Phase 6 (LGPD/auditoria) for the formal check.

---

### Pitfall 11: Hotel scene physics — glass, backlight, reflections, low light, and the pool/deck trap

**What goes wrong:**
Accuracy measured on a webcam demo collapses in the lobby. Specific hotel failure modes:
- **Glass entrances & revolving doors** at sunrise/sunset → backlit silhouettes, WDR needed; reflective marble/polished
  floors create phantom "people" (mirror detections above the floor) that inflate counts and ghost-occupancy.
- **Deliberately dim bars/lounges/atriums** → detection recall drops exactly where dwell analytics matter most.
- **Oblique camera angles** — security cameras are angled to see *faces and wide areas*, which is the *worst geometry for
  counting* (people stack behind each other). This is the #1 reason repurposed-CCTV counts disappoint.
- **Occlusion at peak**: luggage, trolleys, groups walking abreast, tailgating — undercount grows with density, i.e.
  exactly when the number matters (families/groups are the classic collapse: 3 people = 1 detection).
- **Pool / deck / terrace**: outdoor light swings, humidity on housings, glare off water, plus minors in frame (doc 07
  Art. 14) — the highest-scrutiny zone with the hardest imaging conditions.
- **Staff contamination**: reception, cleaners, F&B staff crossing zones all day inflate guest counts and corrupt any
  derived metric (conversion/utilization) — a *definition* problem, not a sensing one.

**Why it happens:**
Validation is done on convenient clips (quiet, well-lit, single-file) and on the model's published accuracy, not on the
deployed scene. Published "98%+" figures come from lab conditions with entry width, density, lighting and group mix
held favorable; real peak-hour accuracy is routinely 88–95%.

**How to avoid:**
- **Overhead or near-overhead mounting beats model choice.** Where a camera can't be moved (existing security CCTV),
  expect lower accuracy at entrances and compensate with geometry (zone polygons + trajectory history) rather than
  hoping the model fixes it. Add one overhead camera at a hard entrance rather than tuning against a bad angle.
- Validate against **manual ground truth under worst conditions**: busiest hour, worst lighting, widest entrance,
  groups of 3, someone standing on the line. Two independent human counters, 15-minute buckets, ≥ 300 in/out events,
  report mean **and range** — not a single flattering number.
- Re-validate after **any** camera move, refit, seasonal decoration, or new furniture in the detection zone. Accuracy
  drifts; it is a maintenance discipline, not a one-time acceptance test.
- Define "who counts" in writing before comparing to a manual audit: staff, cleaners, deliveries, children, passers-by,
  people who pause at the threshold. Disagreement here is usually definitional.
- Anti-ghost measures for reflective floors: minimum detection height / ROI floor polygon that excludes mirrored area;
  confidence threshold per zone; ignore detections below a size/aspect sanity bound.
- For staff exclusion: either a definition-based exclusion (staff zones/hours), or exclude tracks whose recurring
  pattern marks them as staff — **without building an identity database** (aggregate only, no per-person record).
- Hard-cap occupancy per zone to the physical/legal capacity — pool and breakfast areas need this as a safety signal.

**Warning signs:**
- Manual vs system gap much larger at peak than at quiet hours.
- Count drops sharply at specific times of day (sun angle through glass).
- Non-zero occupancy at 04:00 in a closed zone (reflections/ghosts).
- Detections that mirror real people above the floor line.

**Phase to address:** Phase 2 (contagem por zona) for geometry/ROI rules; validation protocol in Phase 5 (produção/RTSP real) — note development starts on webcam/sample video, so hotel-scene accuracy **cannot** be assessed until real RTSP feeds arrive.

---

### Pitfall 12: No ground truth, no load test — "it works" proven on the wrong conditions

**What goes wrong:**
The demo is validated on a 2-minute clip at midday. Production runs 16 cameras at 02:00 with a refrigeration
compressor vibration, one camera on Wi-Fi, and a wedding party in the lobby. Two separate untested assumptions —
*accuracy* and *capacity* — fail simultaneously, and nobody can tell which number is wrong.

**Why it happens:**
Inference FPS (320) is measured; end-to-end behavior under full stream load is not. Accuracy is measured against the
model's benchmark instead of manual counts. Testing uses the same clip used for development (confirmation loop).

**How to avoid:**
- Two independent acceptance tests, both required:
  1. **Accuracy test:** manual ground truth at worst conditions (Pitfall 11 protocol), per direction, per 15-min bucket.
  2. **Load test:** all cameras connected simultaneously, measure per-stream FPS, drop rate, frame age p95, GPU/CPU/RAM,
     DB writer queue depth, dashboard freshness — over ≥ 24 h (to catch leak/accumulation effects and nightly reset).
- Test the failure paths deliberately: pull a network cable mid-count, restart a camera, kill the DB for 30 s, fill
  the disk — and verify recovery *and* that counts reconcile afterward (sessions force-closed, occupancy reset).
- Keep a small library of real recorded sample clips **only for development** with an explicit retention/expiry — never
  let "we need test footage" become a permanent frame store (Pitfall 10).
- Ship a `/health` + per-camera status endpoint early; you cannot fix what you cannot observe.

**Warning signs:**
- No test ever exercised a disconnect.
- Accuracy claims cite the model datasheet, not a manual count from *this* hotel.
- Memory/RAM only ever measured during a 5-minute demo.

**Phase to address:** Phase 5 (produção/multi-câmera) as a gate; test harness built starting Phase 1.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reconnect with fixed `sleep(5)` | Few lines of code | Thunders on NVRs after outages; slow recovery; no jitter | Only in dev against local files |
| `cv2.imwrite` debug frames behind a flag "we'll remove later" | Fast debugging | LGPD exposure; the flag ships | **Never on real streams** — log metadata (box coords, conf, frame age) instead |
| Per-frame `INSERT` of session traces | Simple code | Write ceiling ~4.6k rows/s; pool exhaustion; WAL pressure | Only for unit tests |
| One thread + one `model()` call per camera | Easy to reason about | GPU idle; camera count ceiling ~3–4 | Only ≤ 2 cameras, prototype |
| Occupancy = running `entries − exits` with no reset | Ship today | Silent drift; ops loses trust | Acceptable **only** with nightly reset + clamp shipped in the same PR |
| Frame numbers instead of timestamps | Simpler schema | Breaks on any drop/FPS change; dwell math wrong | **Never** |
| Persist track_id for "future analytics" | Deferred design decision | Cross-day linkage = profiling risk (Art. 12 §2º); needs deletion machinery | **Never** without a written legal basis |
| Dashboard polls `SUM()` over raw event table | No new components | Query time grows unbounded; stale-feeling UI | MVP only, with rollups scheduled next |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **RTSP / DVR (Hikvision etc.)** | Using UDP (default in some builds); dropped RTP → corrupted H.264 that never recovers | Force TCP (`rtsp_transport=tcp`); backoff reconnect; verify with ffmpeg on the same URL before blaming the app |
| **`cv2.VideoCapture`** | Assuming `isOpened()`/`ret` are truthful | Independent staleness watchdog on `last_frame_time`; corrupted-frame detection (frame stats) if staying on OpenCV |
| **Ultralytics YOLO / TensorRT** | Exporting engine with `batch=1` then feeding multi-camera batches | Export with target batch; one exec context + stream per worker; benchmark under contention |
| **ByteTrack (`model.track`)** | Reusing one `persist=True` tracker state across cameras / never resetting on reconnect | Per-camera tracker state; reset tracks on reconnect; force-close open sessions |
| **PostgreSQL** | Writing from the inference thread; single shared connection | Bounded async writer + batched `execute_values`; pool ≪ `max_connections`; time-partitioned tables |
| **FastAPI** | Running inference inside request handlers / returning un-timestamped state | Read-only API over pre-aggregated rollups + in-memory live state; every payload carries `observed_at` |
| **Dashboard (WebSocket/SSE)** | Assuming push means "live" | Explicit freshness field + camera health; stale styling |
| **Host clock / NTP** | Trusting DVR and app clocks to agree | Monitor offset per source; UTC everywhere in DB; timestamps taken at capture |
| **`requirements.txt`** | Letting a convenience library pull face/biometrics deps | Lock file + review; ban face/embedding packages (scope is definitive) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Decode inline with inference | GPU < 40% util, FPS collapses at camera #3 | Thread-per-camera decode → bounded queue → batched GPU consumer | ~2–4 cameras at 1080p on one box |
| Per-row DB inserts | Latency spikes, pool saturation, migration lock waits | Batch 500–2000 rows or COPY; flush on size **or** time | ~thousands of events/s (measured 4.6k rows/s ceiling) |
| Unbounded queues | RAM creep, latency creep, "live" data seconds old | `maxsize` + drop-oldest + drop-rate metric + frame-age p95 | Any sustained overload |
| Dashboard `SUM` over raw traces | Query p95 climbs weekly as table grows | 1-minute rollups + materialized views; partition & drop | Days–weeks of trace data |
| One process holding all cameras | A single crash takes every stream down | Isolate capture per camera (process for hard RTSP hangs); supervisor restart | Any long-running deployment |
| Building TensorRT engine on idle GPU | Runtime slower than PyTorch at scale | Profile under representative contention; or start with PyTorch/FP16 and measure | Multi-stream production |
| No retention on `session_traces` | Table growth, slowdown, legal exposure | Time partitioning + documented TTL | Weeks–months |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| RTSP credentials hardcoded in config/repo (`rtsp://user:pass@host`) | Credential leak; lateral movement into camera network | Env vars/secret store; URL-encode special chars in password (a `#` or `@` silently breaks auth) |
| FastAPI exposed without access-log retention | Marco Civil Art. 15 violation (6 months, under sigilo) | Middleware logging IP/port/timestamp from day one + scheduled purge at exactly 180 days |
| Frames/snapshots in error handlers, backups, or email notifications | LGPD breach — images of guests leaving the governance boundary; email attachments are a classic uncontrolled export | No image bytes anywhere outside RAM; audit outbound notifications; never attach frames to alerts |
| Debug/admin endpoints left on in production | Unauthenticated view of live analytics (and temptation to capture frames) | Auth on all state-changing/read endpoints; audit log of who viewed what |
| Log tables mixing access logs and metrics with one TTL | Either Art. 15 violation or over-retention of metrics | Separate retention regimes per doc 07 §4 |
| Cross-day/cross-camera track persistence | De facto profiling of individuals (LGPD Art. 12 §2º) | Track lifetime = in-frame only; aggregates only at rest |
| Test recordings kept indefinitely "for tuning" | Personal data with no basis/retention limit | Explicit, dated, expiring sample library; prefer synthetic/consented footage |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Big number with no timestamp/freshness | Staff can't tell live from frozen → stop trusting it | `atualizado há Xs` + stale styling + per-camera health |
| Showing "Contagem" without saying *which* count | Footfall vs occupancy vs dwell conflated → "the dashboard is wrong" arguments | Label definitions on-screen; separate cards per metric |
| Dwell shown as a single average | A few zombie tracks distort the mean; ops misreads | Percentiles + distribution + completed/incomplete split |
| Heatmap with no date/time filter or time zone | Guests' privacy-sensitive data viewed casually; wrong day compared | Default to aggregate windows; access logging for detail views |
| No indication of camera offline during outage | Ops makes decisions on hours-old data | Distinct offline state; alarm on `last_frame_age` |
| Occupancy without capacity context | Pool/breakfast zone overcrowding not actionable | Show occupancy vs configured capacity with threshold states |
| Raw event log as the main view | Overwhelming; invites identifying individuals | Default to aggregates; raw events behind role + audit |

## "Looks Done But Isn't" Checklist

- [ ] **RTSP reconnection:** tested by *pulling the cable* mid-count — do sessions force-close, occupancy reconcile, and streams return with backoff? (Common miss: reconnect works, but open sessions hang forever → dwell poisoned.)
- [ ] **Frame freshness:** is frame age measured and displayed? A pipeline with `ret=True` can still be 20 s behind (or feeding corrupted frames).
- [ ] **Occupancy reset:** does it return to 0 nightly and clamp at 0/capacity? Negative occupancy is a bug you haven't seen yet.
- [ ] **Double-count guard:** person loitering *on* the tripwire for 30 s — how many entries counted? (Answer must be 0 or 1, deterministically.)
- [ ] **ID-switch tolerance:** two people crossing abreast, one occluded for ~1 s — one visit or two in the dwell report?
- [ ] **Batch flush under trickle:** at 10 events/min, does the flush time-limit fire (not wait for 500 rows)? p99 write latency should stay sub-second.
- [ ] **Dashboard under DB restart:** does it show "stale/offline" or silently keep the last number?
- [ ] **No image bytes on disk:** `find <appdir> -name "*.jpg" -o -name "*.mp4"` in production returns nothing; no `imwrite` in prod code paths.
- [ ] **No face/biometrics deps:** `pipdeptree` / `requirements.txt` review — no face detection, embedding, or re-ID packages.
- [ ] **Track ID lifetime:** confirmed ephemeral (in-frame, per-camera, per-visit) — no table persists an identity across visits.
- [ ] **Load test at full camera count:** 24 h run with per-stream FPS, drop rate, frame age p95, RAM, DB queue depth all recorded.
- [ ] **Timestamps at capture:** DB durations computed from `capture_ts` (UTC), not processing time or frame index.
- [ ] **Marco Civil logs:** API access log exists with 6-month retention job — and it is *separate* from metrics retention.
- [ ] **Manual ground truth** exists for at least one hard entrance at peak hour, with a written "who counts" definition.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| RTSP instability discovered in production | MEDIUM | Add staleness watchdog + backoff state machine (hot-reloadable config); if OpenCV is the culprit, move ingest to ffmpeg/GStreamer subprocess behind the same frame-queue interface |
| Counting drift already in historical data | HIGH | Cannot reconstruct truth without video (which we don't store — by design). Mark affected day ranges as suspect in BI, apply nightly-reset going forward, re-baseline; treat as a lesson, not a fix |
| Dwell poisoned by zombie sessions | MEDIUM | Force-close sessions older than `max_zone_dwell` as `incomplete`; add exit timeout; recompute distributions excluding incompletes |
| Frame images found on disk | HIGH (legal) | Delete immediately, audit every code path that wrote them, document incident + remediation, re-run privacy gate before next phase |
| DB write bottleneck in production | MEDIUM | Introduce/size the batch writer (buffer + size/time flush), add rollups, partition tables; pause heavy dashboard queries to a replica |
| Camera clock skew detected | LOW–MEDIUM | NTP all sources, backfill a per-camera offset column, recompute affected durations; switch any frame-index math to timestamps |
| Dashboard trust lost with ops users | MEDIUM | Ship freshness + health UI first (visible trust signal), publish metric definitions, then re-validate numbers with a joint manual count |

## Pitfall-to-Phase Mapping

> Phases below are *proposals* for the roadmap (none exist yet); they follow the doc-02 five-layer architecture.

| # | Pitfall | Prevention Phase | Verification |
|---|---------|------------------|--------------|
| 1 | RTSP block/corruption/silent death | **Phase 1 — Ingestão RTSP** | Cable-pull test; `last_frame_age` alarm; >24 h soak with 0 unrecovered outages |
| 2 | Unbounded queues / stale frames | **Phase 1** (+ metric in Phase 4) | Frame-age p95 < 1 s under load; drop-rate metric exists and is non-zero under overload |
| 3 | Double counts / ID switches | **Phase 2 — Motor YOLO+ByteTrack + zonas** | Loiter-on-line test = 0/1 counts; manual count at peak within agreed tolerance |
| 4 | Occupancy drift | **Phase 2** (state model) | Occupancy → 0 nightly; never negative; day-boundary reconciliation alert |
| 5 | Dwell from track fragments | **Phase 2** | Incomplete-track ratio tracked; zombie sessions impossible (exit timeout); p95 dwell plausible vs observation |
| 6 | Clock skew / timestamps | **Phase 1** (timestamp contract), re-checked Phase 3 | All DB timestamps UTC from `capture_ts`; NTP offset monitored; no negative durations |
| 7 | GPU contention / no batching | **Phase 1** (pipeline shape), **Phase 5 — Produção/multi-câmera** (capacity) | Benchmarked camera-count ceiling on real hardware; GPU util high while decode not blocking |
| 8 | DB writes in video loop | **Phase 3 — Sessões/filas + PostgreSQL** | Code review gate (no I/O in loop); batch flush p99; pool utilization stable under load |
| 9 | Dashboard staleness | **Phase 4 — FastAPI + Dashboard** | Freshness field on every metric; stale/offline states; DB-restart drill |
| 10 | LGPD leaks (frames/faces/track IDs) | **Phase 1** baseline, gate at **every** phase; formal audit Phase 6 | No image files on disk; no biometric deps; track-ID lifetime test; retention table matches doc 07 §4 |
| 11 | Hotel scene physics (glass/light/occlusion/pool) | **Phase 2** (ROI/geometry) + **Phase 5** (validation on real RTSP) | Manual ground truth at worst conditions; ghost-occupancy = 0 at night |
| 12 | No ground truth / no load test | **Phase 5** as exit gate | Accuracy report (mean + range) AND 24 h load report both exist |

**Ordering rationale for the roadmap:** Pitfalls 1, 2, 6, 10 are *contract-level* (timestamps, queue policy, privacy,
reconnection) — cheapest to fix at inception, most expensive to retrofit, so they must land in the ingestion phase.
Pitfalls 3, 4, 5 are the *semantic core* — they define whether the numbers mean anything, so they gate dashboard work
(Pitfall 9's dashboard must never be built on unvalidated counting). Pitfalls 8 and 7 belong to their respective
layers (DB, multi-camera) and are the classic "works with one camera, dies at eight" failures — hence a dedicated
capacity/validation phase before production.

**Research flags for phases:**
- **Phase 1 (Ingestão):** deeper research likely needed — OpenCV vs ffmpeg/GStreamer ingestion choice is
  environment-specific (DVR model, Windows host); verify `CAP_PROP_*` timeout property names against the pinned OpenCV
  version. *(Pitfalls 1, 2, 6)*
- **Phase 2 (Contagem/zonas):** needs scene-specific research once real camera footage exists — tripwire geometry,
  debounce parameters, and dwell timeouts cannot be chosen from documentation alone. *(Pitfalls 3, 4, 5, 11)*
- **Phase 5 (Produção/multi-câmera):** needs a capacity benchmark on the actual GPU + real DVRs; the 320 FPS figure
  does not transfer. *(Pitfalls 7, 11, 12)*
- **Phase 6 (LGPD/auditoria):** legal review of `session_traces` retention (movement data vs Art. 12) — legal
  interpretation, not a technical question. *(Pitfall 10)*
- Standard patterns, unlikely to need research: Phase 3 batching/rollups (well-documented), Phase 4 freshness UI
  (pattern is settled).

## Sources

**RTSP / OpenCV (HIGH confidence — official issue tracker + multiple independent sources):**
- OpenCV issue #28638 — silent corrupted frames from persistent RTSP VideoCapture, 15–35 s; ffmpeg continuous = 0 corrupted — https://github.com/opencv/opencv/issues/28638
- OpenCV issue #22677 — `VideoCapture.read()` permanently stuck after camera reconnect — https://github.com/opencv/opencv/issues/22677
- OpenCV issue #25889 — RTSP stops after 5–10 min; H.264 decode errors; `-rtsp_transport tcp` workaround — https://github.com/opencv/opencv/issues/25889
- OpenCV forum — frame drops scaling with RTSP stream count (profiling/CPU-bound) — https://forum.opencv.org/t/frame-drops-when-increasing-the-number-of-rtsp-streams/18292
- The Neural Base — RTSP handling: `CAP_PROP_OPEN_TIMEOUT_MILLISEC` naming, `CAP_PROP_BUFFERSIZE=1`, frame-queue drop-oldest, backoff — https://theneuralbase.com/opencv/learn/advanced/rtsp-handling-for-streams/ (MEDIUM — secondary source, claims verified against OpenCV property naming where possible)
- Ultralytics issue #6351 — RTSP recapture/timeout behavior — https://github.com/ultralytics/ultralytics/issues/6351

**Multi-stream / GPU (HIGH for batching guidance — NVIDIA official docs; MEDIUM for stream-count heuristics):**
- NVIDIA TensorRT Performance docs — multi-streaming, contention, limiting compute resources at build — https://docs.nvidia.com/deeplearning/tensorrt/latest/performance/optimization.html
- Ultralytics Academy — Multi-Stream Inference: decode/batch architecture, drop-don't-queue, per-GPU stream sizing heuristics — https://academy.ultralytics.com/courses/yolo-in-production/multi-stream-inference (MEDIUM — vendor course, numbers explicitly "benchmark on real hardware")
- NVIDIA forums — batch vs streams trade-off; one exec context + one CUDA stream per thread — https://forums.developer.nvidia.com/t/batching-vs-cuda-streams-for-concurrent-inferences/119511/1
- Ultralytics issue #7135 — TensorRT engine batch size must match multi-stream batch — https://github.com/ultralytics/ultralytics/issues/7135

**Counting accuracy / dwell / occupancy (MEDIUM-HIGH — multiple independent 2026 sources agreeing):**
- Ultralytics — People Counting and Occupancy Analytics Methods: four different measurements, entries−exits drift, persistence/debounce is where accuracy comes from, overhead vs oblique angle — https://www.ultralytics.com/blog/people-counting-occupancy-analytics
- Camthink — People counting vs occupancy vs dwell; track loss splits visits; report distributions not means; scene/subgroup bias — https://www.camthink.ai/blog/people-counting-occupancy-dwell-time/
- Ariadne — vendor-neutral 4-hour accuracy test: peak-hour collapse, group dilution, bidirectional drift, 15-min buckets, report interval not point — https://www.ariadne.inc/resources/blogs/people-counter-accuracy-test-methodology/ and /people-counting-occlusion-and-tailgating/
- Vemco — accuracy as maintenance discipline; re-validation after refit; net-error masking — https://vemcogroup.com/en/blog/the-ultimate-guide-to-people-counting-accuracy-2027
- Fora Soft — occupancy drift + nightly reset/sanity bounds; 2D vs 3D mounting effects — https://www.forasoft.com/blog/article/people-counting-software
- UMATechnology — zone/sequence counting, per-ID crossing dedup, occupancy clamping, ID-switch metrics — https://umatechnology.org/people-counting-and-tracking-project-using-deep-learning/

**DB write path (HIGH — measured benchmarks, multiple independent):**
- Will Hackett — 67k events/s into Postgres: naive INSERT plateau ~14k, batch ~34k, COPY ~67k; connection pool/lock starvation at 3am — https://willhackett.com/just-use-postgres/
- async-concurrency.com — measured 4,614 rows/s per-row vs 88k–152k batched/COPY; time-limit must start at first item; losing open batch on cancel — https://async-concurrency.com/concurrent-execution-worker-patterns/async-data-pipelines/batching-database-writes-in-async-pipelines/
- Dhameliya — buffer → batch → rollup pattern for metrics on Postgres — https://dcdhameliya.com/blog/designing-a-simple-metrics-collection-service
- myDBA.dev — single-row INSERT loop vs batch vs COPY throughput table; chunk/partition guidance — https://mydba.dev/blog/timescaledb-insert-performance (MEDIUM — TimescaleDB-flavored, plain-Postgres guidance transfers)

**Time sync (MEDIUM):**
- Argus (arXiv 2401.14132) — NTP-synced cross-camera association, <3 ms threshold on wired CCTV LAN — https://arxiv.org/pdf/2401.14132v2.pdf
- RocSync — clock offset + drift model; consumer cameras drift measurably within 60–90 min of sync — https://exa.ai/library/publication/m51p1zr4qky (MEDIUM — academic)
- BBC R&D WHP191 — NTP vs PTP convergence (1 ms after 24 h vs 25 µs after 30 min); per-frame capture timestamps carried end-to-end — http://downloads.bbc.co.uk/rd/pubs/whp/whp-pdf-files/WHP191.pdf

**LGPD / GDPR privacy-by-design (HIGH for project-specific rules — docs 07/08 are primary; MEDIUM for general GDPR framing):**
- Project doc 07 — retention table (frames = 0 s, tracker buffer ≤ 15 s, API logs exactly 6 months, metrics permanent/anonymized); Art. 11/12/14 analysis; R$ 50M exposure for biometric processing — `DOCUMENTACAO_PROJETO_E_LGPD/07_PARECER_COMPLETO_LGPD_E_MARCO_CIVIL.md`
- Project doc 08 — no I/O in video loop; body-only detection; privacy-by-design rules — `DOCUMENTACAO_PROJETO_E_LGPD/08_PROMPT_E_DIRETRIZES_PARA_AGENTE_IA.md`
- EDPB Guidelines 3/2019 on video devices — necessity, black-box vs realtime, disable unnecessary functions, DPIA triggers — https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201903_video_devices_en.pdf
- Fora Soft — common mistake: enabling face recognition because the camera ships the toggle; privacy as launch-week task; no image persistence; frames in notifications/emails leave governance — https://www.forasoft.com/learn/video-surveillance/articles-vms/privacy-by-design-for-surveillance (MEDIUM)
- Abdulaziz Akyol — production practice: in-memory processing, discard frames, aggregates only, track ID valid only in-frame — https://www.abdulazizakyol.com/en/blog/gdpr-and-video-analytics-without-face-recognition/ (MEDIUM)
- Milestone XProtect GDPR appendix — snapshot/AVI email notifications as uncontrolled export; retention settings — https://doc.milestonesys.com/2025r2/en-US/quick_guides/gdprprivacyguide/gdpr_appendixthexprvmssystemandgdpr.htm (MEDIUM)

**Hotel-specific (MEDIUM — vendor content, but consistent across independent vendors):**
- Ariadne — hotel lobby foot traffic; camera-facing-guests sensitivity; honest framing of estimates — https://www.ariadne.inc/resources/blogs/hotel-lobby-foot-traffic/
- V-Count — hotel scene awkwardness: glass/revolving entrances, atriums, dim lounges, pool decks/terraces, outdoor zones — https://v-count.com/industries/hotels/
- iFovea — camera placement beats resolution; overhead > side-view; WDR for backlit entrances; min 2MP — https://www.ifovea.com/people-counting-video-analytics/
- Retail Sensing — technology accuracy comparison table (video 95–99%, IR beam 85–95% real-world) — https://retailsensing.com/video-analytics/best-people-counting-system/

---
*Pitfalls research for: real-time video analytics / people counting (hotel, LGPD-constrained)*
*Researched: 2026-10-08*
