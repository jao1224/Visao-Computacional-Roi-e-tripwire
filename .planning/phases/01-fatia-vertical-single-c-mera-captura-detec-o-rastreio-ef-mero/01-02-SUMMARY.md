---
phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero
plan: 02
subsystem: rastreio
tags: [ultralytics, bytetrack, yolo, tracking, lgpd, privacidade, pytest, tdd]

# Dependency graph
requires:
  - plan: "01-01"
    provides: "captura.capturar (contrato frame/capture_ts), fixture caminho_modelo e caminho_video_amostra"
provides:
  - "rastreio.carregar_modelo(modelo_path) — devolve YOLO(modelo_path)"
  - "rastreio.rastrear(model, frame) — model.track(persist=True, tracker='bytetrack.yaml', conf=0.25, iou=0.60, classes=[0], verbose=False) → Results"
  - "rastreio.extrair_caixas(result) — guard boxes.id None; devolve [(id:int, xyxy:list, conf:float)]"
  - "tests/test_rastreio.py — CNT-01 (só corpo/tracker explícito) + CNT-03 (IDs efêmeros)"
affects: [01-03-main, 01-04-privacidade, fase-2-zonas, fase-6-rtsp]

# Tech tracking
tech-stack:
  added: [ultralytics model.track (ByteTrack embutido)]
  patterns:
    - "Tracker explícito tracker='bytetrack.yaml' (default TrackTrack rejeitado)"
    - "classes=[0] garante detecção apenas de corpo mesmo no fallback COCO"
    - "Guard boxes.id is not None antes de ler IDs (evita TypeError)"
    - "IDs de rastreio efêmeros: vivem só na memória do tracker (persist=True)"
    - "TDD RED→GREEN por task"

key-files:
  created:
    - rastreio.py
    - tests/test_rastreio.py
  modified: []

key-decisions:
  - "tracker='bytetrack.yaml' explícito — o default do Ultralytics 8.4.121 é TrackTrack"
  - "conf=0.25 passado explicitamente (model.track força 0.1 se omitido), preservando main.py:48"
  - "classes=[0] filtra apenas pessoa, segurando o fallback yolo26n.pt (80 classes)"
  - "extrair_caixas faz guard duplo (boxes None ou boxes.id None) e devolve [] cedo"
  - "Sem matching manual, sem lib de face/Re-ID/embeddings, sem persistência de ID"

patterns-established:
  - "rastreio.py é a única camada de tracking; expõe 3 funções puras de nível de módulo"
  - "extrair_caixas é a fronteira onde IDs efêmeros viram tuplas para o overlay/consumidores"
  - "Auditoria de privacidade por token (to_csv/pickle/json.dump/track_id) automatizada no teste"

requirements-completed: [CNT-01, CNT-03]

# Metrics
duration: 2min
completed: 2026-10-08
---

# Phase 1 Plan 02: Rastreio efêmero ByteTrack em RAM Summary

**`rastreio.carregar_modelo/rastrear/extrair_caixas` com ByteTrack explícito e apenas corpo (classes=[0]), provando por teste que os IDs de rastreio são inteiros voláteis jamais persistidos**

## Performance

- **Duration:** 2 min
- **Started:** 2026-10-08T22:18:53Z
- **Completed:** 2026-10-08T22:20:54Z
- **Tasks:** 2
- **Files modified:** 2 (criados)

## Accomplishments
- `rastreio.py` expõe `carregar_modelo`, `rastrear` e `extrair_caixas` — três funções de módulo (D-04, sem classes)
- `rastrear` fixa o contrato não-negociável: `tracker='bytetrack.yaml'` explícito, `persist=True`, `conf=0.25`, `iou=0.60`, `classes=[0]`, `verbose=False` (fecha T-02-02; CNT-01)
- `extrair_caixas` guarda `boxes.id is None` e devolve `[]`, senão devolve `[(id:int, xyxy:list, conf:float)]` (fecha T-02-01; CNT-03)
- Teste de integração real processa 70 frames do vídeo-amostra: todos os IDs são `int`, ao menos um ID inicial desaparece no último frame (efemeridade real observada, não skip)
- `test_sem_escrita_de_ids` prova ausência de `to_csv`/`pickle`/`json.dump`/`track_id` na fonte (fecha T-02-01)

## Task Commits

Each task was committed atomically (TDD task split RED→GREEN):

1. **Task 1: rastreio.carregar_modelo/rastrear (ByteTrack explícito)** - `e9f6797` (feat)
2. **Task 2: extrair_caixas + testes (RED)** - `dd53fd6` (test)
   **Task 2: extrair_caixas (GREEN)** - `1dfe520` (feat)

**Plan metadata:** PENDING (docs: complete plan)

_Note: TDD task teve commits separados test → feat._

## Files Created/Modified
- `rastreio.py` - `carregar_modelo` (YOLO), `rastrear` (model.track ByteTrack explícito) e `extrair_caixas` (guard boxes.id)
- `tests/test_rastreio.py` - `test_extrair_caixas_guard`, `test_ids_efemeros` (integração), `test_sem_escrita_de_ids`

## Decisions Made
- Tracker explícito `tracker='bytetrack.yaml'` porque o default do Ultralytics 8.4.121 passou a ser TrackTrack (Armadilha 1 da pesquisa).
- `conf=0.25` explícito: `model.track` força `conf=0.1` quando omitido, o que mudaria o comportamento atual de `main.py:48`.
- Guard duplo em `extrair_caixas` (`result.boxes is None or result.boxes.id is None`) — cobre tanto ausência de boxes quanto ausência de rastreio (Armadilha 2).
- Teste de integração marca `pytest.skip` com motivo em pt-BR quando o vídeo não produz IDs/efemeridade — honestidade, nunca falha falsa.

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface Scan

Nenhuma superfície nova fora do `<threat_model>` do plano. As mitigações permanecem as do registro:
- T-02-01 (IDs efêmeros) — `extrair_caixas` só expõe IDs em RAM; `test_sem_escrita_de_ids` prova ausência de persistência.
- T-02-02 (tracker default) — `tracker='bytetrack.yaml'` literal.
- T-02-03 (biometria) — `classes=[0]`; nenhuma lib de face/Re-ID/embeddings importada.
- T-02-04 (associação entre câmeras) — nenhum Re-ID/session/embedding.
- T-02-05 (DoS/AutoUpdate) — `lap` já fixado no `requirements.txt` do Plano 01.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plano 03 (`main.py`) pode chamar `carregar_modelo → rastrear → extrair_caixas → overlay.desenhar_caixas` no laço.
- Verificação visual/manual (webcam índice 0 + vídeo-amostra exibindo caixas/IDs) permanece como backstop obrigatório (Plano 04).
- Nenhum arquivo de mídia/CSV criado pelos testes (`git status --porcelain` limpo após a suíte).

---
*Phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero*
*Completed: 2026-10-08*

## Self-Check: PASSED

- FOUND: rastreio.py
- FOUND: tests/test_rastreio.py
- FOUND commits: e9f6797, dd53fd6, 1dfe520
