---
phase: 02-contagem-por-zona-e-ocupa-o-em-tempo-real
plan: 04
subsystem: integracao-visual
tags: [overlay, main, privacidade, integracao, lgpd, readme, docs]

# Dependency graph
requires:
  - "02-01 (carregar_zonas), 02-02 (verificar_tripwires), 02-03 (atualizar_ocupacao, reconciliar_fonte)"
provides:
  - "overlay.desenhar_tripwires(frame, zonas) — linhas de tripwire com labels"
  - "overlay.desenhar_rois(frame, zonas) — polígonos semi-transparentes"
  - "overlay.desenhar_contadores(frame, estado) — bloco de contadores na HUD"
  - "main.py com wiring de zonas: carregar_zonas, loop de eventos, contadores, reset por tecla"
  - "extensão da auditoria de privacidade (nada em disco, sem face, sem semáforos roteando IDs) e do teste de integração para contagens"
affects: [Fase 3 (API), Fase 8 (validação), CONCERNS.md, README]

# Tech tracking
tech-stack:
  added: [zonas_visualizacao.png, entender_zonas.py]
  patterns:
    - "Overlay sem escrita em disco; somente desenho no frame em RAM"
    - "Tecla R reseta contadores durante a execução; exibição Das zona com labels e cores por direção"
    - "Privacidade: pessoal só em memória, nada de imagem disco, uso exclusivo do 'entender_zonas.py' para depuração"

key-files:
  created:
    - entender_zonas.py
    - zonas_visualizacao.png
  modified:
    - overlay.py
    - main.py
    - tests/test_privacidade.py
    - tests/test_integracao.py
    - README.md
    - .planning/codebase/CONCERNS.md
    - .planning/STATE.md
    - .planning/milestone.lock

key-decisions:
  - "Atualização do CONCERNS.md documenta redução do problema de oclusão em cena lotada"
  - "README reflete nova capacidade de contagem por zona e exemplo de uso"

# Phase 2 Plan 04: Integração visual no main e auditoria Summary

**Integração no `main.py` (carregamento → contagem → overlay → loop), overlay de tripwires/ROIs/contadores, e auditoria de privacidade/integracao ampliada.**

## Performance

- **Started:** 2026-10-10T13:56:33-03:00
- **Completed:** 2026-10-11T12:59:15-03:00
- **Tasks:** 1
- **Files modified:** 9

## Accomplishments
- Overlay passa a desenhar tripwires (vermelho/verde por direção), ROIs semi-transparentes e contadores `ENT/SAI/OCC` na HUD
- `main.py` carrega zonas, faz o loop de eventos Tripwire/Ocupação, desenha overlay e permite reset via tecla R durante a execução
- Auditoria de privacidade estendida para varrer novo código de zonas/overlays (segue sem ler/escrever disco, sem formato por-pessoa, sem face)
- Testes de integração validam contagens no vídeo-amostra sem flicker de eventos
- Documenta limitação de oclusão no `CONCERNS.md` e ajusta README com novas funcionalidades

## Task Commits

1. **Overlay + main wiring + auditoria**
   - `6d18527` (feat: overlay drawing functions for tripwires/ROIs/counters)
   - `3fb50c5` (feat: wire zone counting into main.py and extend privacy/integration audits)
2. **Docs/estado/auxiliares**
   - `4a9fdd4` (docs: document occlusion limitation in CONCERNS.md)
   - `bec1e39` (chore: set default capacity to 50 and update test — tambem presente em 02-03)
   - `8077c81` (Atualiza estado do projeto e arquivos de zonas — inclui entender_zonas.py + zonas_visualizacao.png)
   - `2c14cfa` (docs: update README with Phase 2 features, zona module, and usage)

## Files Created/Modified
- `overlay.py` — `desenhar_tripwires`, `desenhar_rois`, `desenhar_contadores`
- `main.py` — wiring completo de zonas (carregar, eventos, overlay, reset de contadores)
- `entender_zonas.py` + `zonas_visualizacao.png` — utilitário de depuração/visualização (não integrado no pipeline de produção)
- `tests/test_privacidade.py`, `tests/test_integracao.py` — cobertura ampliada
- `README.md`, `CONCERNS.md`, `.planning/STATE.md` — status/docs

## Verification
- Critérios do plano: uso visual com contadores seguindo pessoas (vídeo-amostra), integração com `main.py` funcional, auditoria de privacidade/integracao ampliada — implementado e testado.
- Suite final: 35 testes passando.
