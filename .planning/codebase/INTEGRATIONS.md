# Integrações Externas

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas)

---

## 1. Integrações Existentes (em produção)

| Integração | Versão | Uso no código | Onde |
|---|---|---|---|
| **Ultralytics** (`ultralytics`) | `8.4.121` | YOLO de corpo + **ByteTrack** (`tracker='bytetrack.yaml'`, `conf=0.25`, `iou=0.60`, `classes=[0]`) | `rastreio.py`, `main.py` |
| **OpenCV** (`opencv-python`) | `5.0.0.93` | `VideoCapture` (webcam/arquivo), `imshow`/`waitKey`, `fillPoly`, `pointPolygonTest`, `boundingRect`, `rectangle`, `putText`, `addWeighted` | `captura.py`, `zona.py`, `overlay.py`, `main.py` |
| **NumPy** (`numpy`) | `2.5.2` | Máscaras `(H, W)`, `logical_and`, `clip`, `isfinite`, `asarray` | `zona.py`, `overlay.py` |
| **lap** (`lap`) | `0.5.13` | Associação do tracker (dependência do ByteTrack) | via `ultralytics` |
| **PyYAML** (`pyyaml`) | `6.0.3` | `yaml.safe_load` da configuração de zonas | `zona.py` |
| **pytest** (`pytest`) | `>=8.0` (instalado 9.1.1) | Suíte de 33 testes | `tests/` |

### Fontes de vídeo suportadas hoje
- **Webcam** por índice (`main.py 0`, `main.py 1`) — `cv2.VideoCapture(int)` com `CAP_PROP_BUFFERSIZE = 1`.
- **Arquivo de vídeo local** (`main.py caminho/video.mp4`).
- ⚠️ **RTSP não é suportado de forma confiável**: `cv2.VideoCapture` corrompe frames RTSP após 15–35 s. A ingestão RTSP é a **Fase 6**, com **PyAV**.

### Pesos do modelo (resolvidos por `main.py`, em ordem)
1. `resultados/best.pt` — detector de corpo treinado em CrowdHuman ✅ (versionado)
2. `runs/detect/train_crowdhuman_body/weights/best.pt`
3. `models/best.pt`
4. `models/yolo26n.pt`
5. `yolo26n.pt`

---

## 2. Integrações Planejadas (Fases 3–7 — ainda NÃO implementadas)

| Integração | Fase | Papel | Observações |
|---|---|---|---|
| **PostgreSQL 18** + `asyncpg` | 3 | Config (câmeras, zonas) + métricas agregadas (`metricas_fluxo_zona`, `dwell_agregado_zona`, `heatmap_densidade_camada`) | **Sem** `sessoes`/`session_traces`; sem I/O dentro do loop de vídeo |
| **Fila em RAM + batch writer idempotente** | 3 | Desacopla o loop de vídeo do banco (UUID por lote) | Critério: latência ≤ 5 ms/frame |
| **FastAPI** (+ WebSocket) | 4 | API **somente-leitura** de contagem, ocupação, séries, histogramas e heatmap agregado; guard que impede expor dado por-pessoa | TTL documentado (art. 16) |
| **Logs de acesso** | 4 | IP/data/hora/ação retidos **exatamente 6 meses** sob sigilo (Marco Civil art. 15) | Mínimo funcional |
| **React + Vite + ECharts** | 5 | Dashboard de ocupação ao vivo, séries e heatmap | WebSocket para tempo real; indicador de frescor do dado |
| **docker-compose** | 5 | PostgreSQL + API + dashboard sobem com um comando | `OPS-02` |
| **PyAV** | 6 | Ingestão RTSP multi-stream (substitui `cv2.VideoCapture` para RTSP) | Backoff exponencial + watchdog de staleness |
| **MediaMTX** | 6 | Servidor RTSP **local** de teste — exercita produção sem os DVRs reais | Tracker estritamente por câmera |
| **Jupyter/Colab** | treino | `scripts/treinar_crowdhuman_colab.ipynb` + `scripts/setup_colab_ssh.py` | Fora do pipeline |

---

## 3. Integrações Proibidas (veto permanente)

| Integração | Motivo |
|---|---|
| Detecção/reconhecimento **facial**, biometria, demografia, emoção | LGPD art. 11 (dado sensível) — sem base legal para analytics |
| **MTMCT / Re-ID / associação entre câmeras** (inclusive por silhueta ou aparência) | LGPD art. 12 §2º (perfil comportamental) |
| `opencv-contrib-python` (traz `cv2.face`) | Introduziria módulo de face na dependência |
| Qualquer armazenamento de **frame, imagem, crop ou vídeo** | LGPD art. 6º III (minimização) |
| **PMS/BI** com dados por pessoa | V2 só permite integração via **API de agregados** (V2-03) |

---

## 4. Referências

- Dependências pinadas: `requirements.txt`, `requirements-dev.txt`
- Stack completa: `.planning/codebase/STACK.md`
- Arquitetura-alvo: `docs/DOCUMENTACAO_PROJETO_E_LGPD/02_ARQUITETURA_TECNICA_E_ENGENHARIA.md`
