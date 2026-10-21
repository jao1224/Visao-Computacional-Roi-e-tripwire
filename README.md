# YOLO + LGPD — Visão Computacional para Hotelaria

**Identificação do projeto:** `YOLO + LGPD`  
Detecção de **corpo/silhueta** com YOLO (CrowdHuman) para analytics de fluxo — **zero biometria**, em conformidade com a LGPD.

Sistema que transforma câmeras do hotel em sensores de negócio: contagem, ocupação e (nas próximas fases) permanência por zona. Frames não são gravados; IDs do ByteTrack existem só em RAM.

> **Estado atual (2026-10-21):** Fases **1 e 2 concluídas** (2/9) · **33 testes** verdes · foco em **ocupação por área (ROI)**.
> Roadmap (canônico): [`.planning/ROADMAP.md`](.planning/ROADMAP.md) · Requisitos: [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md) · Contexto: [`.planning/context/`](.planning/context/)

---

## Recorte LGPD (obrigatório)

- Só detecção de corpo — sem face, Re-ID, embedding ou identificação nominal
- Frames voláteis: inferência em memória, sem `imwrite` / gravação de vídeo de pessoas
- Saída apenas agregada (contagens); nenhum `track_id` persistido
- Dependência `opencv-python` (não `opencv-contrib-python`, para não puxar `cv2.face`)
- **Vetado para sempre:** face/biometria, catraca/controle de acesso, MTMCT/Re-ID (inclusive por silhueta), `sessoes`/`session_traces`, IDs persistidos, embeddings, trilha individual, heatmap por indivíduo, gravação de vídeo

Verificado automaticamente por `tests/test_privacidade.py` a cada build.

Contexto e documentação legal: [`.planning/context/`](.planning/context/).
Parecer regulatório: [`PARECER_LGPD_E_MARCO_CIVIL.md`](.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md).
Relatório para a gestão: [`docs/relatorios/`](docs/relatorios/).

---

## Estrutura

```text
Visao-Computacional-Roi-e-tripwire/
├── main.py                 --> Orquestração: captura → rastreio → zonas → overlay
├── captura.py              --> Fonte (webcam/arquivo) + capture_ts
├── rastreio.py             --> YOLO + ByteTrack efêmero (classe 0 = corpo)
├── zona.py                 --> Ocupação ROI + interseção de área + reset/reconciliação
├── overlay.py              --> Caixas filtradas por ROI, HUD, cards de ocupação (in-place)
├── entender_zonas.py       --> Utilitário: gera zonas_visualizacao.png
├── config/
│   ├── data.yaml           --> Dataset (classe: person) — treino
│   └── zonas.yaml          --> ROIs por camera_id (id, tipo, pontos, capacidade)
├── models/                 --> Pesos base (yolo26n.pt) e pesos de face (dívida PRV-03)
├── resultados/best.pt      --> Detector de corpo treinado (CrowdHuman)
├── scripts/                --> Ferramentas de DEV: demarcador de ROI, treino, relatório PDF
├── tests/                  --> 33 testes: privacidade, integração, zonas, overlay, contratos
├── docs/
│   └── relatorios/          --> Relatórios para a gestão (PDF)
└── .planning/              --> Planejamento canônico: roadmap, requisitos, estado,
                                contexto, histórico, mapa do codebase, pesquisa
```

---

## Funcionalidades (Fase 1 + 2)

| Módulo | O que faz |
|--------|-----------|
| **Detecção + Rastreio** | YOLO corpo + ByteTrack em RAM, IDs efêmeros (≤ 15 s) |
| **Ocupação ROI** | Recontagem geométrica frame-a-frame (pé/centro/borda dentro do polígono), com clamp `[0, capacidade]` |
| **Interseção de área** | `Área(Objeto) ∩ Área(ROI)` → % da área da zona efetivamente ocupada, exibido no overlay |
| **Filtro de renderização** | Só desenha (e destaca) quem intersecta a zona configurada |
| **Resets** | Meia-noite local OU vazio > 10 min → zera a ocupação da zona |
| **Reconciliação** | Reabertura de fonte limpa `track_states` inteiro |
| **Tripwire** | Linha bidirecional (ENTROU/SAIU) — **desativado por decisão**: o código existe, comentado, em `zona.py`, `overlay.py` e `main.py` |
| **Overlay** | ROIs (azul alpha 0.2), interseção (vermelho), cards de ocupação e HUD de FPS |
| **Privacidade** | Zero escrita em disco, zero biometria, auditoria automatizada em `tests/test_privacidade.py` |

---

## Como usar

### Inferência em tempo real (webcam ou vídeo)

```bash
./.venv/bin/python main.py                    # webcam padrão (índice 0)
./.venv/bin/python main.py 1                  # índice da câmera
./.venv/bin/python main.py caminho/video.mp4  # arquivo de vídeo
```

Pressione **`q`** para encerrar ou **`r`** para resetar contadores em execução.

### Calibrar / Demarcar Zonas ROI Interativamente (com o mouse)

Para demarcar o polígono de uma zona clicando diretamente na tela da webcam ou de um vídeo:

```bash
# Abre a webcam e permite clicar nos pontos da zona
./.venv/bin/python scripts/demarcar_zona.py 0

# Ou especificando câmera, nome da zona ou arquivo de vídeo
./.venv/bin/python scripts/demarcar_zona.py 0 --camera camera_0 --zona hall
./.venv/bin/python scripts/demarcar_zona.py video.mp4 --camera camera_0 --zona entrada
```

**Recursos e atalhos na janela de calibração:**
- **Clique com Botão Esquerdo:** adiciona um novo vértice no polígono.
- **Clique + Arrastar sobre ponto existente (círculo verde):** edita/move a posição de qualquer ponto sem precisar recomeçar.
- **`a` (Alinhamento Automático):** alinha arestas ortogonais automaticamente (endireita linhas quase horizontais ou verticais).
- **`r` (Retângulo Perfeito):** converte instantaneamente os pontos em um retângulo reto perfeito (bounding box).
- **`u` (Desfazer):** desfaz o último ponto adicionado.
- **`s` (Salvar):** salva as coordenadas em `config/zonas.yaml` e encerra.
- **`c` (Limpar):** apaga todos os pontos.
- **`q` ou ESC:** cancela e sai sem salvar alterações.

### Testes

```bash
./.venv/bin/python -m pytest                  # suite completa de testes (33)
./.venv/bin/python -m pytest tests/test_zona.py -q  # testes de zona e interseção
./.venv/bin/python -m pytest tests/test_privacidade.py -q  # auditoria LGPD
```

> Use sempre `./.venv/bin/python` — o `pytest` do sistema não tem as dependências do projeto.

### Visualizar zonas (sem rodar vídeo)

```bash
./.venv/bin/python entender_zonas.py          # gera zonas_visualizacao.png
```

### Treinar / validar o detector de corpo

```bash
./.venv/bin/python scripts/download_and_convert_crowdhuman.py
./.venv/bin/python scripts/train_body.py
./.venv/bin/python scripts/validate_body.py
```

* **Resolução (`imgsz`):** `640x640`
* **Batch:** `8`
* **Épocas:** `300` com *cosine learning rate decay*

---

## Estado atual (2026-10-21)

| Fase | Status |
|---|---|
| 1 — Fatia vertical single-câmera (captura → detecção → rastreio efêmero) | ✅ Concluída |
| 2 — Contagem por zona e ocupação (ROI + interseção de área) | ✅ Concluída |
| 3 — Persistência PostgreSQL (fila em RAM + escrita em lote) | ⏳ Não iniciada |
| 4 — API FastAPI + conformidade Marco Civil | ⏳ Não iniciada |
| 5 — Dashboard web | ⏳ Não iniciada |
| 6 — Multi-câmera e RTSP (PyAV + MediaMTX) | ⏳ Não iniciada |
| 7 — Dwell e heatmap agregado | ⏳ Não iniciada |
| 8 — Validação de qualidade (marcação manual) | ⏳ Não iniciada |
| 9 — Conformidade LGPD (RIPD/LIA/ROPA, encarregado, incidente) | ⏳ Não iniciada |

**2/9 fases (22%) · 6/27 requisitos concluídos · 33 testes verdes.**

> Nenhuma câmera real com hóspedes deve ser ligada antes do gate da **Fase 9**.

---

## Documentação e relatórios

| Documento | Para quê |
|---|---|
| [`.planning/ROADMAP.md`](.planning/ROADMAP.md) | **Roadmap canônico**: as 9 fases, com metas, dependências e critérios de sucesso |
| [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md) | **Requisitos canônicos** (27) e rastreabilidade requisito → fase |
| [`.planning/STATE.md`](.planning/STATE.md) | Estado de execução do planejamento |
| [`.planning/context/`](.planning/context/) | Contexto: negócio, arquitetura, plantas/câmeras, modelagem do banco, parecer LGPD/Marco Civil, diretrizes e design por fase |
| [`.planning/historico/`](.planning/historico/) | Documentos superados (face-vs-body, MTMCT) — registro histórico, não implementar |
| [`.planning/codebase/`](.planning/codebase/) | Mapa do código: arquitetura, stack, estrutura, testes, riscos, convenções |
| [`docs/relatorios/`](docs/relatorios/) | Relatórios para a gestão do projeto (PDF) |

O relatório de conformidade em PDF é gerado por `scripts/gerar_relatorio_lgpd.py` — que usa `reportlab`, uma **dependência opcional** mantida fora do `requirements.txt` do produto.
