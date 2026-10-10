---
phase: "2"
slug: contagem-por-zona-e-ocupa-o-em-tempo-real
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-09"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (instalado; suite da Fase 1 com 21 testes verdes) |
| **Config file** | nenhum — `tests/conftest.py` (fixtures `caminho_modelo`, `caminho_video_amostra` com skip) |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T2-01 (deps pin pyyaml==6.0.3) | 02-01 | 1 | CNT-02/04 | — | import direto de `zona.py` | static | `python -c "import yaml"` + assert no requirements | ❌ W0 | ⬜ pending |
| T2-02 (config/zonas.yaml) | 02-01 | 1 | CNT-02/04 | T-02-01 (YAML tampering) | `yaml.safe_load` + validação de schema | unit | `pytest tests/test_zona.py::test_zonas_yaml_camera0 -x` | ❌ W0 | ⬜ pending |
| T2-03 (zona.py carregar_zonas) | 02-01 | 1 | CNT-02/04 | T-02-01 | coordenadas numéricas finitas | unit | `pytest tests/test_zona.py::test_carregar_zonas -x` | ❌ W0 | ⬜ pending |
| T2-04 (zona.py verificar_tripwires) | 02-02 | 2 | CNT-02 | T-02-03 (falso evento geométrico) | transição de lado + debounce + hysteresis; eventos não acumulados | unit | `pytest tests/test_zona.py::test_tripwire_entrada_saida -x` | ❌ W0 | ⬜ pending |
| T2-05 (zona.py atualizar_ocupacao + reset/clamp) | 02-03 | 3 | CNT-04 | T-02-02 (trilha individual em RAM) | clamp `[0, capacidade]`; reset meia-noite + known-empty; nunca entradas − saídas | unit | `pytest tests/test_zona.py::test_ocupacao_roi -x` | ❌ W0 | ⬜ pending |
| T2-06 (overlay contadores/tripwires/rois) | 02-04 | 4 | CNT-02/04 | — | desenho in-place, zero disco | unit | `pytest tests/test_zona.py::test_desenhos_retornam_frame -x` | ✅ Teste no harness; funções no 02-04 | ⬜ pending |
| T2-07 (main.py wiring + reconciliação) | 02-03 (reconciliar_fonte) + 02-04 (main.py wiring) | 3+4 | CNT-04 | T-02-02 | reconciliação limpa `track_states` inteiro | unit (reconcile) + static/unit (wiring) | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| T2-08 (privacidade: zona.py no alcance) | 02-04 | 4 | CNT-01/03 | T-02-02/T-02-04 (disco) | zero `imwrite`/`VideoWriter`/face em `zona.py` | unit/static | `pytest tests/test_privacidade.py -x -q` | ✅ | ⬜ pending |
| T2-09 (integração invariantes MP4) | 02-04 | 4 | CNT-02/04 | — | contagens ≥ 0, monotonicidade, sem exceção | integration | `pytest tests/test_integracao.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_zona.py` — stubs cobrindo CNT-02/CNT-04 (~10+ testes determinísticos, sem modelo/vídeo/GUI)
- [ ] `tests/test_integracao.py` — novo teste de invariantes de contagem no MP4 (opcional, tolerante)
- [ ] `tests/test_privacidade.py` — adicionar `zona.py` à lista `_produto_files()` (varredura de tokens banidos) e manter snapshot de disco
- [ ] `requirements.txt` — adicionar `pyyaml==6.0.3` (import direto de `zona.py`)
- [ ] `config/zonas.yaml` — `camera_0` com tripwire + ROI de exemplo (D-21); fixture de teste carrega o arquivo real

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Contadores sobem/descem conforme pessoas cruzam a linha; ocupação aparece coerente; `q` encerra; zero arquivos novos | CNT-02/CNT-04 | Requer GUI (`cv2.imshow`) e julgamento visual | `python main.py test/gemini_generated_video_8d21d35f.mp4`; observar overlay de contadores; `q` para sair; confirmar que não há arquivos novos gerados |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending