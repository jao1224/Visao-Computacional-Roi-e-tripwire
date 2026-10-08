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
| 01-01-01 | 01 | 1 | ING-01 | — | N/A | integration/smoke | `python -m pytest tests/test_captura.py::test_abre_video_amostra -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CNT-01 | — | N/A | static/unit | `python -m pytest tests/test_privacidade.py::test_sem_modulos_de_face -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | CNT-03 | — | IDs morrem ao sair do quadro; nada persistido | unit/integration | `python -m pytest tests/test_rastreio.py::test_ids_efemeros -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | ING-03 | — | Nenhum frame/imagem/crop em disco | integration | `python -m pytest tests/test_privacidade.py::test_sem_escrita_em_disco -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_captura.py` — stubs for ING-01 (abre o MP4 de `test/`, lê ≥ 1 frame)
- [ ] `tests/test_privacidade.py` — stubs for ING-03 (snapshot de diretório antes/depois) e CNT-01 (varredura de tokens proibidos nos módulos do produto)
- [ ] `tests/test_rastreio.py` — stubs for CNT-03 (processa ~60 frames, valida `ids` como inteiros e ausência de persistência)
- [ ] `tests/conftest.py` — shared fixtures (caminho do vídeo-amostra, carregamento do modelo)
- [ ] `pip install pytest` — adicionar ao `requirements.txt` ou a um `requirements-dev.txt`

*If none: "Existing infrastructure covers all phase requirements."*

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
