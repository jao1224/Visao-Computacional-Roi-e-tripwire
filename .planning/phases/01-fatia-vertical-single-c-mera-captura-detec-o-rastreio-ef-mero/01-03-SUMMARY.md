---
phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero
plan: 03
subsystem: video-ingestion
tags: [opencv, ultralytics, yolo, bytetrack, python, cli]

# Dependency graph
requires:
  - phase: 01-01
    provides: captura.abrir_fonte/capturar (capture_ts) e overlay.desenhar_caixas/desenhar_hud
  - phase: 01-02
    provides: rastreio.carregar_modelo/rastrear/extrair_caixas (ByteTrack, só corpo)
provides:
  - main.py como ponto de entrada único que seleciona webcam/arquivo por CLI
  - laço de orquestração capturar → rastrear → extrair_caixas → overlay → imshow
  - resolução de fonte (resolver_fonte) e de peso (resolver_modelo) testáveis
affects: [Phase 2 (contagem por zona), Phase 6 (fonte RTSP)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Laço síncrono de orquestração com teto de FPS e cleanup (release/destroyAllWindows)"
    - "Resolução de entrada por função pura testável (resolver_fonte/resolver_modelo)"

key-files:
  created:
    - tests/test_main.py
  modified:
    - main.py

key-decisions:
  - "CLI: sem argumento → webcam 0; argumento numérico → índice int; caminho existente → arquivo; senão [Erro] e None"
  - "Fonte inválida/caminho inexistente não lança — devolve None e o main retorna (ASVS V5)"
  - "Aviso de pesos base COCO quando o caminho resolvido não termina em best.pt"

patterns-established:
  - "Ponto de entrada único orquestra módulos puros, sem classes (D-03/D-04)"
  - "Logs apenas em console com tags [OK]/[Aviso]/[Erro] (D-06)"

requirements-completed: [ING-01, ING-03, CNT-01, CNT-03]

# Metrics
duration: 2min
completed: 2026-10-08
---

# Phase 1 Plan 03: Integração do ponto de entrada Summary

**main.py passa a ser o ponto de entrada único: a CLI seleciona webcam ou arquivo, e o laço orquestra capturar→rastrear(ByteTrack)→overlay, mantendo IDs só em RAM e zero escrita em disco**

## Performance

- **Duration:** 2 min
- **Started:** 2026-10-08T19:25:23-03:00
- **Completed:** 2026-10-08T19:27:24-03:00
- **Tasks:** 2
- **Files modified:** 2 (main.py, tests/test_main.py)

## Accomplishments
- `resolver_fonte` / `resolver_modelo` como helpers de módulo testáveis; lista de candidatos de pesos preservada intacta
- `main()` reescrito: resolve modelo e fonte, abre a captura, e roda o laço `capturar → rastrear → extrair_caixas → desenhar_caixas/desenhar_hud → imshow` com FPS por tempo de parede e teto de 5 FPS
- Eliminada a chamada direta `model(...)`/`model.predict`; o rastreio é o caminho único via `rastreio.rastrear`
- Nenhuma escrita em disco (`save=`/`imwrite`/`VideoWriter` ausentes); `capture_ts` vem de `captura.capturar`
- Encerramento limpo com `cap.release()` + `cv2.destroyAllWindows()` e mensagem `[OK] Encerrado.`

## Task Commits

Each task was committed atomically (Task 1 TDD: RED → GREEN):

1. **Task 1 (RED): teste que falha para resolução de fonte/modelo** - `f5f0366` (test)
2. **Task 1 (GREEN): resolver_fonte/resolver_modelo + imports** - `b1ccf40` (feat)
3. **Task 2: laço de orquestração no main.py** - `fdf3543` (feat)

**Plan metadata:** `(docs: complete 01-03 plan)` (this SUMMARY commit)

_Note: Task 1 followed TDD (failing test first, then implementation)._

## Files Created/Modified
- `main.py` - Ponto de entrada único; helpers `resolver_fonte`/`resolver_modelo` e laço de orquestração integrando captura/rastreio/overlay
- `tests/test_main.py` - Testes de resolução de fonte/modelo (webcam default, índice→int, caminho existente, inexistente→None, candidatos) e presença dos imports dos módulos

## Decisions Made
- Prioridade de parsing da CLI: vazio → `0` (preserva comportamento/D-03); `isdigit()` → `int`; `os.path.exists` → caminho; caso contrário `None` com `[Erro]` (sem lançar).
- Aviso `[Aviso] Usando pesos base...` disparado por `basename != 'best.pt'` — cobre o fallback COCO sem depender de caminho exato.
- `capture_ts` consumido do contrato `captura.capturar` (não re-carimbado) para respeitar o contrato de timestamp da fase.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Known Stubs
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Integração de ponta a ponta pronta no nível de código; suíte completa verde (15 testes).
- Pendente (backstop, Plano 04): verificação visual com webcam e com o MP4 de `test/`, além da auditoria automatizada de privacidade (nada em disco / sem face).
- Sem novos endpoints/rede; nenhuma superfície de segurança fora do `<threat_model>` do plano (entrada de CLI validada por `os.path.exists`).

---
*Phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero*
*Completed: 2026-10-08*

## Self-Check: PASSED
- main.py — FOUND
- tests/test_main.py — FOUND
- 01-03-SUMMARY.md — FOUND
- Commits f5f0366, b1ccf40, fdf3543 — FOUND
