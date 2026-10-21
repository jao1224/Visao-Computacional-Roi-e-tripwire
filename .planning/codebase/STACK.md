# Pilha Tecnológica (Stack)

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas)
Ambiente: venv local em `./.venv/` — usar **sempre** `./.venv/bin/python`.

---

## 1. Stack Implementada (Fases 1 e 2 — em produção hoje)

| Camada | Tecnologia | Versão | Papel |
|---|---|---|---|
| Linguagem | Python | **3.14.4** | Runtime do pipeline (venv `.venv/`) |
| Visão computacional / ML | `ultralytics` | **8.4.121** | YOLO (detecção de corpo) + ByteTrack efêmero; também traz `lap` e `torch` como dependências transitivas |
| Imagem / vídeo | `opencv-python` | **5.0.0.93** | `VideoCapture` (webcam/arquivo), `imshow`, primitivas de desenho e polígonos |
| Matemática / máscaras | `numpy` | **2.5.2** | Máscaras de imagem, `logical_and`, `clip` |
| Associação do tracker | `lap` | **0.5.13** | Solver de atribuição linear usado pelo ByteTrack |
| Configuração | `pyyaml` | **6.0.3** | Leitura segura (`safe_load`) de `config/zonas.yaml` |
| Testes (dev) | `pytest` | `>=8.0` (instalado **9.1.1**) | Suíte de **33 testes** em `tests/` |

### Como instalar

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements-dev.txt   # inclui pytest
```

> ⚠️ O `pip` do sistema pode estar gerenciado por PEP 668 — instale sempre no venv do repositório.

---

## 2. Stack Planejada (Fases 3–7 — ainda NÃO implementada)

| Camada | Tecnologia | Fase | Motivo |
|---|---|---|---|
| Ingestão RTSP | **PyAV** | 6 | `cv2.VideoCapture` corrompe frames RTSP após 15–35 s (pesquisa de 2026-10-08) |
| RTSP de teste | **MediaMTX** | 6 | Servidor RTSP local — exercita produção sem os DVRs reais |
| Banco | **PostgreSQL 18** + `asyncpg` | 3 | Tabelas de configuração + métricas agregadas (sem `sessoes`/`session_traces`) |
| API | **FastAPI** + WebSocket | 4 | Exposição **somente-leitura** de agregados; TTL documentado (art. 16) |
| Dashboard | **React** + **Vite** + **ECharts** | 5 | Ocupação ao vivo, séries, heatmap agregado |
| Ambiente | **docker-compose** | 5 | PostgreSQL + API + dashboard com um comando (`OPS-02`) |

---

## 3. Ferramentas de Desenvolvimento (fora do pipeline)

| Ferramenta | Onde | Observação |
|---|---|---|
| `reportlab` | venv isolado **fora do repositório** (`/tmp/opencode/pdfvenv`) | **Dependência opcional** do gerador do relatório PDF — deliberadamente **fora** do `requirements.txt` do produto |
| Google Colab / Jupyter | `scripts/treinar_crowdhuman_colab.ipynb`, `scripts/setup_colab_ssh.py` | Treino do detector de corpo fora da máquina de desenvolvimento |

---

## 4. Regras de Dependência

1. **Pin exato** (`==`) em `requirements.txt` — reprodutibilidade.
2. `requirements-dev.txt` = `-r requirements.txt` + `pytest>=8.0`.
3. **Dependências de documentação não entram no `requirements.txt` do produto.**
4. `opencv-contrib-python` é **proibido** (traz `cv2.face` — módulo de face).
5. Nenhuma dependência pode escrever mídia em disco por conta própria.
6. Toda dependência nova precisa ser auditada contra o vetor de biometria (LGPD art. 11).

---

## 5. Referências

- Pins atuais: `requirements.txt`, `requirements-dev.txt`
- Onde cada biblioteca é usada: `.planning/codebase/INTEGRATIONS.md`
- Justificativas técnicas: `.planning/research/`
