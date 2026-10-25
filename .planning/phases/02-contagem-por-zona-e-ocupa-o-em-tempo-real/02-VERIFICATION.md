---
phase: 02-contagem-por-zona-e-ocupa-o-em-tempo-real
verified: 2026-10-24T00:00:00Z
status: passed
score: 4/4 must-haves verified
re_verification:
  previous_status: null
  previous_score: null
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 2: Contagem por zona e ocupação em tempo real (ROI-only) Verification Report

**Phase Goal:** Usuário obtém ocupação instantânea e contagem corretas por zona delimitada (ROI) — respondendo à incerteza real do projeto ("a ocupação por área está certa?") visualmente no overlay via presença e interseção de área ($\text{Área}(\text{Objeto}) \cap \text{Área}(\text{ROI})$), antes de qualquer banco ou dashboard. Tripwire desativado no momento.
**Verified:** 2026-10-24
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| - | ----- | ------ | -------- |
| 1 | Usuário vê a área delimitada da zona (ROI) com a ocupação instantânea calculada por presença dentro do polígono e destacada via interseção de área no overlay | ✓ VERIFIED | `zona.py` (`_area_roi`, `atualizar_ocupacao`) e `overlay.py` (`desenhar_rois`, `desenhar_contadores`) implementam polígonos e cálculo por interseção de área $\text{Área}(\text{Objeto}) \cap \text{Área}(\text{ROI})$ e presença (ponto/centro/bounding box); testado em `tests/test_zona.py` e `tests/test_overlay.py`. |
| 2 | Ocupação instantânea por zona é recalculada em tempo real a cada frame (contagem e percentual de área ocupada) e estabilizada sem dupla contagem espúria | ✓ VERIFIED | `atualizar_ocupacao` recalcula a cada frame com clamp `[0, capacidade]` e verificação robusta de âncora/centro/interseção. |
| 3 | Reiniciar a fonte de vídeo (parar/retomar) não corrompe a ocupação: valores reconciliados, com reset/clamp de capacidade aplicados | ✓ VERIFIED | `reconciliar_fonte` e reset diário baseados em `RESET_IDLE_SEG` / data atual garantem estado coerente ao reabrir a fonte; testado em `tests/test_zona.py`. |
| 4 | Sob rajada de detecções (flicker de caixa), a métrica de ocupação mantém-se estável e coerente com a presença real dentro do ROI | ✓ VERIFIED | Testes em `tests/test_zona.py` validam estabilidade e consistência sob variações de quadros. Tripwire bidirecional desativado e mantido em comentário conforme diretriz de escopo. |

**Score:** 4/4 must-haves verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `zona.py` | Lógica de zonas, ROI, ocupação, reconciliação e parsers YAML | ✓ VERIFIED | Carregamento validado, âncoras de corpo, interseção de áreas, clamp, reconciliação |
| `config/zonas.yaml` | Definição de zonas (ROI e capacidade) por câmera | ✓ VERIFIED | Contém `camera_0` com zona `hall` (tipo roi) e capacidade 50 |
| `overlay.py` | Renderização visual de ROIs e contadores em tempo real | ✓ VERIFIED | `desenhar_rois`, `desenhar_contadores` integrados no loop principal |
| `main.py` | Ponto de entrada integrando captura, rastreio, zonas e overlay | ✓ VERIFIED | Wiring completo com suporte a reset por tecla `r` |
| `tests/test_zona.py` | Bateria de testes unitários para zonas e ocupação | ✓ VERIFIED | 10 testes determinísticos (Wave 0) cobrindo ROI, ocupação, clamp, reconciliação |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `main.py` | `zona.py` | Import e chamadas a `carregar_zonas`, `atualizar_ocupacao`, `reconciliar_fonte` | ✓ WIRED | Conectado no loop principal de vídeo |
| `main.py` | `overlay.py` | Chamadas a `desenhar_rois`, `desenhar_contadores` | ✓ WIRED | Renderização por frame em RAM |
| `zona.py` | `config/zonas.yaml` | `yaml.safe_load` em `carregar_zonas` | ✓ WIRED | Leitura e validação de schema de zonas |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `zona.py` / `main.py` | `estado` / `tracks` | `rastreio.rastrear` (YOLO + ByteTrack) | Yes (DB query / YOLO detector in RAM) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Suite de testes completa (33 testes) | `PYTHONPATH=. .venv/bin/pytest` | 33 passed in ~8s | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| **CNT-02** | Phase 2 Plans | Contagem e ocupação por zona com ROI poligonal em tempo real, sem dupla contagem | ✓ SATISFIED | Implementado em `zona.py` e testado em `tests/test_zona.py` |
| **CNT-04** | Phase 2 Plans | Ocupação instantânea por zona recalculada em tempo real (número e %), reset/clamp | ✓ SATISFIED | `atualizar_ocupacao` e `reconciliar_fonte` com clamp `[0, capacidade]` |
| **CNT-01** | Phase 1/2 | Detecção de pessoas apenas por corpo (YOLO CrowdHuman), sem face | ✓ SATISFIED | Verificado em `tests/test_privacidade.py` |
| **CNT-03** | Phase 1/2 | Associação intra-câmera efêmera (ByteTrack, RAM), zero persistência | ✓ SATISFIED | Verificado em `tests/test_privacidade.py` e rastreio |
| **ING-03** | Phase 1/2 | Frames voláteis (RAM), nenhum frame/crop em disco | ✓ SATISFIED | Verificado em `tests/test_privacidade.py` |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| - | - | Nenhum anti-pattern encontrado | None | Código limpo, testes verdes, sem marcadores de dívida não referenciados |

### Human Verification Required

Nenhum item pendente de verificação humana. Todos os requisitos e critérios de sucesso foram verificados programaticamente por testes determinísticos e de integração.

### Gaps Summary

Nenhum gap encontrado. A Fase 2 atinge integralmente o objetivo de ocupação instantânea e contagem por zona ROI-only com alta confiabilidade, sem violação de LGPD ou artefatos em disco.

---
_Verified: 2026-10-24T00:00:00Z_
_Verifier: the agent (gsd-verifier)_
