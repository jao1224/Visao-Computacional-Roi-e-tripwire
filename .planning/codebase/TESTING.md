# Estratégia e Cobertura de Testes

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas)
**Resultado:** ✅ **33/33 testes verdes** em ~6–10 s

---

## 1. Comando canônico

```bash
./.venv/bin/python -m pytest
```

> ⚠️ **Use sempre o interpretador do venv do repositório.** O `pytest` do sistema falha por falta das dependências do projeto (`ultralytics`, `opencv-python`, `numpy`, `pyyaml`).
>
> Instalação: `./.venv/bin/python -m pip install -r requirements-dev.txt`

---

## 2. Cobertura por arquivo

| Arquivo | Linhas | Testes | Foco |
|---|---:|---:|---|
| `tests/conftest.py` | 32 | — (fixtures) | Fixtures compartilhadas: frames sintéticos, zonas de teste, estados de ocupação |
| `tests/test_captura.py` | 34 | **3** | Abertura de webcam/arquivo, carimbo `capture_ts`, retorno `None` em fonte inválida |
| `tests/test_rastreio.py` | 59 | **3** | Extração de caixas `(id, xyxy, conf)`, guard de `boxes.id is None`, tuplas vazias |
| `tests/test_zona.py` | 261 | **10** | Carga/validação de YAML, **ocupação por ROI**, **interseção de área**, clamp `[0, capacidade]`, resets (diário/inatividade), reconciliação, poda de track states |
| `tests/test_overlay.py` | 41 | **4** | Desenho das ROIs, destaque da interseção, **filtro de caixas fora do ROI**, HUD/card de ocupação |
| `tests/test_main.py` | 39 | **6** | Resolução de fonte (`resolver_fonte`) e de pesos (`resolver_modelo`), montagem do pipeline, wiring do overlay |
| `tests/test_integracao.py` | 247 | **4** | Pipeline ponta a ponta com fonte sintética: captura → rastreio → zona → overlay, sem escrita em disco |
| `tests/test_privacidade.py` | 133 | **3** | **Auditoria LGPD automatizada** (ver abaixo) |
| **Total** | **846** | **33** | |

---

## 3. `tests/test_privacidade.py` — a auditoria LGPD que roda em todo build

Este é o arquivo mais importante da suíte: **transforma os vetos de privacidade em testes que quebram o build**.

| Teste | O que garante |
|---|---|
| Ausência de face/biometria | Nenhum módulo do produto importa `face`, `biometria`, `demografia`, `emocao`; `requirements.txt` não traz `opencv-contrib-python`; nenhum uso de `cv2.face`/`FaceDetectorYN` |
| Nada gravado em disco | O pipeline não chama `cv2.imwrite`, `VideoWriter` ou equivalente; rodar não cria arquivo de imagem |
| Nenhum identificador individual persistido | Não há escrita de `track_id`, `session_id`, `sessoes`, `session_traces`, `embedding`, `rota` ou `jornada` |

**Regra para agentes de IA:** esses testes **não podem ser desabilitados, afrouxados ou pulados**. Se um teste de privacidade falha, a correção é remover o código que viola a política — nunca o teste.

---

## 4. Estratégia de teste por fase

| Fase | O que os testes cobrem | Requisito |
|---|---|---|
| 1 — Fatia vertical | Captura, rastreio efêmero, integração do pipeline, privacidade | ING-01, ING-03, CNT-01, CNT-03 |
| 2 — Contagem por zona | Ocupação por ROI, interseção de área, clamp/reset/reconciliação, overlay | CNT-02, CNT-04 |
| 3 — Persistência | *(planejado)* fila em RAM, batch idempotente, schema sem coluna por-pessoa | API-01, QUA-01 |
| 4 — API | *(planejado)* endpoints somente-leitura, TTL de retenção, logs de 6 meses | API-02..04 |
| 5 — Dashboard | *(planejado)* | DSH-01..02, OPS-02 |
| 6 — Multi-câmera | *(planejado)* reconexão, watchdog, tracker isolado por câmera | ING-02, OPS-01 |
| 7 — Dwell + heatmap | *(planejado)* histograma agregado sem linha por pessoa | DWL-01..02, DSH-03 |
| 8 — Qualidade | *(planejado)* acurácia vs. marcação manual em vídeo de pico | QUA-02, QUA-03 |
| 9 — Conformidade | *(planejado)* auditoria repo-wide (PRV-01) | PRV-01..05, OPS-03 |

---

## 5. Convenções

- Arquivos `tests/test_<módulo>.py` espelham os módulos do raiz.
- Fixtures compartilhadas em `tests/conftest.py`; casos específicos ficam no próprio arquivo.
- Testes que dependem de **modelo** ou **vídeo** ausentes devem `pytest.skip(...)` explicitamente — nunca falhar.
- Testes de privacidade não usam mocks para os módulos auditados: leem o **código-fonte real** do repositório.
- Nenhum teste pode gravar imagem ou vídeo de pessoa em disco — nem como "fixture de debug".

---

## 6. Referências

- Módulos testados: `.planning/codebase/ARCHITECTURE.md`
- Mapeamento requisito → fase: `.planning/REQUIREMENTS.md`
- Execução e resultado: `.planning/STATE.md`
