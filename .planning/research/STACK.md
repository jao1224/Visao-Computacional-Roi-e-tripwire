# Pesquisa de Pilha Tecnológica (Stack Research)

**Domínio:** Plataforma de contagem de pessoas e analytics de fluxo em tempo real (RTSP multi-câmera → YOLO+ByteTrack → PostgreSQL → FastAPI → dashboard)
**Pesquisado em:** 2026-10-08
**Confiança:** ALTA (versões verificadas diretamente nos registros PyPI / npm / GitHub em 2026-10-08; padrões de arquitetura verificados em documentações oficiais e projetos do ecossistema 2025–2026)

> **⚠️ DOCUMENTO DE PESQUISA — DATADO (2026-10-08) E PARCIALMENTE SUPERADO.**
> Preservado como **registro de referência técnica**, não como plano. Índice, mapa de validade e equivalências da numeração antiga: [`README.md`](README.md) (nesta pasta).
> - **Roadmap canônico:** [`../ROADMAP.md`](../ROADMAP.md) — **9 fases**. O roadmap de fases sugerido neste documento é de **6** e **não** é o plano.
> - **Vetos definitivos (mantidos):** MTMCT, Re-ID, `session_traces`/`sessoes`, embeddings de aparência e qualquer persistência de `track_id`/`session_id` estão **fora do escopo para sempre** (LGPD art. 12 §2º). Ignore as seções/patterns/fases que os mencionem. Permitido: associação efêmera em RAM + métricas agregadas.
> - **Escopo e requisitos:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · **estado:** [`../STATE.md`](../STATE.md).
> - **Stack real:** Python **3.14.4** (venv `.venv/`) — a pesquisa fixou 3.12 por causa do `av` 19.x. Estado real: [`../codebase/STACK.md`](../codebase/STACK.md).
> 
> Escopo: Apenas novas camadas (ingestão, rastreio, filas, banco, API, dashboard). O detector existente (`main.py`, YOLO CrowdHuman) está fora do escopo conforme o contexto do milestone.

---

## Pilha Recomendada

### Tecnologias Principais

| Tecnologia | Versão | Propósito | Por que é recomendada |
|------------|---------|---------|---------------------|
| Python | **3.12+** (ou superior) | Ambiente de execução | Compatibilidade com bibliotecas de visão computacional, assincronicidade e ecossistema de IA. |
| Ultralytics YOLO | **8.1+** | Inferência de Detecção | Já utilizado em `main.py` (YOLO CrowdHuman); alta performance e integração nativa com PyTorch. |
| PyTorch | **2.2+** | Backend de Deep Learning | Suporte a GPU CUDA otimizado para inferência de alta velocidade (~320 FPS). |
| PostgreSQL | **16+ / 18** | Banco de Dados Relacional | Confiabilidade, suporte a JSONB para configurações/polígonos e extensibilidade para métricas agregadas. |
| FastAPI | **0.110+** | API Backend | Framework assíncrono de altíssima performance para exposição de métricas (somente-leitura) e documentação automática Swagger. |

### Bibliotecas de Visão Computacional e Processamento de Vídeo

| Biblioteca | Versão | Propósito | Por que é recomendada |
|------------|---------|---------|---------------------|
| OpenCV (`opencv-python`) | **4.9+** | Manipulação de vídeo e overlays | Processamento rápido de frames, redimensionamento e desenho de polígonos ROI em tela. |
| PyAV (`av`) | **12.0+** | Decodificação RTSP | Interface Python robusta para FFmpeg, essencial para ingestão estável de múltiplos fluxos RTSP de câmeras. |
| ByteTrack / Supervision | **Roboflow Supervision 0.19+** | Rastreamento efêmera em RAM | Algoritmo de tracking intra-câmera altamente eficiente e integrado com YOLO. |

### Banco de Dados e Fila

| Biblioteca | Versão | Propósito | Por que é recomendada |
|------------|---------|---------|---------------------|
| SQLAlchemy | **2.0+ (Async)** | ORM / Conexão com banco | Suporte nativo a consultas assíncronas (`asyncpg`) para operação sem gargalos no I/O. |
| asyncpg | **0.29+** | Driver PostgreSQL Async | Driver async de altíssima performance em C para Python. |

---

## Diretrizes de Conformidade LGPD na Pilha
1. **Zero persistência de frames:** Nenhuma imagem ou crop é gravado em disco ou banco.
2. **Sem identificação:** Bibliotecas de reconhecimento facial, embeddings ou biometria são terminantemente proibidas de serem adicionadas às dependências.
3. **Agregação em lote:** A gravação no PostgreSQL ocorre via fila em memória (*batch writer*), isolando o banco do loop de vídeo.
