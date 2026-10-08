---
phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero
plan: 04
subsystem: verificacao-privacidade-integracao
tags: [privacy, integration, tdd, checkpoint-pending]
dependency_graph:
  requires:
    - 01
    - 02
    - 03
  provides:
    - tests_privacidade
    - tests_integracao
  affects:
    - tests
tech-stack:
  added:
    - pytest
  patterns:
    - disk-snapshot-audit
    - token-prohibition-scan
    - ephemeral-tracking-assertions
key-files:
  created:
    - tests/test_privacidade.py
    - tests/test_integracao.py
  modified: []
decisions:
  - decision: enforced disk-write prohibition with before/after media snapshot
    rationale: ING-03 requires proving no new media files created during pipeline
    impact: test_sem_escrita_em_disco fails if any media is created
metrics:
  duration: pending
  completed_date: "2026-10-08T22:47:59Z"
  tasks_completed: 2
  tasks_total: 3
  files_created: 2
  files_modified: 0
  tests_passed: 6
  tests_total: 6
---

# Phase 01 Plan 04: Verificação de Privacidade, Integração e Gate Visual

> Sumário parcial: Tasks 1 e 2 executadas e commitadas. Task 3 (verificação visual humana) permanece pendente como checkpoint:human-verify (gate=blocking).

## Objective

Provar de forma automatizada os invariantes de privacidade e a efemeridade dos IDs (auditoria de disco + varredura de face/biometria + pipeline headless), deixando a verificação visual como gate humano.

## Completed Tasks

### Task 1: tests/test_privacidade.py — nada em disco (ING-03) e sem face/biometria (CNT-01)
- **Type:** auto, tdd=true
- **Status:** completed
- **Commit:** 04f06b0
- **Files:** tests/test_privacidade.py (created)

**Tests implemented:**
1. `test_sem_modulos_de_face` — Varredura case-insensitive dos tokens proibidos ('face', 'biometr', 'demograf', 'insightface', 'facenet', 'retinaface', 'arcface', 'deepface', 'cv2.face', 'imwrite', 'imsave', 'videowriter', 'tofile') nos 4 módulos do produto (main.py, captura.py, rastreio.py, overlay.py) + requirements.txt.
2. `test_sem_escrita_em_disco` — Snapshot antes/depois dos arquivos de mídia (*.jpg/.jpeg/.png/.mp4/.avi/.mkv) no repositório (ignorando .git), executa pipeline headless por ~30 frames sobre vídeo-amostra usando captura.capturar → rastreio.rastrear → rastreio.extrair_caixas → overlay.desenhar_caixas/desenhar_hud, libera cap; pula com motivo em pt-BR se modelo/arquivo indisponíveis.
3. `test_requirements_sem_contrib` — Verifica ausência de 'opencv-contrib' em requirements.txt.

**Verification:** `python -m pytest tests/test_privacidade.py -x -q` → 3 passed (3.93s)

### Task 2: tests/test_integracao.py — pipeline ponta a ponta e IDs efêmeros (CNT-03)
- **Type:** auto, tdd=true
- **Status:** completed
- **Commit:** 04f06b0
- **Files:** tests/test_integracao.py (created)

**Tests implemented:**
1. `test_pipeline_amostra_detecta_corpo` — Processa ≥ 60 frames headless; total de caixas ≥ 1; todo track_id é `int`. Usa captura.abrir_fonte, rastreio.carregar_modelo, loop com desenhar_caixas/desenhar_hud; libera fonte.
2. `test_ids_efemeros` — Compara IDs dos primeiros 1/3 vs últimos 1/3 (até 120 frames); exige que pelo menos um ID desapareça (transição). Se não houver transição, pula com motivo em pt-BR — nunca falha falsa.
3. `test_sem_persistencia_ids` — Snapshot antes/depois incluindo *.csv/*.json além de mídia; processa 30 frames headless; verifica ausência de arquivos novos.

**Verification:** `python -m pytest tests/test_integracao.py -x -q` → 3 passed (6.72s)

**Combined verification (Tasks 1-2):** `python -m pytest tests/test_privacidade.py tests/test_integracao.py -q` → 6 passed (7.21s)

## Pending Tasks

### Task 3: Verificação visual — caixas de corpo + IDs, sem face (gate=blocking)
- **Type:** checkpoint:human-verify, gate=blocking
- **Status:** NOT EXECUTED (pending human)
- **Action:** Não executado conforme instrução — gate humano. Após suíte completa verde, executar roteiro:
  1. `python -m pytest tests/ -q` — confirmar suíte verde
  2. `python main.py test/gemini_generated_video_8d21d35f.mp4` — verificar caixas laranja com "ID N | XX%", HUD FPS/Pessoas, sem face/objetos não-humanos; pressionar q
  3. `python main.py` (webcam) — mesmo comportamento; pressionar q
  4. `git status --porcelain` — confirmar nenhum arquivo de mídia (*.jpg/*.png/*.mp4/*.avi) novo
  5. Confirmar ausência de face/biometria e IDs mudam/desaparecem conforme saem do quadro

**Awaiting:** Human approval via resume-signal ("aprovado" ou descrição do problema). This is blocking completion of the full phase.

## Deviations from Plan
None - Tasks 1-2 executed exactly as specified (TDD). No code changes to product modules (main.py, captura.py, rastreio.py, overlay.py); only new test files.

## Auth Gates
None.

## Known Stubs
None. Tests only; no product code stubs introduced.

## Threat Flags
None - tests are observational/audit-only (no new network endpoints, auth paths, file access patterns at trust boundaries in product code).

## Self-Check
- [x] Created files exist: tests/test_privacidade.py, tests/test_integracao.py
- [x] Commits exist: 04f06b0 contains both test files
- [x] All automated verify commands passed for Tasks 1-2 (6/6 tests)
- [x] Task 3 explicitly not executed per plan (checkpoint:human-verify, gate=blocking)
- [x] Partial SUMMARY.md created with substantive content
- [x] No new media files detected by disk audit

**Self-Check Result:** PASSED

## Next Steps
Await human verification (Task 3). Once approved, Task 3 will be completed and final SUMMARY.md/state updates performed.
