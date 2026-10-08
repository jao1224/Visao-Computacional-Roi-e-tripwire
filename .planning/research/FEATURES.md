# Feature Research: Hotel People-Flow Analytics (Body-Only, Analytics-Only)

**Domain:** Computer vision people counting & zone analytics for hospitality  
**Researched:** 2026-10-08  
**Confidence:** HIGH  
**Scope:** Analytics only (no face, no biometrics, no access control)

## 1. Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete for a people-flow analytics system.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Bidirectional people counting** | Standard in people counters (entrances/exits). Core KPI for traffic. | LOW | Tripwires/line crossing. Already aligned with current `main.py` + ByteTrack direction logic. |
| **Per-zone counting** | Hotels need occupancy per lobby, restaurant, pool, gym, lounge. | LOW | Use ROIs/polygons + entry/exit events per zone. |
| **Real-time occupancy** | Ops need instant view of how many people in each zone/global. | LOW | Compute from zone in/out; must be O(1) updates (no DB writes in video loop). |
| **Dwell time (per zone)** | Measures how long people stay (queue vs dining vs lingering). Critical for staffing. | MEDIUM | Requires tracking per person with zone entry/exit timestamps; handle re-entries and timeouts. |
| **Multi-camera ingest** | Hotels have multiple CFTV streams (lobby, corridors, restaurant). | MEDIUM | Parallel ingestion (threads/processes), independent pipelines, RTSP support (webcam first per PROJECT.md). |
| **Multi-object tracking (ByteTrack)** | Prevents double-counting; foundation for dwell/flow. | MEDIUM | Existing in codebase direction; must remain body-only (no face embeddings). |
| **Multi-camera tracking (MTMCT)** | Same person moving across adjacent cameras counted once in flow metrics. | HIGH | Cross-camera association by spatio-temporal constraints + body appearance features (ReID) but **only anonymous body features**. No identity linking to PII. |
| **Zone configuration (ROIs/polygons)** | Flexible per-space definitions (corridors, irregular areas). | LOW | Configurable zones/cameras in DB (schema 06). |
| **Anonymized event stream** | All metrics derived from anonymous tracklets (track_id + zone + ts). | LOW | Enforce: no frames, no crops, no face vectors stored. |
| **LGPD/privacy by design** | Non-negotiable (body-only, volatile frames). | LOW | Frames discarded after inference; no biometric processing; metrics aggregated. |
| **Access-controlled API logs (6 months)** | Marco Civil Art. 15 compliance if API exposed. | LOW | Structured logs with minimal metadata; retention policy enforced. |

## 2. Differentiators (Competitive Advantage)

Features that add value beyond commodity counters and align with hotel ops.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Heatmaps (activity/dwell-weighted)** | Visualize hot/cold zones by time of day; identify underutilized spaces. Strong for layout/staffing. | MEDIUM | Can be computed from anonymized position history (no images). Prefer dwell-weighted over raw hits for hotels. |
| **Flow between zones (origin-destination)** | See movement patterns (lobby?restaurant?pool). Helps optimize flows/staffing. | MEDIUM-HIGH | Builds on MTMCT + zone transitions; keep aggregated (counts of transitions) not individual paths exposed in UI lists. |
| **Queue analytics** | Detect queue formation (length, dwell in queue zone, wait time). High value at check-in/buffet. | MEDIUM | Special handling for queue ROIs; can alert on thresholds. |
| **Occupancy trends & time-series** | Historical view (hourly/daily/weekly) for planning (cleaning, F&B, gym peak). | LOW | Aggregated metrics in DB (`metricas_fluxo_zona` per schema 06). |
| **Alerts & thresholds** | Proactive: zone nearing capacity, unusual dwell, queue growing. Prevents overcrowding/poor experience. | MEDIUM | Rule-based (configurable per zone). Alert delivery async (email/Slack/webhook). Never log PII. |
| **Reports (scheduled/ondemand)** | Export CSV/PDF for ops/management. Audit-friendly and supports capacity planning. | MEDIUM | Aggregate-only. Include coverage (cameras/zones), time ranges, privacy note. |
| **Live dashboard (web)** | Single pane: instant occupancy, per-zone, recent trends. Adoption driver. | MEDIUM | Read-only from aggregated metrics; no access to raw video/frames. |
| **Graceful degradation** | Continue operating if one camera drops (RTSP reconnect, backpressure). | MEDIUM | Critical for multi-camera reliability. |
| **Low-latency inference path** | =5ms/frame on GPU (doc 08) with DB I/O off-video loop. | LOW-MED | Architecture already specified; implementation detail but differentiating for real-time UX. |
| **Configurable retention windows** | Per metric type (events vs aggregates). Enforce LGPD minimization. | LOW | Default minimal; aggregates kept as long as business-justified; event traces minimized. |

## 3. Anti-Features (Deliberately NOT Build)

These are commonly requested but create legal/privacy/ scope risk. Explicitly exclude for body-only analytics.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Facial recognition/identification** | Access control, loyalty, VIP recognition. | Explicitly out of scope (PROJECT.md). Violates “analytics only, zero biometrics”. High LGPD risk (Art. 11). | Body-only counting/tracking; no identity. |
| **Face embeddings/templates** | ReID across cameras “by face”. | Biometric data (sensitive). Requires legal basis beyond analytics. Not needed. | Anonymous body ReID (appearance features) with strict no-PII policy; even then treat with caution and avoid persistence of templates. |
| **Access control/turnstiles** | Hotel wants doors/locks. | Control function, not analytics. Different legal basis/UX. Out of scope. | Keep analytics-only; integration out of v1. |
| **Demographics (age/gender/race/emotion)** | Marketing insights. | Often inferred from face; even body-based classifiers can be sensitive and create profiling concerns under LGPD. | Do not estimate demographics. Focus on counts/dwell/flow only. |
| **Video recording/storage of people** | Forensics/replay. | Contradicts “frames discarded after inference”. Creates large PII surface, retention/compliance burden. | Volatile frames in RAM only; export aggregates/reports only. |
| **Snapshots/crops of people** | Debugging UI. | Persists identifiable imagery. Easy to leak. | Use bounding boxes + track IDs + metrics in UI; no image previews of individuals. |
| **Named/guest identification** | Link to PMS/booking. | Re-identifies individuals. Crosses analytics?identity boundary. | Never link tracks to guests/rooms/IDs. Strict anonymization. |
| **Cross-site tracking** | Chain hotels want global view. | Expands scope massively; identity correlation risk. | Per-site deployment with isolated data stores. |
| **Emotion/dwell “intent” inference** | Behavioral profiling. | Unreliable + ethically problematic; not necessary for hotel ops KPIs. | Stick to measurable behaviors (zone entry/exit/dwell/queue). |
| **License plate / other biometrics** | Parking integration sometimes asked. | Out of scope (body-only). Separate system with its own basis. | Exclude from v1; document as separate capability. |
| **Face blur “for storage”** | Tempting to record blurred video. | Still processing/storing derived imagery; increases attack surface; contradicts no-storage principle. | No storage at all. |
| **Real-time individual watchlists** | Security use case. | Shifts from aggregate analytics to surveillance/identification. | Explicitly out of scope; keep separation of concerns. |

## 4. Feature Dependencies

Critical for roadmap phase ordering (earlier = required by later).

```
Ingest (multi-camera, RTSP/webcam)
  +--> Tracking (ByteTrack, body-only)
       +--> Counting (bidirectional, per-zone)
       +--> Occupancy (real-time)
       +--> Dwell time (per zone)
       +--> MTMCT (cross-camera association)  [depends on stable tracks + ReID by body]
       ¦     +--> Flow/O-D (origin-destination) [depends on MTMCT]
       +--> Zone analytics (ROIs/tripwires)
       ¦     +--> Heatmaps (activity/dwell-weighted)
       ¦     +--> Queue analytics [special ROI semantics]
       +--> Event stream (anonymized)

DB schema (zones/cameras/sessions/session_traces/metricas_fluxo_zona)
  +--> Aggregates (trends/time-series)
  +--> Reports (scheduled/ondemand)
  +--> Dashboard reads (real-time + history)

Privacy/logging (LGPD + 6mo API logs)
  +--> All persisted artifacts (must be enforced globally)

Alerts/thresholds
  +--> Depends on real-time occupancy/queue metrics
```

### Dependency Notes
- **Tracking before everything analytics:** Counting/dwell/MTMCT all require stable tracklets. ByteTrack is prerequisite.
- **Zones before zone-specific features:** Dwell, tripwires, heatmaps, queue analytics require configured ROIs.
- **MTMCT is high-dependency:** Flow/O-D requires cross-camera identity consistency; MTMCT depends on tracking stability + body ReID. Can defer to later phase if needed, but listed as table stakes in spirit for multi-camera hotels.
- **DB off-video loop:** Aggregation writes must be async/batched (doc 08). Dashboard/reports depend on DB but ingestion never blocks on DB.
- **Privacy enforcement is cross-cutting:** All features must comply (no frames, no biometrics). Treat as dependency for any persistence.
- **Alerts depend on real-time metrics:** Compute from in-memory state or fast aggregates, not slow queries in hot path.

## 5. MVP Definition

### v1 - Launch (Validate concept, LGPD-compliant baseline)
Minimum to deliver hotel-relevant analytics with webcam/videos first, RTSP later.

- [ ] **Multi-camera ingest** (webcam + sample videos; RTSP planned). 
- [ ] **Body detection + ByteTrack** (no face). 
- [ ] **Bidirectional counting per zone** (tripwires + ROIs).
- [ ] **Real-time occupancy** (per zone + global).
- [ ] **Dwell time (basic)** (per zone, average/min/max). 
- [ ] **Zone configuration** (CRUD in DB).
- [ ] **Privacy by design** (frames discarded after inference; no biometric storage).
- [ ] **DB schema + aggregated metrics** (per doc 06).
- [ ] **Minimal dashboard** (occupancy + counts + dwell basics).
- [ ] **6-month API access log policy** (if API exposed).

### v1.x - Post-validation (Harden for multi-camera hotel use)
Add once core stable.

- [ ] **MTMCT (body-only)** to avoid double-counting across cameras; track flow consistency.
- [ ] **Heatmaps (dwell-weighted)** for visual insights.
- [ ] **Flow between zones (O-D)** aggregated transitions.
- [ ] **Queue analytics** (queue length, wait time, threshold alerts).
- [ ] **Alerts & thresholds** (configurable, async delivery).
- [ ] **Reports (CSV/PDF scheduled/ondemand)** aggregate-only.
- [ ] **Graceful RTSP reconnect + health checks**.
- [ ] **Retention policy enforcement** (automated cleanup by window).

### v2+ - Future (Only if justified, strict compliance)
Defer until PMF; require explicit review against LGPD.

- [ ] **Advanced MTMCT tuning** (occlusion-heavy corridors) — complexity high, value incremental.
- [ ] **Predictive occupancy** (time-series forecasting) — useful for staffing; ensure no profiling.
- [ ] **Capacity alerts with escalation** — depends on alerting maturity.
- [ ] **Multi-site aggregation** (tenant/isolation model) — increases compliance surface; avoid identity correlation.
- [ ] **Integrations (PMS/BI)** — read-only aggregates via API; no PII exchange.

## 6. Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Rationale |
|---------|------------|---------------------|----------|-----------|
| Body-only tracking (ByteTrack) | HIGH | MEDIUM | **P1** | Foundation for all analytics. |
| Bidirectional counting + zones | HIGH | LOW | **P1** | Table stakes; immediate value. |
| Real-time occupancy + dwell | HIGH | LOW-MED | **P1** | Core hotel KPIs (ops/staffing). |
| Multi-camera ingest (RTSP) | HIGH | MEDIUM | **P1** | Matches hotel CFTV reality. |
| DB schema + aggregates | HIGH | LOW | **P1** | Required for dashboard/reports; enforces structure. |
| Privacy by design + logs | HIGH | LOW | **P1** | Compliance non-negotiable. |
| Minimal dashboard | HIGH | MEDIUM | **P1** | Adoption/validation. |
| MTMCT (body-only) | HIGH | HIGH | **P2** | Prevents cross-camera double-count; important for multi-camera. |
| Heatmaps | MEDIUM-HIGH | MEDIUM | **P2** | Strong differentiator for layout decisions. |
| Flow/O-D | MEDIUM-HIGH | MEDIUM-HIGH | **P2** | Insightful but depends on MTMCT stability. |
| Queue analytics + alerts | HIGH | MEDIUM | **P2** | High hotel value (check-in/peak). |
| Reports (CSV/PDF) | MEDIUM-HIGH | MEDIUM | **P2** | Mgmt reporting/auditability. |
| Graceful degradation/reconnect | MEDIUM-HIGH | MEDIUM | **P2** | Reliability in prod. |
| Retention enforcement | MEDIUM-HIGH | LOW | **P2** | Operational compliance. |
| Predictive/forecasting | MEDIUM | HIGH | **P3** | Nice-to-have post-PMF. |
| Multi-site aggregation | LOW-MED | HIGH | **P3** | Scope expansion; defer. |

**Priority key:** P1 = must for v1; P2 = should in v1.x; P3 = future/v2+.

## 7. Competitor/Market Signals (Body-Only Context)

Signals from research (V-Count, DISPL, Verkada, Ariadne, etc.) inform positioning while keeping strict LGPD stance.

| Feature | Common in Market | Our Approach |
|---------|-------------------|--------------|
| People counting (bidirectional) | Ubiquitous (table stakes). | Body-only, 3D/depth or 2D+tracking; prioritize accuracy + privacy. |
| Occupancy/dwell/heatmaps | Common in retail analytics. | Apply to hotel zones (lobby/restaurant/pool/gym) with hotel-relevant semantics. |
| Demographics (age/gender) | Offered by some vendors (often face-based). | **Explicitly exclude.** Not needed; high privacy risk. |
| Staff exclusion | Some vendors use wearables/tags. | Optional if requested later; does not require biometrics; keep minimal. |
| Privacy-first (no face/anonymous) | Growing (GDPR-driven). | **Core differentiator:** body-only, no frames stored, analytics-only. Explicit LGPD compliance. |
| MTMCT/flow | Less common in basic counters, more in enterprise. | Implement with body-only ReID; focus on aggregated flow (not individual paths). |

## 8. Sources

- PROJECT.md (hotel analytics scope, body-only, constraints, out-of-scope) — HIGH confidence
- DOCUMENTACAO_PROJETO_E_LGPD/01_VISAO_GERAL_E_NEGOCIO_HOTEL.md (business goals: occupancy/flow/dwell/heatmaps) — HIGH confidence
- V-Count (people counting + analytics, privacy notes) — MEDIUM (market signal)
- DISPL (People Counting with Body Shape AI hybrid) — MEDIUM (body-based approach exists)
- PeopleCountings.com / Ariadne (market landscape, privacy-first) — MEDIUM
- Verkada People Analytics (feature set reference) — LOW-MED (vendor-specific)
- MarketsandMarkets People Counting report summary (market context) — MEDIUM

---
*Feature research for: Hotel people-flow analytics (body-only, LGPD-compliant). Researched: 2026-10-08.*
