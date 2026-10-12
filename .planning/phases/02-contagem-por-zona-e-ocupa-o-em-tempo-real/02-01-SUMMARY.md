---
phase: 02-contagem-por-zona-e-ocupa-o-em-tempo-real
plan: 01
subsystem: zonas
tags: [zonas, yaml, pytest, pyyaml, tripwire, roi, lgpd, privacidade]

# Dependency graph
requires:
  - "módulos planos da Fase 1 (captura, overlay, rastreio, main)"
provides:
  - "zona.py — constantes (DEBOUNCE_FRAMES, HYSTERESIS_PX, RESET_IDLE_SEG, PRUNE_FRAMES) + helpers de geometria (_bottom_center, _lado, _dist_ponto_segmento) + carregar_zonas"
  - "config/zonas.yaml — camera_0 com tripwire 'recepcao' e roi 'hall', capacidade 50"
  - "pyyaml==6.0.3 pinado em requirements.txt"
  - "tests/test_zona.py — harness Wave 0 determinístico de CNT-02/CNT-04 (13 testes)"
affects: [02-02-tripwire, 02-03-ocupacao, 02-04-main-overlay]

# Tech tracking
tech-stack:
  added: [pyyaml, config/zonas.yaml, zona.py, tests/test_zona.py]
  patterns:
    - "yaml.safe_load + validação de schema (pontos numéricos, >= 3 em roi, raz âncora da ocupação)"
    - "Zona inválida é pulada com [Aviso]; arquivo/câmera ausente -> [] com [Erro]/[Aviso] (Armadilha 5)"
    - "Atributo 'lado' por produto vetorial (transição conta, posição não)"
    - "Testes sem modelo/vídeo/GUI/relógio real (Wave 0 determinístico)"

key-files:
  created:
    - config/zonas.yaml
    - zona.py
    - tests/test_zona.py
  modified:
    - requirements.txt

key-decisions:
  - "pyyaml==6.0.3 pinado e consumido só via import direto em zona.py (A4)"
  - "capacidade padrão 50 por câmera, aplicada por clamp a cada zona"
  - "Arquivo zonas.yaml ausente ou câmera sem entrada retorna [] sem levantar exceção (graceful)"

# Phase 2 Plan 01: Config de zonas + carregamento validado Summary

**`config/zonas.yaml` (tripwire recepcao + roi hall, capacidade 50) + `carregar_zonas` com validação de schema e helpers de geometria, com harness de 13 testes determinísticos Wave 0**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-10-10T13:12:06-03:00
- **Completed:** 2026-10-10T13:12:36-03:00
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- `pyyaml==6.0.3` pinado em `requirements.txt` para parsing seguro do YAML de zonas
- `config/zonas.yaml` criado com `camera_0`: tripwire `recepcao` (linha [[100,360],[540,360]], direcao saida), roi `hall` (polígono de 4 pontos), capacidade 50 (ajustada de 30 para 50 em `bec1e39`)
- `zona.py` com constantes `DEBOUNCE_FRAMES=3`, `HYSTERESIS_PX=15.0`, `RESET_IDLE_SEG=600`, `PRUNE_FRAMES=60`, helpers `_bottom_center`/`_lado`/`_dist_ponto_segmento`/`_pontos_validos`/`_normalizar_zona` e `carregar_zonas(camera_id, caminho)` com validação de schema e avisos nas falhas duráveis
- Harness `tests/test_zona.py` com 13 testes determinísticos cobrindo YAML camera_0, carregamento, grupos de tripwire/roi e resets relevantes de CNT-02/CNT-04 (Wave 0)

## Task Commits

1. **Task 2: Testes (RED) + config + pin** - `75ffed5` (test: harness zonas, zonas.yaml, pyyaml)
2. **Task 3: zona.py (GREEN)** - `25f836e` (feat: helpers geométricos + carregar_zonas)
3. **Ajuste pós-plano:** `bec1e39` (chore: capacidade padrão 50 + teste)

## Files Created/Modified
- `config/zonas.yaml` - Config de zonas por câmera (D-02)
- `zona.py` - Módulo de zonas: constantes, geometria, `carregar_zonas`
- `tests/test_zona.py` - Harness Wave 0 (13 testes determinísticos)
- `requirements.txt` - Adicionado `pyyaml==6.0.3`

## Verification
- must_haves do plano cumpridos: YAML parseável, carregar_zonas normaliza/valida, harness de 13 testes criado (RED ao escrever, GREEN após zona.py)
- Suite `pytest tests/ -q` ao final da fase: 35 verdes
