# Pesquisa de Armadilhas do Domínio (Domain Pitfalls)

**Domínio:** Analytics de vídeo em tempo real / contagem de pessoas / pipelines RTSP (analytics de fluxo em hotelaria, restrito por LGPD)
**Pesquisado em:** 2026-10-08
**Confiança:** MÉDIA-ALTA (ALTA em RTSP/OpenCV, loteamento de banco e modos de falha de contagem — múltiplas fontes independentes incl. docs/issues oficiais; MÉDIA em especificidades de hotel e sincronização de relógio — menos fontes diretas)

> **⚠️ DOCUMENTO DE PESQUISA — DATADO (2026-10-08) E PARCIALMENTE SUPERADO.**
> Preservado como **registro de referência técnica**, não como plano. Índice, mapa de validade e equivalências da numeração antiga: [`README.md`](README.md) (nesta pasta).
> - **Roadmap canônico:** [`../ROADMAP.md`](../ROADMAP.md) — **9 fases**. O roadmap de fases sugerido neste documento é de **6** e **não** é o plano.
> - **Vetos definitivos (mantidos):** MTMCT, Re-ID, `session_traces`/`sessoes`, embeddings de aparência e qualquer persistência de `track_id`/`session_id` estão **fora do escopo para sempre** (LGPD art. 12 §2º). Ignore as seções/patterns/fases que os mencionem. Permitido: associação efêmera em RAM + métricas agregadas.
> - **Escopo e requisitos:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · **estado:** [`../STATE.md`](../STATE.md).
> 
> Contexto do projeto: evolução de um `main.py` existente (YOLO CrowdHuman, ~320 FPS GPU) para uma arquitetura em camadas (ingestão RTSP → YOLO+ByteTrack → filas → PostgreSQL → FastAPI/dashboard).
> Restrições rígidas: **nenhuma detecção facial (LGPD)**, frames nunca persistidos, latência ≤ 5 ms/frame em GPU, **nenhum I/O de banco dentro do loop de vídeo**, logs de acesso à API retidos por 6 meses (Marco Civil Art. 15).

---

## Armadilhas Críticas

### Armadilha 1: Tratar `cv2.VideoCapture` RTSP como leitor confiável e não-bloqueante

**O que acontece:**
O pipeline trava ou degrada silenciosamente após alguns minutos de operação com streams RTSP ao vivo. O OpenCV acumula frames em buffer na biblioteca subjacente (FFmpeg), fazendo com que o stream fique cada vez mais atrasado em relação ao tempo real ("lag" crescendo até congelar ou estourar a memória RAM).

**Por que acontece:**
`cv2.VideoCapture` lê frames de forma síncrona e bloqueante. Se a inferência (YOLO) demorar um pouco mais que o intervalo do frame, o buffer interno enche e o OpenCV continua entregando frames antigos ("stale frames").

**Como evitar:**
- Utilizar uma thread de leitura dedicada (buffer de tamanho 1) que puxa sempre o frame mais recente e descarta os intermediários, ou adotar bibliotecas robustas de streaming como PyAV (`av`).
- Implementar um watchdog de staleness para detectar se o último frame lido tem mais de X segundos.

---

### Armadilha 2: Realizar I/O de Banco de Dados dentro do Loop de Vídeo

**O que acontece:**
O FPS cai vertiginosamente de 300+ FPS para menos de 10 FPS, ou o banco de dados PostgreSQL sofre falhas de conexão por exaustão de pool devido a milhares de inserções por segundo geradas pelas detecções de vídeo.

**Por que acontece:**
Cada chamada síncrona `INSERT` ou `UPDATE` no banco dentro do loop de processamento de quadros adiciona latência de rede/disco (milissegundos), o que destrói o rendimento (*throughput*) do motor de visão computacional.

**Como evitar:**
- **Regra de ouro:** O loop de vídeo **nunca** fala diretamente com o banco de dados.
- Utilizar uma fila em memória (Thread-safe Queue) no Python. O worker de vídeo empacota métricas agregadas na fila, e uma thread/tarefa em lote (*batch writer*) descarrega os dados no PostgreSQL a cada N segundos.

---

### Armadilha 3: Violação acidental da LGPD por persistência de rastreios (Track IDs)

**O que acontece:**
O desenvolvedor armazena o `track_id` gerado pelo ByteTrack junto com o timestamp e a zona no banco de dados para calcular métricas, achando que é anônimo.

**Por que acontece:**
Confusão conceitual: um `track_id` contínuo ao longo do tempo forma uma trilha comportamental (*session trace*), que constitui dado pessoal indireto rastreável (vedado pelo Art. 12 §2º da LGPD).

**Como evitar:**
- O ByteTrack deve ser usado exclusivamente na **memória RAM** de forma efêmera (para estabilizar a contagem da zona no quadro atual).
- No banco de dados, gravar **apenas dados agregados** (ex: contagem total, ocupação média, histogramas de dwell), sem nenhum ID individual.
