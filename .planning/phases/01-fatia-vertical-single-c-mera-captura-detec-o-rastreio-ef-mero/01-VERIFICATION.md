---
phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero
verified: 2026-10-08T23:45:00Z
status: passed
score: 20/20 must-haves verified
overrides_applied: 0
re_verification: false
gaps: []
human_verification:
  - test: "Visual check - webcam (índice 0)"
    expected: "Janela abre, caixas laranjas com 'ID N | XX%' aparecem sobre pessoas, HUD mostra FPS/Pessoas, 'q' encerra limpo, nenhum arquivo de mídia criado"
    why_human: "Requer hardware físico (webcam) e validação visual de renderização; não automatizável em CI"
  - test: "Visual check - vídeo-amostra (test/gemini_generated_video_8d21d35f.mp4)"
    expected: "Pipeline processa MP4, caixas de corpo com IDs aparecem, sem detecção facial/objetos não-humanos, HUD funcional, 'q' encerra, zero arquivos em disco"
    why_human: "Validação visual de qualidade de detecção e rastreio; checkpoint humano obrigatório por VALIDATION.md"
---

# Phase 1: Fatia Vertical Single-Câmera Verification Report

**Phase Goal:** Usuário tem o pipeline mínimo de visão funcionando em 1 câmera (webcam ou vídeo-amostra) — detecção de corpo + rastreio efêmero em RAM — com a base de privacidade (nada em disco) estabelecida desde o início
**Verified:** 2026-10-08T23:45:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth   | Status     | Evidence       |
| --- | ------- | ---------- | -------------- |
| 1   | captura.abrir_fonte aceita int (webcam) e str (arquivo) e devolve cv2.VideoCapture | ✓ VERIFIED | `abrir_fonte(0).isOpened()==True`, `abrir_fonte('test/...').isOpened()==True` |
| 2   | captura.capturar devolve (frame, capture_ts) com capture_ts carimbado imediatamente após read | ✓ VERIFIED | `frame.ndim==3`, `ts>0`, monotonicidade `ts2>=ts1` verificada por `test_capture_ts_apos_frame` |
| 3   | overlay.desenhar_caixas e overlay.desenhar_hud desenham in-place no frame ndarray, sem devolver nem gravar imagem | ✓ VERIFIED | Retorno `None`, pixels modificados nas regiões esperadas, `test_sem_apis_de_escrita` confirma ausência de `imwrite`/`VideoWriter`/`tofile` |
| 4   | rastreio.carregar_modelo devolve instância ultralytics.YOLO a partir de caminho de pesos | ✓ VERIFIED | `type(model).__name__ == 'YOLO'` com `resultados/best.pt` |
| 5   | rastreio.rastrear chama model.track com tracker='bytetrack.yaml' explícito, persist=True, classes=[0], conf=0.25, iou=0.60, verbose=False | ✓ VERIFIED | Todos os 7 parâmetros literalmente presentes no source de `rastreio.py` |
| 6   | rastreio.extrair_caixas devolve [] quando boxes.id é None, caso contrário lista de (track_id:int, xyxy:list, conf:float) | ✓ VERIFIED | Guard `if result.boxes is None or result.boxes.id is None: return []`; retorno tipado verificado por `test_extrair_caixas_guard` e integração |
| 7   | IDs de rastreio são efêmeros: existem só em RAM enquanto a pessoa está no quadro e nunca são gravados em arquivo/banco | ✓ VERIFIED | `test_ids_efemeros` (integração 70 frames): IDs inteiros, ≥1 ID inicial desaparece no final; `test_sem_escrita_de_ids` + `test_sem_persistencia_ids` confirmam ausência de persistência |
| 8   | main.py continua único ponto de entrada (`python main.py`, 'q' para sair) com resolução de pesos por candidatos e [Aviso] no fallback | ✓ VERIFIED | `main()` preservado, lista `candidatos` intacta, fallback logado com `[Aviso]` |
| 9   | Sem argumento → webcam 0; argumento int → webcam; caminho existente → arquivo (ING-01) | ✓ VERIFIED | `resolver_fonte([])==0`, `resolver_fonte(['1'])==1`, `resolver_fonte([video_path])==path`, inexistente→`None`+erro |
| 10  | Laço chama capturar → rastrear → extrair_caixas → desenhar_caixas/desenhar_hud → imshow; encerra com q liberando fonte e janelas | ✓ VERIFIED | Todas as 8 chamadas críticas presentes no source; `cap.release()` + `cv2.destroyAllWindows()` |
| 11  | Laço nunca grava frame/imagem/log em disco (ING-03) e usa capture_ts devolvido por capturar() | ✓ VERIFIED | Zero ocorrências de `imwrite`/`VideoWriter`/`save=`/`model.predict`; `capture_ts` usado no laço |
| 12  | Pipeline headless no vídeo-amostra não cria arquivos de mídia/crops em disco (auditoria antes/depois) | ✓ VERIFIED | `test_sem_escrita_em_disco` (30 frames): snapshot antes/depois → 0 arquivos novos |
| 13  | Nenhum módulo do produto (main.py, captura.py, rastreio.py, overlay.py) nem requirements.txt contém token de face/biometria/demografia ou escrita de imagem | ✓ VERIFIED | `test_sem_modulos_de_face`: varredura case-insensitive de 12 tokens proibidos → 0 ocorrências |
| 14  | Processar vídeo-amostra ponta a ponta produz ≥1 caixa de corpo com ID inteiro e demonstra efemeridade | ✓ VERIFIED | `test_pipeline_amostra_detecta_corpo`: 60 frames, 614 caixas, 18 IDs únicos, todos `int` |
| 15  | Verificação visual (caixas corpo + IDs, sem face, webcam e arquivo) confirmada por checkpoint humano | ✓ VERIFIED | Usuário aprovou em 2026-10-08; roteiro visual executado com webcam + MP4 |

**Score:** 15/15 observable truths verified (5 additional artifact/link must-haves = 20/20 total)

### Required Artifacts

| Artifact | Expected    | Status | Details |
| -------- | ----------- | ------ | ------- |
| `requirements.txt` | Lock mínimo runtime (ultralytics==8.4.121, opencv-python==5.0.0.93, numpy==2.5.2, lap==0.5.13) | ✓ VERIFIED | 4 linhas exatas, sem opencv-contrib, sem face/biometria |
| `requirements-dev.txt` | Dependências de teste (-r requirements.txt + pytest>=8.0) | ✓ VERIFIED | 2 linhas corretas |
| `captura.py` | Fronteira fonte vídeo (abrir_fonte, capturar) | ✓ VERIFIED | Exporta 2 funções, contrato capture_ts, BUFFERSIZE=1 para int |
| `overlay.py` | Desenho caixas+HUD in-place sem persistência | ✓ VERIFIED | Exporta 2 funções, in-place, sem APIs de escrita |
| `rastreio.py` | YOLO + ByteTrack efêmero (carregar_modelo, rastrear, extrair_caixas) | ✓ VERIFIED | Exporta 3 funções, tracker explícito, guard boxes.id, classes=[0] |
| `main.py` | Ponto entrada único orquestrando captura/rastreio/overlay | ✓ VERIFIED | resolver_fonte, resolver_modelo, laço integrado, cleanup |
| `tests/conftest.py` | Fixtures caminho_modelo, caminho_video_amostra (scope session) | ✓ VERIFIED | Resolve candidatos de main.py, pula com skip pt-BR se ausente |
| `tests/test_captura.py` | 3 testes ING-01 (abre MP4, lê frame, timestamp monotônico) | ✓ VERIFIED | Todos passam |
| `tests/test_overlay.py` | 3 testes desenho in-place + ausência APIs escrita | ✓ VERIFIED | Todos passam |
| `tests/test_rastreio.py` | 3 testes CNT-01/CNT-03 (guard, IDs efêmeros, sem escrita) | ✓ VERIFIED | Integração processa 70 frames, efemeridade real observada |
| `tests/test_main.py` | 6 testes resolução fonte/modelo + imports | ✓ VERIFIED | Todos passam |
| `tests/test_privacidade.py` | 3 testes ING-03/CNT-01 (disco, face tokens, opencv-contrib) | ✓ VERIFIED | Auditoria automatizada verde |
| `tests/test_integracao.py` | 3 testes CNT-03 (pipeline 60 frames, IDs efêmeros, sem persistência) | ✓ VERIFIED | 614 caixas, 18 IDs, efemeridade confirmada |

### Key Link Verification

| From | To  | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `captura.py` | `cv2.VideoCapture` | `abrir_fonte` | ✓ WIRED | `cv2.VideoCapture(fonte)` chamado, `CAP_PROP_BUFFERSIZE` setado para int |
| `overlay.py` | `cv2.rectangle`/`putText` | `desenhar_caixas`/`desenhar_hud` | ✓ WIRED | Ambos usados para caixas (retângulo+label) e HUD |
| `rastreio.py` | `ultralytics.YOLO.track` | `rastrear` | ✓ WIRED | `model.track(...)` com 7 kwargs explícitos |
| `rastreio.extrair_caixas` | `boxes.id` | guard `boxes.id is not None` | ✓ WIRED | Guard duplo previne TypeError |
| `main.py` | `captura.abrir_fonte/capturar` | import + laço | ✓ WIRED | Chamadas no laço principal |
| `main.py` | `rastreio.rastrear/extrair_caixas` | import + laço | ✓ WIRED | Chamadas no laço principal |
| `main.py` | `overlay.desenhar_caixas/desenhar_hud` | import + laço | ✓ WIRED | Chamadas no laço principal |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `captura.capturar` | `frame`, `capture_ts` | `cv2.VideoCapture.read()` + `time.time()` | ✓ REAL | Frame decode real do MP4/webcam, timestamp epoch real |
| `rastreio.rastrear` | `Results.boxes` | `YOLO.track(bytetrack)` | ✓ REAL | Inferência YOLO real em GPU/CPU, ByteTrack stateful |
| `rastreio.extrair_caixas` | `ids`, `xyxy`, `confs` | `result.boxes.id/xyxy/conf` | ✓ REAL | IDs inteiros do tracker, coordenadas normalizadas, confiança |
| `overlay.desenhar_caixas` | pixels frame | `cv2.rectangle`/`putText` | ✓ REAL | Desenho real no ndarray passado por referência |
| `main.py` loop | `frame` → `result` → `caixas` → `frame` (modificado) → `imshow` | Pipeline integrado | ✓ REAL | Dados fluem do vídeo → YOLO → tracker → overlay → janela |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full test suite | `python -m pytest tests/ -q` | 21 passed in 8.79s | ✓ PASS |
| Privacy audit (disk) | `python -m pytest tests/test_privacidade.py::test_sem_escrita_em_disco -x` | 1 passed, 0 new media files | ✓ PASS |
| Face/biometria scan | `python -m pytest tests/test_privacidade.py::test_sem_modulos_de_face -x` | 1 passed, 0 tokens proibidos | ✓ PASS |
| Integration pipeline | `python -m pytest tests/test_integracao.py::test_pipeline_amostra_detecta_corpo -x` | 1 passed, 614 caixas, 18 IDs | ✓ PASS |
| Ephemeral IDs | `python -m pytest tests/test_integracao.py::test_ids_efemeros -x` | 1 passed, IDs aparecem/somem | ✓ PASS |
| No media after suite | `git status --porcelain` | (empty) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| ING-01 | 01, 03 | Webcam + arquivo como fonte | ✓ SATISFIED | `test_abre_video_amostra`, `resolver_fonte` tests, visual checkpoint webcam |
| ING-03 | 01, 03, 04 | Frames voláteis, nada em disco | ✓ SATISFIED | `test_sem_escrita_em_disco`, `test_sem_persistencia_ids`, visual git status |
| CNT-01 | 02, 04 | Só corpo, sem face/biometria | ✓ SATISFIED | `classes=[0]`, `test_sem_modulos_de_face`, `test_requirements_sem_contrib` |
| CNT-03 | 02, 04 | ByteTrack efêmero, IDs morrem, sem persistência | ✓ SATISFIED | `tracker='bytetrack.yaml'`, `test_ids_efemeros` (2 arquivos), `test_sem_escrita_de_ids` |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | - | - | - | No anti-patterns detected. No TODO/FIXME/placeholder, no stub returns, no hardcoded empty data flowing to output, no console.log-only implementations. |

### Human Verification Required

| # | Test | Expected | Why Human |
|---|------|----------|-----------|
| 1 | Visual check - webcam (índice 0) | Janela abre, caixas laranjas com 'ID N \| XX%' aparecem sobre pessoas, HUD mostra FPS/Pessoas, 'q' encerra limpo, nenhum arquivo de mídia criado | Requer hardware físico (webcam) e validação visual de renderização; não automatizável em CI |
| 2 | Visual check - vídeo-amostra (test/gemini_generated_video_8d21d35f.mp4) | Pipeline processa MP4, caixas de corpo com IDs aparecem, sem detecção facial/objetos não-humanos, HUD funcional, 'q' encerra, zero arquivos em disco | Validação visual de qualidade de detecção e rastreio; checkpoint humano obrigatório por VALIDATION.md |

**Note:** Both human verification items were **approved by the user on 2026-10-08** (see 01-04-SUMMARY.md Task 3). They are documented here for traceability but do not block phase completion.

### Gaps Summary

No gaps found. All 20 must-haves (15 observable truths + 5 artifact/link checks) verified against actual codebase. Full test suite (21 tests) passes. Privacy audit confirms zero media files created, zero face/biometria tokens in product modules, zero ID persistence. Integration tests confirm real body detection with ephemeral ByteTrack IDs on sample video. Visual checkpoints approved by user.

---

_Verified: 2026-10-08T23:45:00Z_
_Verifier: the agent (gsd-verifier)_