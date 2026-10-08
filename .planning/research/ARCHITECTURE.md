# Architecture Research

**Domain:** Real-time video analytics / people-counting (hotel people-flow)
**Researched:** 2026-10-08
**Confidence:** HIGH (pipeline shape, threading, zone logic) / MEDIUM (MTMCT production practice, build order)

## Standard Architecture

### System Overview

Surveyed ~12 independent production-grade people-counting / video-analytics
projects (GitHub) + academic MTMCT literature + official Roboflow/Ultralytics
guides. They all converge on the **same shape**, which validates the 5-layer
model in `02_ARQUITETURA_TECNICA_E_ENGENHARIA.md`. The real finding is that
the 5 layers hide **two loops that must never touch**:

```
┌────────────────────────── HOT LOOP (RAM only, ≤5 ms/frame) ──────────────────────────┐
│                                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │  INGESTÃO    │   │  MOTOR       │   │  ANALYTICS   │   │  SESSÃO / MTMCT      │   │
│  │  CameraSrc ×N│──▶│  YOLO+Byte-  │──▶│  Zonas/ROI/  │──▶│  Re-ID efêmero +     │   │
│  │  (thread/cam)│   │  Track ×N    │   │  tripwire    │   │  fusão global        │   │
│  │  1 tracker   │   │  (1 por cam) │   │  dwell       │   │  (TTL em RAM)        │   │
│  └──────────────┘   └──────────────┘   └──────┬───────┘   └──────────┬───────────┘   │
│        ▲ frames      ▲ tracks                │ eventos              │ session_id    │
│        │             │                       ▼                      ▼               │
│  ┌──────┴─────────────┴───────────────────────────────────────────────────────────┐  │
│  │              BUFFER DE EVENTOS + SESSION STATE (thread-safe, em memória)      │  │
│  └───────────────────────────────────────┬───────────────────────────────────────┘  │
└──────────────────────────────────────────┼──────────────────────────────────────────┘
                                           │  batch upsert / worker (a cada poucos s)
┌──────────────────────────────────────────▼──────────────────────────────────────────┐
│  COLD PATH (I/O, tolera latência)                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │  FILA ASSÍN- │──▶│  PostgreSQL  │──▶│  FastAPI     │──▶│  Dashboard           │  │
│  │  CRONA +     │   │  zonas/cams/ │   │  REST/WS     │   │  ocupação, heatmap,  │  │
│  │  batch writer│   │  sessões/    │   │  (read-only) │   │  séries temporais    │  │
│  └──────────────┘   │  métricas    │   └──────────────┘   └──────────────────────┘  │
│                     └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

Única borda invertida (esquerda): configuração (polígonos de zona, câmeras)
criada no dashboard → PostgreSQL → recarregada pelo pipeline. Nunca o contrário.
```

**The one structural rule every working system obeys:** frames and inferences
never leave RAM; only *discrete events* (entrada/saída/dwell/sessão) cross into
the persistence path. Doc 02 §3 and doc 08 already say this — the research
confirms it is the load-bearing constraint, not a nicety.

### Component Responsibilities

| Component | Responsibility (owns) | Talks to → | Typical Implementation |
|-----------|----------------------|------------|------------------------|
| **Fonte de vídeo** (`CameraSrc`) | Conexão, reconexão, frescor do frame. *Não sabe o que é modelo.* | → Motor | Thread por câmera, slot "último frame" (`threading.Lock` + `frame.copy()`), `CAP_PROP_BUFFERSIZE=1`, backoff exponencial, watchdog |
| **Motor visão** | Estado de trilhas **por câmera** (1 tracker = 1 câmera). Produz `track_id` estável. | ← Fonte; → Analytics | YOLO (Ultralytics) + ByteTrack, um objeto `Tracker` por stream; frame-skip para multiplexar GPU |
| **Analytics de zona** | Polígonos ROI, tripwires, timers de dwell, delta de ocupação. Função pura: `TrackUpdate + config → Evento` | ← Motor; → Buffer/Fila | `cv2.pointPolygonTest`, estado por `track_id` (`{track_id: ts_entrada}`), histerese na tripwire |
| **Sessão / MTMCT** | Identidade global (session_id), TTL, fusão inter-câmeras | ← Analytics/tracklets; → Buffer | Fila de tracklets + embeddings de aparência efêmeros + grafo de câmeras adjacentes |
| **Buffer/Fila assíncrona** | Desacoplar hot loop do banco. Backpressure. | ← Sessão/Analytics; → PG | `queue.Queue`/`asyncio` em processo; Redis/Kafka só se processos separados |
| **Persistência** | Schema, batch upsert, agregados. **Nunca** chamada do hot loop. | ← Fila; → API | PostgreSQL + JSONB (polígonos), escritor em lote a cada N segundos |
| **API** | Leitura (REST/WS) + logs de acesso 6 meses. **Não** chama o pipeline. | ← PG; → Dashboard | FastAPI, endpoints de ocupação/séries |
| **Dashboard** | Exibição. Único componente com UI. | ← API | Web; WS ou polling curto para tempo real |

## Recommended Project Structure

Aligns with the existing repo (root `main.py`, pt-BR). No `src/` convention
exists yet, so a flat package root is the lowest-friction choice:

```
<raiz>/
├── main.py                    # já existe — vira CLI/entrypoint
├── nucleo/                    # contrato compartilhado SEM dependência de CV
│   ├── config.py              # carrega YAML/env, valida zonas/câmeras
│   ├── eventos.py             # dataclasses: TrackUpdate, EventoZona, EventoSessao
│   └── filas.py               # buffer thread-safe + batch writer
├── ingestao/                  # Layer 1
│   ├── base.py                # Protocol/ABC FonteVideo
│   ├── webcam.py              # v1 (dev)
│   ├── arquivo.py             # vídeos-amostra (v1, determinístico p/ testes)
│   └── rtsp.py                # v2+: reconexão, timeout, ffmpeg fallback
├── motor/                     # Layer 2
│   ├── detector.py            # wrapper YOLO CrowdHuman (extraindo de main.py)
│   ├── tracker.py             # ByteTrack, instância POR câmera
│   └── pipeline.py            # frame → detections → tracks (loop quente)
├── analytics/                 # Layer 3 (parte 1: lógica pura)
│   ├── zonas.py               # polígonos, ponto-âncora, teste de pertinência
│   ├── tripwire.py            # contagem entrada/saída + histerese
│   ├── dwell.py               # tempo por zona (dict track_id → ts)
│   └── heatmaps.py            # acumulador de densidade
├── sessoes/                   # Layer 3 (parte 2: MTMCT — depois)
│   ├── gerenciador.py         # sessões ativas, TTL 15 min, lock
│   ├── features.py            # embedding de aparência (corpo, efêmero)
│   └── fusao.py               # topologia de câmeras + cosseno → session_id
├── persistencia/              # Layer 4
│   ├── modelos.py             # SQLAlchemy/Tortoise (schema doc 06)
│   └── escritor.py            # batch upsert, retry
├── api/                       # Layer 5
│   ├── app.py                 # FastAPI
│   ├── rotas/                 # zonas, câmeras, ocupação, séries
│   └── logs_acesso.py         # Marco Civil Art. 15
└── dashboard/                 # Layer 5 (frontend)
```

### Structure Rationale

- **`nucleo/` separado de `motor/`:** os tipos de evento são o contrato entre
  o hot loop e o cold path. Testáveis sem GPU, sem OpenCV, sem câmera.
- **`analytics/` puro:** toda a lógica de zona/dwell é função de
  `(tracks, config)`. É a única parte que se pode testar com fixtures de
  vídeo e asserts determinísticos — e é onde os bugs de contagem moram.
- **`sessoes/` separado e *por último*:** MTMCT é um consumidor de tracklets,
  não parte do loop de inferência. Mantê-lo isolado permite shippar
  contagem por zona sem ele (e é o módulo mais incerto do projeto).
- **`ingestao/` com Protocol:** é o que permite começar com webcam/arquivo e
  trocar por RTSP depois **sem tocar em mais nada** — validado pelo padrão
  `detectors/`/`trackers/` registry de projetos reais.

## Architectural Patterns

### Pattern 1: Captura threaded com slot "último frame" (producer-consumer)

**What:** Uma thread por câmera lê continuamente e grava só o frame mais
recente numa variável protegida por lock; o consumidor pega `frame.copy()`.
**When to use:** Sempre que houver mais de uma câmera ou inferência mais lenta
que o stream. É *o* padrão da literatura — Roboflow, Samaritan, QEngineering,
dezenas de repositórios convergem.
**Trade-offs:** Descarta frames (correto para analytics — processar frame velho
é pior que descartar); precisa de lock (custo irrisório vs. inferência).

```python
class CameraStream:                      # fundido de 4 fontes independentes
    def __init__(self, source):
        self._frame = None; self._lock = threading.Lock(); ...

    def _read_loop(self):                # thread dedicada
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self._reconnect_with_backoff(); continue
            with self._lock:
                self._frame = frame      # sobrescreve o anterior

    def read(self):                      # nunca bloqueia
        with self._lock:
            return None if self._frame is None else self._frame.copy()
```

### Pattern 2: Buffer de eventos + batch upsert (nunca I/O no loop)

**What:** O hot loop produz eventos discretos (`ENTROU`, `SAIU`, `DWELL_TICK`,
`tessela_heatmap`) para uma fila em memória; um worker separado faz upsert em
lote a cada poucos segundos.
**When to use:** Sempre. Doc 02 §3 e doc 08 já decretam; toda produção
consultada faz igual (SQLite/PG/TimescaleDB via writer assíncrono).
**Trade-offs:** Perde no máximo o buffer em caso de crash (aceitável para
métricas agregadas); ganha o loop de vídeo inteiro.

```python
# nucleo/filas.py — o evento é o ÚNICO objeto que cruza a fronteira
@dataclass(frozen=True)
class EventoZona:
    camera_id: int; zona_id: int
    tipo: Literal["ENTROU", "SAIU"]
    track_id: int; session_id: int | None
    ts: datetime; evento_id: str        # UUID → idempotência no consumer
```

**Idempotência obrigator:** reprocessar um lote após crash não pode duplicar
contagem — `evento_id` (UUID) como chave. Padrão confirmado no design HLD de
ocupação (at-least-once + idempotência via `event_id`).

### Pattern 3: Máquina de estado por `track_id` para zona/dwell (não por frame)

**What:** Contagem e dwell vivem num dict `{track_id: estado}`; só o
**delta** (`False→True` = entrada) gera evento. Nunca "quantas caixas estão
na zona agora".
**When to use:** Sempre — é a diferença entre contar pessoas e contar
deteções (que oscilam).
**Trade-offs:** Precisa de `track_id` estável → **ByteTrack é pré-requisito
de analytics de zona**, não opcional. Dict precisa de limpeza (TTL / track
encerrado) senão vaza memória.

```python
# analytics/dwell.py — espelha o bloco oficial time_in_zone do Roboflow
def atualizar(estado: dict[int, datetime], track_id: int,
              dentro: bool, ts: datetime, reset_ao_sair=True):
    if dentro and track_id not in estado:
        estado[track_id] = ts                       # entrada confirmada
    elif not dentro and track_id in estado and reset_ao_sair:
        del estado[track_id]                        # saída → fechar evento
```

**Âncora do ponto:** testar o **centro-inferior** da caixa (pés), não o
centro — pessoas cortadas pela borda inferior da imagem dão contagem errada
com centro. Referência: `triggering_anchor` do Roboflow `time_in_zone`.

**Histerese na tripwire:** zona morta de ~5% da altura do frame ao redor da
linha; o estado só é confirmado quando o centróide cruza completamente o
limite oposto. Sem isso, jitter de centróide gera eventos `ENTROU/SAIU`
em rajada (encontrado em `mrazza/cctv-home-occupancy`).

### Pattern 4: MTMCT em 3 fases, desacoplado do loop de inferência

**What:** (1) rastreamento local ByteTrack → tracklets; (2) extração de
embedding de aparência **de corpo inteiro** por tracklet; (3) fusão global
por restrição topológica + similaridade cosseno → `session_id`.
**When to use:** Só quando contagem por zona single-camera já está estável.
**Trade-offs:** online (janela temporal deslizante) é obrigatório para
ocupação em tempo real; offline (pós-processamento por correlação-clustering)
é mais preciso mas só serve para relatórios. Recomendação: **online com
janela**, aceitando IDF1 menor.

```python
# sessoes/fusao.py — lógica de associação (doc 05 §3, validada pela literatura)
def candidatos(novo_tracklet, abertos, grafo_caminhas, ttl=timedelta(minutes=15)):
    for s in abertos:
        if s.camera_id == novo_tracklet.camera_id:   # mesma câmera → já resolvido
            continue
        if nao_adjacente(grafo_caminhas, s.camera_id, novo_tracklet.camera_id):
            continue                                  # restrição topológica
        if abs(s.ultimo_ts - novo_tracklet.ts) > tempo_transito_max(...):
            continue                                  # inviabilidade física
        if distancia_cosseno(s.media_embedding, novo_tracklet.embedding) < TAU:
            yield s                                    # match → mesmo session_id
```

Evidência académica convergente (MEDIUM-HIGH): restrição topológica/temporal
é "crucial clue" em MTMCT (LAAM ICCV'21, ReidTrack CVPRW'23, TCLM); Re-ID puro
funciona mas erra mais; **feature bank** com vários embeddings por pessoa
(por pose/ângulo) reduz trocas de identidade sob oclusão (CVPRW'24, 2º lugar
AI City) — vale copiar, é barato.

**Sem face:** Re-ID de pessoa é *por natureza* de corpo inteiro — os datasets
padrão (Market-1501, DukeMTMC) são silhuetas de corpo. Nenhum dos métodos
citados usa face. Zero conflito com o escopo LGPD do projeto.

**LGPD — ressalva de projeto (MEDIUM):** embedding de aparência corporal é
dado pessoal se permitir reidentificação. Mitigação já prevista no doc 05
(`efêmero`, TTL 15 min, RAM) — reforçar como invariante de arquitetura: o
vetor **nunca** toca disco e some com a sessão.

### Pattern 5: Detector e tracker como registries/Protocol trocáveis

**What:** `BaseDetector`/`BaseTracker` (Protocol) + registro de backend;
YoloDetector e ByteTrack são as únicas implementações hoje.
**When to use:** Vale a pena desde já — é o mecanismo que permitirá
adicionar ONNX/TensorRT, RTSP ou Re-ID **sem tocar no resto** (padrão
literal de `sid-2672/Video-analytics-pipeline` e `yolo26-analytics`).
**Trade-offs:** ~meia tarde de trabalho; evita refatoração futura.

## Data Flow

### Hot path (por frame, direção única)

```
Câmera/Webcam/Arquivo
   │  thread própria, sobrescreve frame antigo
   ▼
FonteVideo.read() ──(frame + camera_id + ts)──▶ Pipeline.detect()
   │                                                │
   │                                    YOLO → detections (bboxes)
   │                                                ▼
   │                                    Tracker[camera].update()
   │                                    (1 instância POR câmera)
   │                                                │
   │                                    tracks: track_id, bbox, ts
   │                                                ▼
   │                          Zonas.testar(track, polígonos) → dentro?
   │                          Tripwire.cruzo?(centróide, histerese)
   │                          Dwell.atualizar(estado[track_id])
   │                                                │
   │                                    EventoZona / EventoSessao
   │                                                ▼
   │                                   Buffer thread-safe (append)
   ▼                                                │
 frame descartado (LGPD: nunca persistido)         │
```

### Cold path (a cada N segundos / lote, direção única)

```
Buffer ──drain──▶ Fila ──worker──▶ batch upsert ──▶ PostgreSQL
                                                          │
                            ┌─────────────────────────────┤
                            ▼                             ▼
                    FastAPI (read-only)          escritor de agregados
                    /api/v1/zonas/{id}/ocupacao  (metricas_fluxo_zona,
                    /api/v1/series?zona=…&de=…    heatmaps, prefix-sum)
                            │
                            ▼
                    Dashboard (REST + WS/polling curto)
```

### Key Data Flows

1. **Contagem por zona:** track_id cruza tripwire → `EventoZona(ENTROU|SAIU)`
   → buffer → lote → `metricas_fluxo_zona` → API → dashboard. *Delta*, não
   gauge, é a fonte de verdade; ocupação atual = prefix-sum dos deltas.
2. **Dwell time:** `track_id` entra em ROI → timestamp em RAM → tick/saída →
   evento `DWELL` → agregação no banco. O timer **vive em RAM**, o banco só
   recebe fechamentos e agregados.
3. **Heatmap:** cada track dentro de zona contribui para
   `trilha_ponto(zona, célula, ts)` → acumulador → densidade por célula.
   Nunca por frame: só quando o track se move (event-driven).
4. **Jornada inter-câmera:** tracklets encerrados + embedding → fusão →
   `session_id` → attach aos eventos já emitidos → `sessoes.session_traces`.
5. **Config (única borda invertida):** dashboard cria/edita polígono →
   `zonas.polygon JSONB` → pipeline recarrega (SIGHUP ou polling barato).

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 câmera (dev, webcam/vídeo) | Processo único. Fila `queue.Queue` em memória. SQLite ou PG local. Sem WS. **É o v1 — não otimizar antes disso.** |
| 2–8 câmeras (hotel pequeno) | Thread por câmera; 1 GPU combatching/frame-skip (~320 FPS dividos → 8–16 câmeras @15 FPS, doc 02); batch upsert a cada 2–5 s; FastAPI + dashboard |
| 8–32 câmeras (hotel grande) | Separar processo de inferência do processo de API; Redis Streams como fronteira; sub-stream 720p @10–15 FPS; writer dedicado; agregados pré-calculados |
| Multi-site / 100+ | Kafka/Redpanda, workers de inferência horizontais, edge bridge por site (câmeras atrás de NAT), TimescaleDB. **Muito além do escopo** |

### Scaling Priorities

1. **Primeiro gargalo — RTSP decode/leitura:** `cap.read()` bloqueante com
   N câmeras serializa tudo (problema documentado no tutorial Samaritan).
   Corrigir com Pattern 1 *antes* de otimizar GPU. Sintoma: FPS efetivo por
   câmera cai ~1/N.
2. **Segundo gargalo — I/O de banco no loop:** latência de rede/lock de
   tabela entra no hot loop → queda de FPS → frames perdidos. Corrigir com
   batch writer (Pattern 2). Sintoma: FPS oscila junto com latência do PG.
3. **Terceiro — VRAM/CPU da GPU:** reduzir `imgsz`, trocar para nano,
   frame-skip, sub-stream da câmera. Nunca adicionar câmera antes de medir.

## Anti-Patterns

### Anti-Pattern 1: I/O de banco dentro do loop de vídeo

**What people do:** `INSERT` a cada detecção/frames, ou `await db.execute()`
num `async def` que roda inferência.
**Why it's wrong:** Sincroniza hot loop com rede/disco; um pico de latência do
PG derruba FPS e causa perda de frames. É literalmente a restrição doc 08.
**Do this instead:** append num buffer em memória + worker de batch upsert
com `evento_id` idempotente.

### Anti-Pattern 2: Um tracker global compartilhado entre câmeras

**What people do:** instanciar `ByteTrack()` uma vez e passar detecções de
todos os streams.
**Why it's wrong:** o estado (Kalman, associacao) fica corrompido; `track_id`
colide entre câmeras e a contagem vira lixo. Achado explícito em
`salkooheji/vision-track` ("one shared ByteTrack across streams corrupts ID state").
**Do this instead:** `trackers: dict[camera_id, ByteTrack]`. IDs reiniciam por
câmera — isso é correto, não é bug.

### Anti-Pattern 3: Ler RTSP e inferir na mesma thread

**What people do:** `while True: frame = cap.read(); model(frame)`.
**Why it's wrong:** buffer interno do OpenCV cresce → processa footage de
segundos atrás (lag acumulado) ou frames antigos aleatórios.
**Do this instead:** thread de leitura descartando frames antigos +
`CAP_PROP_BUFFERSIZE=1` + watchdog de frescor. (Roboflow, QEngineering.)

### Anti-Pattern 4: Contar detecções em vez de trilhas

**What people do:** `if ponto_dentro_zona: count += 1` a cada frame.
**Why it's wrong:** uma pessoa parada na zona vira +30/s; jitter gera entradas
e saídas duplicadas.
**Do this instead:** contagem só no **delta de estado por `track_id`**
(Pattern 3) + histerese na tripwire.

### Anti-Pattern 5: MTMCT como fase 1 do projeto

**What people do:** começar pela parte difícil (identidade global) porque
"single-camera é fácil".
**Why it's wrong:** fusão inter-câmera depende de tracklets estáveis;
ByteTrack instável → fusão instável → debugging impossível de isolar. Todos
os históricos de build reais entregam single-camera primeiro.
**Do this instead:** `session_id = camera_id + track_id` no v1 (sessão
degenerada mas funcional); ativar fusão real só quando contagem por zona
passar em QA.

### Anti-Pattern 6: Dashboard consultando o banco por frame

**What people do:** polling a cada 100 ms com `SELECT count(*) FROM tracks`.
**Why it's wrong:** carga de leitura disputa com escrita; latência de query
nunca dá tempo real de verdade.
**Do this instead:** estado de ocupação **atual** mantido em RAM no processo
do pipeline e exposto via WS/barato; banco só para histórico e séries.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Câmera/DVR RTSP | `CameraSrc` (Protocol) com reconexão + fallback ffmpeg | **Não disponível ainda** — v1 usa webcam/arquivo; interface já prevê a troca. Credenciais por env var, nunca em código |
| GPU NVIDIA | Device explícito no detector; fallback CPU p/ dev | ~3,1 ms/frame (doc 02); medir no hardware real antes de prometer nº de câmeras |
| PostgreSQL | Batch writer assíncrono, JSONB p/ polígonos | Schema já especificado no doc 06 — não redesenhar |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `ingestao` ↔ `motor` | leitura não-bloqueante de frame | Único ponto onde ndarray cruza — e some ali |
| `motor` ↔ `analytics` | `TrackUpdate` (dataclass, imutável) | Analytics é função pura → testável sem câmera |
| `analytics`/`sessoes` ↔ `persistencia` | fila de `Evento*` + batch writer | **Fronteira mais importante do sistema** (doc 08) |
| `persistencia` ↔ `api` | SQL read-only | API nunca importa `motor`/`ingestao` |
| `api` ↔ `dashboard` | REST + WS/polling | Dashboard nunca fala com o pipeline |

## Build Order (dependency-driven)

Extraído de histórico real entregue (`Ai-Retail-Footfall-Analytics`, 9 fases),
guia de 7 passos YuSMP (2026) e da lógica de dependência entre componentes:

```
①  Fonte (webcam/arquivo) + Detector + Tracker (1 câmera)
        │   prerequisite: nada. É a fatia vertical mínima.
        ▼
②  Analytics de zona (tripwire + dwell + estado por track_id)  ← precisa de ①
        │   SAÍDA: eventos em RAM / overlay visual. Valida contagem.
        ▼
③  Persistência (schema doc 06 + fila + batch upsert)         ← precisa de ②
        │   SAÍDA: eventos no PG. Agora há "verdade" durável.
        ▼
④  FastAPI (read-only) + ⑤ Dashboard                           ← precisa de ③
        │   SAÍDA: produto utilizável single-camera. PILOTO aqui (1–5 câmeras).
        ▼
⑥  Multi-câmera + RTSP (threads, tracker por stream, reconexão) ← precisa de ①②③
        │   (③ já deve ser fila-based p/ aguentar 8× eventos)
        ▼
⑦  Heatmaps + séries temporais + agregados pré-calculados      ← precisa de ③④
        ▼
⑧  MTMCT / Re-ID / session_id global                           ← precisa de ⑥ estável
        ▼
⑨  Hardening: LGPD audit, logs Art. 15, watchdog, monitoramento
```

**Ordering rationale:**
- **①→② antes de qualquer banco:** a incerteza real é "a contagem está
  correta?". Só se responde com overlay visual e fixtures de vídeo — banco
  e dashboard só atrasam esse feedback.
- **③ cedo (mas depois da lógica):** o schema doc 06 já existe, então o
  custo é baixo; e a fila é pré-requisito para ⑥, não pode ser retrofit.
- **④+⑤ antes de ⑥:** entrega valor verificável (piloto YuSMP: 1–5 câmeras,
  semanas, medir precisão) antes de investir em concorrência.
- **⑥ antes de ⑦/⑧:** heatmaps e MTMCT multiplam volume de dados; precisa
  do pipeline multi-stream estável primeiro.
- **⑧ por último:** é o componente com maior incerteza e menor impacto na
  contagem por zona (que funciona single-camera). `session_id` degenerado
  cobre o MVP.
- **⑨ contínuo, com auditoria final:** LGPD não é fase, é invariante — mas a
  auditoria (frames nunca persistidos, TTL de embeddings, logs 6 meses) faz
  sentido como gate antes do piloto real.

## Sources

- **Docs do projeto** (arquitetura-alvo, MTMCT, schema, perf) — fonte primária
  `DOCUMENTACAO_PROJETO_E_LGPD/02_…md`, `05_…md` — HIGH (não-externo)
- Roboflow Blog, *Process RTSP Streams for Real-Time Video Analytics* (2026-05) — HIGH (oficial)
- Roboflow `inference` `analytics/time_in_zone/v1.py` — implementação oficial de dwell — HIGH
- Ultralytics docs, *Object Counting* (YOLO26, `region`, `bytetrack.yaml`) — HIGH (oficial)
- `sid-2672/Video-analytics-pipeline` — arquitetura módulos/supervisor — MEDIUM (repo público)
- `MohibShaikh/yolo26-analytics` — `VideoSource→Detector→Tracker→ZoneAnalyzer` + PG/FastAPI — MEDIUM
- `salkooheji/vision-track` — isolamento de tracker por stream — MEDIUM
- `mrazza/cctv-home-occupancy` — histerese de tripwire, Fast&Slow, SQLite/FastAPI — MEDIUM
- `MOHDJUNAID70/Store-Intelligence-System` — pipeline YOLO→ByteTrack→Zone→API→PG — MEDIUM
- `mohankasaurabh/Ai-Retail-Footfall-Analytics` — histórico de build em 9 fases — MEDIUM (ordem de fases)
- Samaritan docs 04 *multi-camera and threading* — blocking read → thread por câmera — MEDIUM
- The Neural Base, *RTSP stream processing / RTSP handling* — gotchas de produção — LOW (blog, mas consistente)
- Markaicode, *FastAPI Inference Architecture* (2026-07) — monolith <100 req/s vs fila — LOW
- HLD occupancy system (Substack 2026-01) — eventos/deltas/prefix-sum/idempotência — LOW (blog)
- **MTMCT:** ReidTrack (CVPRW 2023), LAAM (ICCV 2021), State-aware Re-ID (1906.01357), *Robust Online Multi-Camera* (CVPRW 2024), Ristani & Tomasi (CVPR 2018), TCLM (2105.01213) — HIGH (peer-reviewed), aplicação a produção MEDIUM

---
*Architecture research for: hotel people-flow analytics (Visão Computacional)*
*Researched: 2026-10-08*
