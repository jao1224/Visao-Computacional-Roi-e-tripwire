# Phase 2: Contagem por zona e ocupação em tempo real - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-08
**Phase:** 02-contagem-por-zona-e-ocupa-o-em-tempo-real
**Areas discussed:** Definição de zonas/tripwires, Módulo novo e integração no main.py, Ocupação: reset/clamp/reconciliação, Overlay visual de contadores, Lógica de contagem anti-duplicação, Testes e validação

---

## Definição de zonas/tripwires

| Option | Description | Selected |
|--------|-------------|----------|
| Tripwire (linha) vs ROI poligonal | Tripwire para contagem ENTROU/SAÍDA + ROI para ocupação instantânea — ambos necessários | ✓ |
| Formato do arquivo de config | `config/zonas.yaml` (legível, editável, versionado) | ✓ |

**User's choice:** Tripwire + ROI na mesma zona; YAML como formato de config; `camera_id` mapeia 1:1 com fonte resolvida em `main.py`

**Notes:** Usuário esclareceu que zonas não dependem de câmeras reais — são configuração lógica definida agora para vídeo-amostra/webcam, depois cadastradas por câmera no PostgreSQL via dashboard (Fase 5+).

---

## Módulo novo e integração no main.py

| Option | Description | Selected |
|--------|-------------|----------|
| Nome do módulo | `zona.py` (português, substantivo, raiz, segue convenção Fase 1) | ✓ |
| Funções expostas | `carregar_zonas`, `verificar_tripwires`, `atualizar_ocupacao`, `desenhar_contadores` | ✓ |
| Ponto de integração no main.py | Após `extrair_caixas`, antes de `desenhar_hud` | ✓ |

**User's choice:** `zona.py` na raiz; integração no laço `while` do `main.py` passando `tracks` e `frame`; estado (`estado`, `track_states`) vive em `main()` e passado por referência.

---

## Ocupação: reset/clamp/reconciliação

| Option | Description | Selected |
|--------|-------------|----------|
| Reset diário | Meia-noite OU known-empty (ocupação 0 por > 10 min) — ambos | ✓ |
| Clamp | `max(0, min(ocupacao, capacidade))` — capacidade no YAML | ✓ |
| Reconciliação pós-reconexão | Ao reabrir fonte, zera ocupação e `crossed` daquela camera_id | ✓ |

**User's choice:** Reset duplo (horário + known-empty) mais robusto; clamp evita negativo e acima da capacidade; reconciliação prepara Fase 6.

---

## Overlay visual de contadores

| Option | Description | Selected |
|--------|-------------|----------|
| Onde implementar | Estende `overlay.py` (desenho) | ✓ |
| Elementos | `desenhar_tripwires` (verde/vermelho), `desenhar_rois` (azul alpha), `desenhar_contadores` (cards IN/OUT/OCUP) | ✓ |

**User's choice:** Cores: laranja caixas (existente), verde entrada/vermelho saída tripwires, azul ROIs, branco/preto HUD.

---

## Lógica de contagem anti-duplicação

| Option | Description | Selected |
|--------|-------------|----------|
| Estado por track_id | `last_zone`, `crossed` set, `frames_since_first_seen`, `last_cross_ts` | ✓ |
| Debounce | `frames_since_first_seen >= 3` (track estável antes de contar) | ✓ |
| Hysteresis | Afastar `> 15 px` da linha antes de permitir reverso | ✓ |
| Direção | Produto vetorial (linha × movimento) → ENTRADA/SAÍDA | ✓ |

**User's choice:** Parâmetros fixos em constantes no topo de `zona.py` (podem virar config depois).

---

## Testes e validação

| Option | Description | Selected |
|--------|-------------|----------|
| Arquivo de teste | `tests/test_zona.py` | ✓ |
| Fixtures | `zonas_config` carrega YAML (ou dict inline) | ✓ |
| Casos | tripwire entrada/saída, sem dupla contagem, ocupação ROI, reset diário, hysteresis | ✓ |
| Vídeo-amostra | `config/zonas.yaml` inclui `camera_0` para 1280x720 | ✓ |

**User's choice:** Testes unitários isolados + config de exemplo para vídeo-amostra.

---

## Claude's Discretion

- Assinatura exata das funções de `zona.py` (parâmetros, ordem, tipos)
- Estrutura interna do `track_states` (dict vs dataclass)
- Como `main.py` deriva `camera_id` da fonte (webcam 0 → `"camera_0"`, arquivo → `"camera_0"`, RTSP futuro → `"camera_N"`)
- Valores exatos: `debounce_frames=3`, `hysteresis_px=15`, `reset_idle_min=10`
- `desenhar_tripwires`/`desenhar_rois` em `overlay.py` (por ser desenho)

---

## Deferred Ideas

- MTMCT / Re-ID entre câmeras — FORA DO ESCOPO (LGPD Art. 12 §2º)
- Heatmap de densidade — Fase 7 (DWL-02)
- Dashboard CRUD de zonas — Fase 5 (DSH-01/DSH-03)
- Persistência de eventos ENTROU/SAÍDA no PostgreSQL — Fase 3 (API-01)
- Validação contra contagem manual em pico — Fase 8 (QUA-03)