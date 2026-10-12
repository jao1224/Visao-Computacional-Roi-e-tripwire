---
phase: 02-contagem-por-zona-e-ocupa-o-em-tempo-real
plan: 03
subsystem: ocupacao
tags: [ocupacao, reconciliacao, clamp, reset, lgpd]

# Dependency graph
requires:
  - "02-01 (zona.py carregar_zonas, helpers geométricos, constantes)"
  - "02-02 (verificar_tripwires, track_states)"
provides:
  - "zona.atualizar_ocupacao(tracks, zonas, estado, agora=None, track_states=None) — contagem por ROI com clamp e reset diário"
  - "zona.reconciliar_fonte(estado, track_states) — reajusta/memoriza estado ao reconectar/reabrir fonte"
  - "semântica de clamp entre 0 e capacidade; reinício diário por RESET_IDLE_SEG"
affects: [main.py (loop), 02-04 overlay]

# Tech tracking
tech-stack:
  unchanged: [zona.py]
  patterns:
    - "Contagem de ocupação via âncora bbox (bottom_center) dentro de polígonos"
    - "Capacidade por câmera compartilhada, aplicada por clamp [0, capacidade]"
    - "Reset após RESET_IDLE_SEG (=600s) ou ao reabrir fonte (reconciliação)"

key-files:
  modified:
    - zona.py
    - config/zonas.yaml

key-decisions:
  - "Ocupacão zerada ao reiniciar a fonte + reconciliacao via reconciliar_fonte (estado coerente)"
  - "Valores nunca negativos ou acima da capacidade (clamp)"
  - "Capacidade padrão de 50 no YAML (ajuste em bec1e39)"

# Phase 2 Plan 03: Ocupação por ROI e reconciliação Summary

**`atualizar_ocupacao` conta cabeças dentro de ROIs com âncora bbox, aplica clamp [0, capacidade] e reset diário; `reconciliar_fonte` estabiliza o estado ao reabrir o vídeo.**

## Performance

- **Started:** 2026-10-10T13:47:09-03:00 (feita em conjunto com 02-02)
- **Completed:** 2026-10-11T11:51:17-03:00
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Ocupação calculada por ROI usando o centro do bbox (`_bottom_center`) dentro do polígono definido — sem persistência por-pessoa
- clamp entre 0 e capacidade (atualmente 50) impede sobrecarga de contagem visual
- Reset diário por `RESET_IDLE_SEG` evita 'home block' de ocupação
- `reconciliar_fonte` descreve estado atual da contagem de ROI e limpa quando a fonte muda
- Capacidade no YAML ajustada para 50

## Task Commits

1. **Ocupação e reconciliação (em bundle com tripwire)**
   - `96eb45e` (feat: tripwire traversal and occupancy with reset logic)
   - `bec1e39` (chore: set default capacity to 50 and update test)

## Files Created/Modified
- `zona.py` - `atualizar_ocupacao`, `reconciliar_fonte`, helpers de clamp/reset
- `config/zonas.yaml` - capacidade 50

## Verification
- Critério do plano: ocupação refletindo ROI corretamente, não corrompida por restart, clampado entre limites — coberto pelos testes e validado no vídeo-amostra.

