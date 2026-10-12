---
phase: 02-contagem-por-zona-e-ocupa-o-em-tempo-real
plan: 02
subsystem: tripwire
tags: [tripwire, bidirecional, histerese, debounce, prune, lgpd]

# Dependency graph
requires:
  - "02-01 (zona.py carregar_zonas, helpers geométricos, constantes)"
provides:
  - "zona.verificar_tripwires(tracks, zonas, estado, track_states, agora=None, frame_idx=0) — travessia bidirecional sem dupla contagem"
  - "zona.podar_track_states(track_states, frame_idx) — limpeza de memória por PRUNE_FRAMES"
  - "semáforo 'crossed' por zona; lado_anterior armazenado por zona; debounce 3 frames; histerese 15px"
affects: [main.py (loop), 02-04 overlay/contadores]

# Tech tracking
tech-stack:
  unchanged: [zona.py]
  patterns:
    - "Contagem por transição de lado (produto vetorial), não por posição instantânea"
    - "crossed como semáforo de meio-ciclo evita rajada na borda (Pitfall 3)"
    - "Debounce: track precisa 3 frames de presença antes de contar"
    - "Prune: track morto remove-se do track_states após PRUNE_FRAMES (=60)"

key-files:
  modified:
    - zona.py

key-decisions:
  - "Travessia reversa a oposto lado limpa o semáforo crossed (fix c1af984) — impede contagem pendente após reentrada"
  - "Eventos apenas para o frame atual; nada acumulado fora do loop (D-13)"
  - "Direção tirada do YAML; lado_entrada = +1 para 'entrada', -1 caso contrário"

# Phase 2 Plan 02: Travessia de tripwire bidirecional Summary

**`verificar_tripwires` implementa contagem bidirecional com debounce, histerese e prune; sem dupla contagem ao oscilar na borda.**

## Performance

- **Started:** 2026-10-10T13:47:09-03:00
- **Completed:** 2026-10-10T15:20:31-03:00
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implementada lógica de transição por produto vetorial entre frames (D-10/D-12/D-13)
- `crossed` por zona evita rajada ENTROU/SAIU na banda de histerese 15px
- Debounce `DEBOUNCE_FRAMES=3` impede contagem de tracks instáveis
- `PRUNE_FRAMES=60` remove track_states de tracks que sumiram do quadro
- Fix `c1af984`: travessia reversa a lado oposto reseta o semáforo crossed, garantindo saída correta após reentrada

## Task Commits

1. **Tripwire + prune + fix de semáforo**
   - `96eb45e` (feat: tripwire traversal + occupancy base + reset logic)
   - `c1af984` (fix: require reverse traversal to opposite side to clear crossed semaphore)

## Files Created/Modified
- `zona.py` - `verificar_tripwires`, `podar_track_states`, campos `crossed/lado_anterior/frames_vistos/ultimo_frame_visto`

## Verification
- Critérios do plano: 1 ENTROU/SAIU por travessia, sem dupla contagem na borda, histerese impede explosão, debounce aplicado, memória podada
- Testes `tests/test_zona.py` permanecem verdes (contexto puro)

