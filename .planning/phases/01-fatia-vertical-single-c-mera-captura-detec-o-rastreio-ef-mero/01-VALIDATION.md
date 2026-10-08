---
phase: "01"
slug: "fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-08"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Wave 0 instala) |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ING-01 | T-01-02 | Deps sem face/contrib | static | `python -c "import ultralytics, cv2, numpy, lap, pytest"` | ✅ P01 | ⬜ pending |
| 01-01-02 | 01 | 1 | ING-01 | T-01-03 | Fonte arquivo validada | integration | `python -m pytest tests/test_captura.py -x -q` | ✅ P01 | ⬜ pending |
| 01-01-03 | 01 | 1 | ING-03 | T-01-01 | Overlay não grava em disco | unit/static | `python -m pytest tests/test_overlay.py -x -q` | ✅ P01 | ⬜ pending |
| 01-02-01 | 02 | 1 | CNT-01 | T-02-03 | Só corpo (classes=[0]) | static/unit | `python -c "…tracker/classes asserts…"` | ✅ P02 | ⬜ pending |
| 01-02-02 | 02 | 1 | CNT-03 | T-02-01 | IDs efêmeros, nada persistido | unit/integration | `python -m pytest tests/test_rastreio.py -x -q` | ✅ P02 | ⬜ pending |
| 01-03-01 | 03 | 2 | ING-01 | T-03-01 | Fonte CLI validada | unit | `python -m pytest tests/test_main.py -x -q` | ✅ P03 | ⬜ pending |
| 01-03-02 | 03 | 2 | ING-03 | T-03-02 | Laço sem escrita em disco | static | `python -c "…main.py source asserts…"` | ✅ P03 | ⬜ pending |
| 01-04-01 | 04 | 3 | ING-03, CNT-01 | T-04-01/02 | Nada em disco; sem face | integration/static | `python -m pytest tests/test_privacidade.py -x -q` | ✅ P04 | ⬜ pending |
| 01-04-02 | 04 | 3 | CNT-03 | T-04-03 | IDs efêmeros ponta a ponta | integration | `python -m pytest tests/test_integracao.py -x -q` | ✅ P04 | ⬜ pending |
| 01-04-03 | 04 | 3 | ING-01, CNT-01, CNT-03 | — | Verificação visual (backstop) | manual | `python main.py` (webcam + MP4) | ✅ P04 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Criados pelo Plano 01 (Task 1) e preenchidos ao longo dos planos:

- [x] `tests/conftest.py` — fixtures `caminho_video_amostra` e `caminho_modelo` (Plano 01)
- [x] `tests/test_captura.py` — ING-01 (abre o MP4 de `test/`, lê ≥ 1 frame) (Plano 01)
- [x] `tests/test_overlay.py` — desenho in-place sem APIs de escrita (Plano 01)
- [x] `tests/test_rastreio.py` — CNT-01/CNT-03 (~60 frames, IDs inteiros e efêmeros) (Plano 02)
- [x] `tests/test_main.py` — resolução de fonte/modelo (Plano 03)
- [x] `tests/test_privacidade.py` — ING-03 + CNT-01 (Plano 04)
- [x] `tests/test_integracao.py` — CNT-03 ponta a ponta (Plano 04)
- [x] `pytest` em `requirements-dev.txt` (`-r requirements.txt` + `pytest>=8.0`) (Plano 01)

*Marcação `[x]` = atribuído a um plano; o status de execução é atualizado na fase de execução.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Ver caixas de corpo e IDs na tela, sem face | ING-01, CNT-01, CNT-03 | Aceitação visual por natureza | Rodar `python main.py`, abrir `test/gemini_generated_video_8d21d35f.mp4` e webcam (índice 0); confirmar caixas de corpo + IDs estáveis; pressionar `q` para sair |
| Nenhuma face/biometria/demografia detectada | CNT-01 | Fronteira de privacidade exige inspeção do repo + requirements | Busca por tokens `face`/`biometr`/`biometric`/`demograf`/`reconhecimento_facial` nos módulos do produto e `requirements.txt` vem vazia |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
