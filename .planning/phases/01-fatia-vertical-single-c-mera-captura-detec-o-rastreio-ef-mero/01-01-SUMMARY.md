---
phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero
plan: 01
subsystem: ingesta-video
tags: [opencv, video-capture, overlay, pytest, requirements, lgpd, privacidade]

# Dependency graph
requires: []
provides:
  - "requirements.txt com lock de runtime (ultralytics, opencv-python, numpy, lap)"
  - "requirements-dev.txt com pytest"
  - "captura.abrir_fonte(fonte) — fronteira da fonte de vídeo (webcam int / arquivo str)"
  - "captura.capturar(cap) — contrato (frame, capture_ts) carimbado na captura"
  - "overlay.desenhar_caixas(frame, caixas) — desenho in-place de caixas com ID/conf"
  - "overlay.desenhar_hud(frame, fps, n_pessoas) — HUD in-place"
  - "tests/conftest.py com fixtures caminho_modelo e caminho_video_amostra"
affects: [01-02-rastreio, 01-03-main, 01-04-privacidade, fase-2-zonas, fase-6-rtsp]

# Tech tracking
tech-stack:
  added: [pytest, requirements.txt, requirements-dev.txt]
  patterns:
    - "Módulos planos na raiz sem pacote/__init__.py (D-01/D-02)"
    - "Funções puras de nível de módulo, sem classes (D-04)"
    - "capture_ts carimbado imediatamente após cap.read (contrato de timestamp)"
    - "Overlay in-place sem nenhuma API de escrita em disco (ING-03)"
    - "TDD RED→GREEN por task"

key-files:
  created:
    - requirements.txt
    - requirements-dev.txt
    - captura.py
    - overlay.py
    - tests/conftest.py
    - tests/test_captura.py
    - tests/test_overlay.py
    - .gitignore
  modified: []

key-decisions:
  - "opencv-python (não opencv-contrib-python) para evitar cv2.face"
  - "Versões fixadas iguais às verificadas na máquina (ultralytics 8.4.121, opencv-python 5.0.0.93, numpy 2.5.2, lap 0.5.13)"
  - "abrir_fonte não valida abertura — devolve o cap; o chamador checa isOpened()"
  - "CAP_PROP_BUFFERSIZE=1 apenas para fonte int (webcam); arquivo não suporta"

patterns-established:
  - "Fronteira de fonte de vídeo isolada em captura.py (RTSP entra na Fase 6 sem tocar o resto)"
  - "capture_ts nunca re-carimbado a jusante"
  - "overlay.py é a única camada de desenho; proibida escrita em disco"
  - "Auditoria de privacidade escopada aos módulos do produto + requirements.txt"

requirements-completed: [ING-01, ING-03]

# Metrics
duration: 3min
completed: 2026-10-08
---

# Phase 1 Plan 01: Lock de dependências, fronteira de captura e overlay Summary

**Lock de runtime + `captura.abrir_fonte/capturar` (contrato capture_ts) + `overlay.desenhar_caixas/desenhar_hud` in-place, com harness pytest e 6 testes verdes**

## Performance

- **Duration:** 3 min
- **Started:** 2026-10-08T22:07:15Z
- **Completed:** 2026-10-08T22:09:56Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- `requirements.txt`/`requirements-dev.txt` criados com versões fixadas e sem lib de face/biometria (fecha T-01-02)
- `captura.py` expõe `abrir_fonte` (webcam int / arquivo str, BUFFERSIZE=1 em webcam) e `capturar` que devolve `(frame, capture_ts)` carimbado imediatamente após o `read`
- `overlay.py` desenha caixas com ID/conf e HUD in-place via `cv2.rectangle`/`cv2.putText`, sem nenhuma API de escrita em disco (fecha T-01-01, metade de ING-03)
- Harness pytest (`tests/conftest.py`) com fixtures `caminho_modelo` (resolução dos candidatos de `main.py:11-19`) e `caminho_video_amostra` (MP4 de `test/`); 6 testes verdes lendo o vídeo-amostra real

## Task Commits

Each task was committed atomically (TDD tasks split RED→GREEN):

1. **Task 1: Lock de dependências + scaffold (Wave 0)** - `887973b` (chore — ver Issues; commit externo bundle, meu commit foi no-op)
2. **Task 2: captura.py (RED)** - `60b1e9b` (test)
   **captura.py (GREEN)** - `8d8cfdc` (feat)
3. **Task 3: overlay.py (RED)** - `9320419` (test)
   **overlay.py (GREEN)** - `f1b6a4c` (feat)

**Hygiene:** `d0d2020` (chore: .gitignore)

**Plan metadata:** `PENDING` (docs: complete plan)

_Note: TDD tasks têm commits separados test → feat._

## Files Created/Modified
- `requirements.txt` - Lock de runtime: ultralytics/opencv-python/numpy/lap fixados
- `requirements-dev.txt` - `-r requirements.txt` + `pytest>=8.0`
- `captura.py` - Fronteira da fonte de vídeo com contrato `capture_ts`
- `overlay.py` - Desenho in-place de caixas (ID/conf) e HUD, sem persistência
- `tests/conftest.py` - Fixtures `caminho_modelo` e `caminho_video_amostra`
- `tests/test_captura.py` - 3 testes ING-01 (abre MP4, lê frame, timestamp monotônico)
- `tests/test_overlay.py` - 3 testes de desenho in-place e ausência de APIs de escrita
- `.gitignore` - Ignora `__pycache__/`, `*.pyc`, `.pytest_cache/`

## Decisions Made
- `opencv-python` em vez de `opencv-contrib-python` (evita `cv2.face`) — alinhado a D-05/CNT-01
- `abrir_fonte` não valida abertura; devolve o `cap` para o chamador checar `isOpened()` (contrato explícito no plano)
- Fixtures em escopo `session` com `pytest.skip` em pt-BR quando o recurso não existe

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] pytest ausente no ambiente**
- **Found during:** Task 1 (verify de dependências)
- **Issue:** `import pytest` falhava (`ModuleNotFoundError`), requisito da Wave 0
- **Fix:** `python -m pip install "pytest>=8.0"` → instalado pytest 9.1.1
- **Files modified:** ambiente (fora do repo)
- **Verification:** `python -c "import ultralytics, cv2, numpy, lap, pytest"` → `deps-ok` (exit 0)
- **Committed in:** no-op (dependência de ambiente; declarada em `requirements-dev.txt`)

**2. [Rule 2 - Missing hygiene] Adicionado `.gitignore` para artefatos gerados**
- **Found during:** Task 2 (RED) — `tests/__pycache__/` apareceu como untracked
- **Issue:** Sem `.gitignore`, artefatos de runtime (pycache/pytest_cache) ficariam untracked e seriam varridos por commits
- **Fix:** Criado `.gitignore` com `__pycache__/`, `*.pyc`, `.pytest_cache/`
- **Files modified:** `.gitignore`
- **Verification:** `git status --porcelain` limpo após os testes
- **Committed in:** `d0d2020`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 hygiene)
**Impact on plan:** Nenhum scope creep; ambas necessárias para o gate de verificação e o estado limpo do repo.

## Issues Encountered

**Commit baseline externo em `887973b` ("projeto visao computacional")**
- Durante a Task 1, um processo externo ao executor criou um commit que **bundleou** `requirements.txt`, `requirements-dev.txt` e `tests/conftest.py` junto com todos os arquivos do backup que estavam untracked (`main.py`, `test/`, `models/`, `resultados/`, `runs/`, `scripts/`, etc.).
- Efeito: o commit individual da Task 1 virou no-op (os arquivos já estavam commitados); a atribuição atômica da Task 1 aponta para `887973b`.
- Não havia hooks configurados (`.git/hooks` só com `.sample`; `core.hooksPath` vazio), portanto a origem é externa ao repositório.
- Tasks 2 e 3 foram commitadas atomicamente sem interferência (RED→GREEN separados).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plano 02 (`rastreio.py`) pode consumir `captura.capturar` e a fixture `caminho_video_amostra` para o teste de IDs efêmeros.
- Plano 03 (`main.py`) pode importar `captura`/`overlay` e usar as fixtures `caminho_modelo`/`caminho_video_amostra`.
- Backstop manual restante para ING-01: abrir a webcam física (índice 0) — verificação visual (Plano 04).
- Nenhum arquivo de mídia novo criado pelos testes (`git status --porcelain` limpo).

---
*Phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero*
*Completed: 2026-10-08*

## Self-Check: PASSED

- FOUND: requirements.txt, requirements-dev.txt, captura.py, overlay.py, tests/conftest.py, tests/test_captura.py, tests/test_overlay.py, .gitignore, 01-01-SUMMARY.md
- FOUND commits: 887973b, 60b1e9b, 8d8cfdc, 9320419, f1b6a4c, d0d2020
