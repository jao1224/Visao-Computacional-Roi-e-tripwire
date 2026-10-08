# Fase 1: Fatia vertical single-câmera (captura, detecção, rastreio efêmero) - Research

**Pesquisado em:** 2026-10-08
**Domínio:** Ingestão de vídeo single-câmera (webcam/arquivo) + detecção de corpo + rastreio efêmero em RAM (ByteTrack) com overlay na tela e base de privacidade "nada em disco"
**Confiança:** ALTA (API do Ultralytics/OpenCV verificada diretamente no fonte instalado e por smoke test executado na máquina)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Módulos **planos na raiz** do projeto — `captura.py`, `rastreio.py`, `overlay.py` — importados pelo `main.py`. **Sem pacote, sem `__init__.py`**, seguindo a convenção atual de scripts autônomos (`STRUCTURE.md`).
- **D-02:** Nomes dos módulos novos **em português** (combina com a raiz — `treinar_crowdhuman.py` — e com mensagens/comentários em pt-BR).
- **D-03:** `main.py` permanece o **único ponto de entrada** (`python main.py`, `q` para sair) — mantém seus padrões atuais: resolução de pesos por fallback de candidatos (`main.py:11-19`), guard `main()`, mensagens em pt-BR.
- **D-04:** Conexão entre módulos por **funções simples** chamadas pelo laço `while` do `main.py` (ex.: `capturar()`, `rastrear()`, `desenhar()`) — **sem classes nem Pipeline orquestrador**; cada função faz uma coisa.
- **D-05:** Criar **`requirements.txt`** mínimo na raiz (ultralytics, opencv-python, numpy e o que mais os imports exigirem) — hoje o repo não tem nenhum lock de dependências.
- **D-06:** Logs de execução **somente no console** (print com tags `[OK]`/`[Aviso]`/`-->` em pt-BR) — nenhum arquivo de log em disco (elimina risco de log por-pessoa violar ING-03).

### the agent's Discretion
- Assinatura exata e parâmetros das funções de cada módulo
- Como o ByteTrack é integrado (provavelmente `model.track()` do Ultralytics com `persist=True` — decisão técnica do researcher/planner)
- Formato dos dados passados entre módulos (dict, tupla, dataclass simples)
- Valores de `conf`, `iou`, FPS alvo (hoje 5 FPS em `main.py:35`)
- Estratégia de teste manual com `test/gemini_generated_video_8d21d35f.mp4`
- Conteúdo detalhado do `requirements.txt` (versões)

### Deferred Ideas (OUT OF SCOPE)
- Nenhuma — a discussão permaneceu dentro do escopo da fase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da pesquisa |
|----|-----------|---------------------|
| ING-01 | Processa webcam e arquivos de vídeo-amostra como fonte de vídeo | `captura.py` abstrai `cv2.VideoCapture` com `fonte` aceitando `int` (índice, ex.: `0`) ou `str` (caminho, ex.: `test/gemini_generated_video_8d21d35f.mp4`). Verificado: webcam index 0 abre via DSHOW (0.60 s, 480x640) e o MP4 abre (480 frames, 24 FPS). |
| ING-03 | Frames voláteis (RAM), descartados após inferência — nenhuma imagem/frame/crop toca disco | `model.track(..., save=False)` (padrão) não grava nada — confirmado por auditoria de diretório antes/depois do smoke test. Overlay desenha in-place no frame em RAM; `overlay.py` proíbe `imwrite`/`VideoWriter`. `verbose=False` evita despejo por-frame. |
| CNT-01 | Detecção apenas por corpo (YOLO CrowdHuman) — nenhum módulo de face/biometria | `resultados/best.pt` verificado com `names = {0: 'person'}` (classe única corpo). O fallback `yolo26n.pt` tem 80 classes COCO — **filtrar com `classes=[0]`**. Auditoria de código: nenhum import de face/biometria nos módulos do produto. |
| CNT-03 | Associação intra-câmera efêmera (ByteTrack, segundos, RAM) — IDs morrem ao sair do quadro, nunca persistidos | `model.track(frame, persist=True, tracker='bytetrack.yaml')`; IDs verificados aparecendo/sumindo entre frames (ex.: ID 12 só no frame 15; IDs 18–23 só no frame 60). `track_buffer: 30` (RAM) mantém ID vivo só ~por segundos. Nenhuma escrita de ID em arquivo/banco. |
</phase_requirements>

## Resumo

A Fase 1 é uma fatia vertical de desenvolvimento em **1 câmera**: webcam ou vídeo-amostra -> YOLO CrowdHuman (corpo) -> ByteTrack efêmero em RAM -> overlay na tela, com a invariante de privacidade estabelecida desde o início (nada em disco, sem face, IDs efêmeros). O codebase atual já tem o núcleo de inferência funcionando em `main.py` (`YOLO(modelo)(frame, conf=0.25, iou=0.60)`) e um vídeo-amostra em `test/`. O trabalho é **extrair** esse laço em três módulos planos (`captura.py`, `rastreio.py`, `overlay.py`) e **trocar `model()`/`model.predict()` por `model.track()`** com ByteTrack, mantendo `main.py` como único ponto de entrada.

A integração é mais simples do que o esperado: o Ultralytics já embarca ByteTrack (`bytetrack.yaml`) e implementa o rastreio com um único kwarg (`tracker='bytetrack.yaml'`) + `persist=True`, sem dependência extra de tracking (apenas `lap`, que é instalado automaticamente). Verifiquei o comportamento real na máquina: `results = model.track(frame, persist=True, tracker='bytetrack.yaml', ...)` retorna `list[Results]` onde `results[0].boxes.id` traz os IDs — **presente apenas quando o rastreio está ativo** (a coluna extra de 7 valores). O ponto não óbvio e crítico: em Ultralytics **8.4.121 o tracker padrão mudou para `tracktrack.yaml` (TrackTrack), não ByteTrack** — a decisão do usuário exige ByteTrack, então `tracker='bytetrack.yaml'` **precisa ser passado explicitamente**.

As demais decisões são contratos baratos agora e caros de retrofitar depois: carimbo de tempo no momento da captura (`capture_ts`), política de "frame mais recente vence" (latest-frame-wins) encapsulada em `captura.py`, e a prova executável de "nada em disco" (auditoria de diretório antes/depois + grep de módulos de face). A recomendação de menor risco é um laço **síncrono** (compatível com D-04 "funções simples, sem classes"), com `CAP_PROP_BUFFERSIZE=1`, deixando a porta aberta para uma thread de captura 1-slot atrás da mesma função `capturar()` quando o RTSP chegar na Fase 6.

**Recomendação principal:** Manter o laço síncrono; trocar a chamada de inferência por `model.track(frame, persist=True, tracker='bytetrack.yaml', conf=0.25, iou=0.60, classes=[0], verbose=False)`; guardar `if result.boxes.id is not None` antes de ler IDs; carimbar `capture_ts = time.time()` logo após `cap.read()`; criar `requirements.txt` com `ultralytics==8.4.121`, `opencv-python==5.0.0.93`, `numpy==2.5.2`, `lap==0.5.13`.

## Stack Padrão

### Núcleo
| Biblioteca | Versão verificada | Propósito | Por que é padrão |
|------------|-------------------|-----------|------------------|
| Python | 3.14.4 (na máquina) | Runtime | Interpretador real instalado; `STACK.md` diz 3.11.9 e `research/SUMMARY.md` diz 3.12 — ambos desatualizados. Não fixar versão no `requirements.txt` (não há). `[VERIFIED: torch/ultralytics rodando neste Python]` |
| ultralytics | 8.4.121 | Inferência YOLO + ByteTrack embutido | Já é o stack de `main.py`; tracking built-in sem dependência extra. `[VERIFIED: pip list + inspeção do fonte instalado]` |
| opencv-python | 5.0.0.93 | Captura (`cv2.VideoCapture`), desenho (`rectangle`/`putText`), janela (`imshow`) | Já usado em `main.py`; `cv2.__version__ == 5.0.0`. `[VERIFIED: import cv2]` |
| numpy | 2.5.2 | Tipo dos frames e do `boxes.data` | Dependência transitiva obrigatória; frames em RAM. `[VERIFIED]` |
| lap | 0.5.13 | Atribuição linear usada pelo ByteTrack | **Instalado automaticamente pelo Ultralytics no primeiro `track()`** ("Ultralytics requirement ['lap>=0.5.12'] not found, attempting AutoUpdate"). Deve estar no `requirements.txt` para evitar AutoUpdate (rede + escrita em disco) a cada ambiente novo. `[VERIFIED: smoke test]` |
| torch / torchvision | 2.11.0+cu128 / 0.26.0+cu128 | Backend de inferência/GPU | Transitivo do ultralytics; `main.py` não importa torch diretamente. Não precisa entrar no `requirements.txt` a menos que se queira fixar a build CUDA. `[VERIFIED]` |

### Suporte
| Biblioteca | Versão | Propósito | Quando usar |
|------------|--------|-----------|-------------|
| pytest | (a adicionar — Wave 0) | Testes automatizados de privacidade/contrato | Necessário pela Nyquist validation (config `nyquist_validation: true`); hoje o repo não tem nenhum framework de teste. `[ASSUMED: versão a definir]` |

### Alternativas Consideradas
| Em vez de | Poderia usar | Trade-off |
|-----------|--------------|-----------|
| `model.track(tracker='bytetrack.yaml')` (built-in) | Pacote `trackers` (Roboflow) — `ByteTrackTracker().update(detections)`, sugerido em `research/SUMMARY.md` | O `trackers` desacopla o rastreio do modelo e facilita trocar algoritmo (OC-SORT/BoT-SORT), mas adiciona dependência e mais código. Para a fatia single-câmera da Fase 1, o built-in é zero-dep e alinhado à discrição do CONTEXT ("provavelmente `model.track()`"). Adiar `trackers` para quando houver necessidade real de troca de algoritmo. `[VERIFIED: bytetrack.yaml embutido em ultralytics/cfg/trackers/]` |
| Laço síncrono (recomendado) | Thread de captura 1-slot (latest-frame-wins "puro", `research/ARCHITECTURE.md`) | A thread garante frescor mesmo com inferência lenta, mas adiciona complexidade de concorrência no Windows. Fase 1 é dev/single-câmera; encapsular atrás de `capturar()` deixa a troca para a Fase 6 sem tocar o `main.py`. |
| `model.track` default (TrackTrack) | ByteTrack | **Não é opção** — decisão do usuário exige ByteTrack explicitamente. O default em 8.4.121 é TrackTrack (ver "Estado da arte"). |

### Instalação
```bash
pip install ultralytics opencv-python numpy lap
```

### Verificação de versões
Verificado diretamente na máquina em 2026-10-08 (não em registry — este ambiente já tem o stack pronto):
```
ultralytics 8.4.121
opencv 5.0.0   (pacote opencv-python 5.0.0.93)
numpy 2.5.2
lap 0.5.13
torch 2.11.0+cu128 (cuda True)
```
Conteúdo sugerido do `requirements.txt` (D-05):
```
ultralytics==8.4.121
opencv-python==5.0.0.93
numpy==2.5.2
lap==0.5.13
```

## Architecture Patterns

### Estrutura recomendada
```
scriptvisaocomput/
├── main.py          # único ponto de entrada; laço while orquestra os 3 módulos
├── captura.py       # fronteira da fonte de vídeo: abrir_fonte(), capturar()
├── rastreio.py      # carregar_modelo(), rastrear()  (YOLO + ByteTrack)
├── overlay.py       # desenhar_caixas(), desenhar_hud()  (funções puras de desenho)
├── requirements.txt # NOVO (D-05)
└── test/gemini_generated_video_8d21d35f.mp4  # vídeo-amostra (ING-01)
```

### Padrão 1: Rastreio via `model.track()` em laço manual
**O quê:** substituir `model(frame, conf=..., iou=...)` por `model.track(frame, persist=True, tracker='bytetrack.yaml', ...)` dentro do `while` do `main.py`.
**Quando usar:** sempre na Fase 1 (o rastreio é o núcleo do CNT-03).
**Fatos verificados:**
- Assinatura real (instalado): `Model.track(self, source=None, stream=False, persist=False, **kwargs) -> list[Results]`.
- `tracker='bytetrack.yaml'` e `conf`/`iou`/`classes`/`verbose` vão em `**kwargs`.
- `model.track` **força** `conf=0.1` (se não passado) e `batch=1`; por isso passar `conf=0.25` explicitamente mantém o comportamento atual de `main.py`.
- Com `persist=True` chamado frame-a-frame com um `numpy.ndarray`, o estado do tracker é mantido e os IDs permanecem coerentes entre chamadas (verificado: IDs 1–10 estáveis por 30+ frames).
**Exemplo:**
```python
# Source: inspeção de ultralytics/engine/model.py (instalado) + smoke test local
results = model.track(frame, persist=True, tracker='bytetrack.yaml',
                      conf=0.25, iou=0.60, classes=[0], verbose=False)
```

### Padrão 2: Contrato de timestamp (captura, não processamento)
**O quê:** carimbar `capture_ts = time.time()` **imediatamente após** `cap.read()` retornar, e carregar `(frame, capture_ts)` pelo pipeline. Nunca re-carimbar a jusante, nunca usar índice de frame para tempo.
**Por quê:** Armadilha "Phase 1" de `PITFALLS.md` (Pitfall 6): se o timestamp é feito na hora do processamento, a idade do frame vira erro de timestamp. O `cv2.VideoCapture` **não expõe timestamp de sensor** — `time.time()` logo após o read é o melhor disponível em webcam/arquivo. Para matemática de idade de frame use a mesma base (epoch). `[VERIFIED: cv2 não tem getter de timestamp; padrão confirmado em PITFALLS.md]`

### Padrão 3: latest-frame-wins (frame mais recente vence)
**O quê:** garantir que o inferidor processe o frame mais novo disponível e descarte os atrasados.
**Como na Fase 1 (síncrono, compatível com D-04):**
1. Após abrir: `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)` para reduzir o buffer interno (webcam).
2. Opcional (webcam mais rápida que a inferência): drenar o buffer com `cap.grab()` em sequência e pegar o último com `cap.retrieve()` antes do processamento pesado.
3. Nunca encher fila nem acumular frames; descartar é o comportamento correto (frescor > completude).
**Caveats verificados:** `CAP_PROP_BUFFERSIZE` retorna `-1.0` ao setar em fonte de **arquivo** (não suportado) e o suporte em webcam via DSHOW é parcial. `grab()`/`retrieve()` funciona (avança a posição sem decodificar; `retrieve()` retorna `(720,1280,3)`). A versão robusta (thread 1-slot) fica encapsulada na mesma `capturar()` para a Fase 6. `[VERIFIED: probe_grab.py]`

### Padrão 4: overlay como funções puras de desenho
**O quê:** `overlay.py` recebe um frame (ndarray) e desenha in-place (caixas+label com ID+conf, HUD de FPS+contagem), igual a `main.py:57-76`, sem retornar/gravar imagem.
**Regra:** nada de `cv2.imwrite`/`VideoWriter`. Saída só pela janela `cv2.imshow`. Usar âncora de caixa como hoje; para a Fase 2 (zona/tripwire) a âncora recomendada é o centro-inferior da caixa (bottom-center).

### Anti-Padrões a Evitar
- **Usar `model.track` sem `tracker='bytetrack.yaml'`:** o default é TrackTrack; viola a decisão de ByteTrack.
- **Ler `boxes.id` sem guard:** `boxes.id` é `None` quando não há rastreio (`is_track=False`); iterar sobre ela quebra. Sempre `if result.boxes.id is not None`.
- **`save=True`/`save_txt=True`/`save_crop=True` em qualquer chamada:** grava imagens/txt em `runs/` -> viola ING-03.
- **Carimbar tempo na hora do processamento:** quebra o contrato de `capture_ts` (Pitfall 6).
- **Escrever track_id em qualquer arquivo/CSV/print rotulado como log persistente:** viola CNT-03/ING-03.
- **Deixar o fallback COCO (`yolo26n.pt`) sem `classes=[0]`:** detecta 80 classes e não é "só corpo".

## Don't Hand-Roll

| Problema | Não construir | Use | Por quê |
|----------|---------------|-----|---------|
| Associação temporal de detecções (tracking) | Algoritmo próprio de matching por IoU/centroide | `model.track(tracker='bytetrack.yaml')` | ByteTrack já trata oclusão, low-score association, keep-alive; hand-roll garante ID switches |
| Captura de vídeo multi-fonte | Camada própria de sockets/ffmpeg | `cv2.VideoCapture(index)` / `cv2.VideoCapture(path)` | Webcam e arquivo já resolvidos; RTSP (Fase 6) terá tratamento específico |
| Desenho de caixas/labels/HUD | Renderizador próprio | `cv2.rectangle`/`cv2.putText` (como `main.py`) | Já existe e funciona; mantém o padrão do repo |
| Configuração do tracker | YAML/params próprios de ByteTrack | `bytetrack.yaml` embutido | Defaults curados (`track_buffer: 30`, `match_thresh: 0.8`, etc.); tuning na Fase 2 se preciso |

**Insight-chave:** a precisão de contagem depende do *tracker*, não do detector (`PITFALLS.md` #3). Não reinventar o matching; ajustar `track_buffer` só se a oclusão da cena exigir (Fase 2).

## Common Pitfalls

### Armadilha 1: Tracker padrão trocado (TrackTrack vs ByteTrack)
**O que dá errado:** chamar `model.track(..., persist=True)` sem `tracker=` e processar com TrackTrack achando que é ByteTrack.
**Por que acontece:** em Ultralytics 8.4.121 o default mudou para `tracktrack.yaml` (docs oficiais listam TrackTrack como default).
**Como evitar:** passar `tracker='bytetrack.yaml'` sempre.
**Sinal:** comportamento de associação diferente do esperado / docs desatualizados.

### Armadilha 2: `boxes.id` ausente quebra o laço
**O que dá errado:** `for box, tid in zip(boxes, boxes.id)` lança quando não há rastreio (ex.: primeiro frame sem detecção -> `id = None`).
**Por que acontece:** `Boxes.id` só existe com dados de 7 colunas (`is_track=True`); com 6 colunas retorna `None`.
**Como evitar:** `if result.boxes.id is not None:` antes de acessar. `[VERIFIED: fonte Boxes.__init__ e propriedade id]`
**Sinal:** `TypeError: 'NoneType' object is not iterable`.

### Armadilha 3: Escrita silenciosa em disco
**O que dá errado:** `Ultralytics` criando `runs/detect/...` ou o AutoUpdate do `lap` gravando em `site-packages` — quebra a auditoria "nada em disco".
**Por que acontece:** defaults `save=True` em alguns caminhos; `lap` ausente dispara `pip install` automático (verificado: escreveu em `%APPDATA%`).
**Como evitar:** manter `save=False` (default) e nunca passar `save*`; incluir `lap` no `requirements.txt`; a auditoria de disco deve ser escopada ao **diretório de trabalho da aplicação** (imagem/vídeo), não ao `site-packages`.
**Sinal:** novo `runs/` após rodar; mensagem "Ultralytics requirement [...] attempting AutoUpdate".

### Armadilha 4: Carimbo de tempo no lugar errado
**O que dá errado:** usar `time.time()` no momento da inferência/desenho para dwell/frame-age — corrompe durações quando a inferência atrasa (Pitfall 6).
**Por que acontece:** é onde é mais fácil colocar o `time.time()`.
**Como evitar:** carimbar na saída de `cap.read()`, carregar o valor junto do frame.
**Sinal:** idade de frame inconsistente; durações negativas (Fase 2).

### Armadilha 5: Aparência de "só corpo" no fallback COCO
**O que dá errado:** se `resultados/best.pt` não existir, o fallback `yolo26n.pt` (80 classes) detecta carro/cadeira/etc.
**Por que acontece:** o fallback de candidatos em `main.py:11-19` termina em `yolo26n.pt`.
**Como evitar:** `classes=[0]` na chamada de tracking; logar `[Aviso]` quando cair no fallback (já é o padrão do repo).
**Sinal:** caixas em objetos não-humanos.

### Armadilha 6: Resíduo de "face" no repo confunde auditoria LGPD
**O que dá errado:** grep repo-wide por `face` **não é vazio** — `models/base_face_weights.pt` é referenciado em `treinar_crowdhuman.py:23` e `scripts/train_body.py:8` (pesos de face usados como *inicialização de transfer learning*).
**Por que acontece:** o repo tem scripts de treino `[teste]` com resíduo de face, fora do produto.
**Como evitar:** escopar a auditoria de face/biometria aos módulos do produto (`main.py`, `captura.py`, `rastreio.py`, `overlay.py`) e ao `requirements.txt`; declarar os scripts de treino como `[teste]` fora do escopo do produto (per `STRUCTURE.md:41`). Ressalva para a Fase 9 (PRV-03) formalizar esse escopo. `[VERIFIED: grep repo]`

### Armadilha 7: Ambiente global tem libs de face instaladas
**O que dá errado:** `facenet-pytorch 2.5.3` e `opencv-contrib-python 5.0.0.93` (traz `cv2.face`) estão instalados **na máquina**.
**Por que acontece:** vieram de outros projetos; não são dependências deste repo.
**Como evitar:** não incluir no `requirements.txt`; usar `opencv-python` (não `opencv-contrib-python`); o código do produto não pode importar `cv2.face`/`facenet`. A prova é por auditoria de código+requirements, não do ambiente global. `[VERIFIED: pip list]`

## Code Examples

### Captura (captura.py) — webcam ou arquivo, com capture_ts
```python
# Source: cv2 5.0.0.93 verificado na máquina; padrão de main.py:28-45
import time
import cv2

def abrir_fonte(fonte):
    # fonte: int (índice de webcam) ou str (caminho de vídeo)
    cap = cv2.VideoCapture(fonte)
    if isinstance(fonte, int):
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # reduz buffer da webcam (parcial em DSHOW)
    return cap

def capturar(cap):
    ok, frame = cap.read()
    if not ok:
        return None, None
    capture_ts = time.time()  # carimbo no momento da captura (contrato da Fase 1)
    return frame, capture_ts
```

### Rastreio (rastreio.py) — YOLO + ByteTrack efêmero
```python
# Source: ultralytics/engine/model.py (instalado) + smoke test local 2026-10-08
from ultralytics import YOLO

def carregar_modelo(modelo_path):
    return YOLO(modelo_path)

def rastrear(model, frame):
    # persist=True mantém o tracker entre chamadas (IDs coerentes frame-a-frame)
    results = model.track(frame, persist=True, tracker='bytetrack.yaml',
                          conf=0.25, iou=0.60, classes=[0], verbose=False)
    return results[0]

def extrair_caixas(result):
    # boxes.id é None quando não há rastreio -> sempre guardar
    if result.boxes is None or result.boxes.id is None:
        return []
    xyxy = result.boxes.xyxy.cpu().tolist()
    ids = result.boxes.id.int().cpu().tolist()
    confs = result.boxes.conf.cpu().tolist()
    return list(zip(ids, xyxy, confs))  # [(track_id, [x1,y1,x2,y2], conf), ...]
```

### Overlay (overlay.py) — desenho puro, sem persistir
```python
# Source: main.py:57-76 (extraído); cv2 5.0.0
import cv2

def desenhar_caixas(frame, caixas):
    for tid, (x1, y1, x2, y2), conf in caixas:
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 165, 0), 2)
        label = f'ID {tid} | {conf*100:.1f}%'
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (int(x1), int(y1) - 22), (int(x1) + w, int(y1)), (255, 165, 0), -1)
        cv2.putText(frame, label, (int(x1), int(y1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

def desenhar_hud(frame, fps, n_pessoas):
    cv2.putText(frame, f'FPS: {fps:.1f} | Pessoas: {n_pessoas}', (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
```

### Prova executável de "nada em disco" (auditoria)
```powershell
# Snapshot antes/depois de rodar o pipeline (escopo: diretório de trabalho)
Get-ChildItem -Recurse -Include *.jpg,*.png,*.mp4,*.avi,*.mkv -LiteralPath . |
  Where-Object { $_.FullName -notlike '*\.git\*' } |
  Select-Object FullName,LastWriteTime | Sort-Object FullName | Out-File $env:TEMP\antes.txt
# ... rodar: python main.py (deixar N segundos, 'q' para sair) ...
git status --porcelain   # deve continuar sem novos arquivos de mídia
```

### Auditoria de face/biometria (escopada ao produto)
```bash
# Deve retornar vazio nos módulos do produto e no requirements.txt
rg -n -i "face|biometr|demograf|insightface|facenet|retinaface|arcface|cv2\.face|imwrite|imsave|VideoWriter" main.py captura.py rastreio.py overlay.py requirements.txt
```

## State of the Art

| Abordagem antiga | Abordagem atual | Quando mudou | Impacto |
|------------------|-----------------|--------------|---------|
| `sv.ByteTrack` (supervision) | `model.track(tracker=...)` built-in do Ultralytics | `sv.ByteTrack` deprecado em supervision 0.28, **removido em 0.31** | Evita dependência removida; zero-dep de tracking |
| Tracker padrão ByteTrack | Tracker padrão **TrackTrack** (`tracktrack.yaml`) | Ultralytics 8.4.x | **Precisa passar `tracker='bytetrack.yaml'` explicitamente** |
| `cv2.CAP_PROP_OPEN_TIMEOUT_MILLISEC` | — | não existe em OpenCV 5.0.0 (verificado `hasattr=False`) | Relevante só na Fase 6 (RTSP); não usar esse nome |

**Descontinuado/obsoleto:**
- `cv2.VideoCapture` para RTSP: banido para ingestão de rede (Fase 6); OK para webcam/arquivo na Fase 1.
- `opencv-contrib-python`: instalado no ambiente global (traz `cv2.face`) mas não deve entrar no `requirements.txt` do produto.

## Assumptions Log

| # | Suposição | Seção | Risco se errado |
|---|-----------|-------|-----------------|
| A1 | O laço síncrono é suficiente para a Fase 1 (single-câmera, ~5 FPS); thread 1-slot fica para a Fase 6 | latest-frame-wins | Se a webcam acumular latência perceptível, é preciso adicionar a thread antes — mas a função `capturar()` isola a troca |
| A2 | `persist=True` frame-a-frame com ndarray mantém IDs (verificado empiricamente nesta versão) | Padrão 1 | Se uma atualização do Ultralytics resetar entre chamadas, seria preciso usar `stream=True` ou gerenciar o tracker manualmente |
| A3 | Fixar versões do `requirements.txt` iguais às da máquina de dev é aceitável | Stack | A máquina-alvo pode ter build CUDA/OpenCV diferentes; ajustar na validação da Fase 8 |
| A4 | pytest é o framework de teste a adotar | Validação | Conflita com a convenção "sem framework de testes" atual; validar com o usuário antes de adicionar |
| A5 | `test/gemini_generated_video_8d21d35f.mp4` é fixture válida de ING-01 (contém pessoas: 10 detecções no 1º frame) | ING-01 | Já verificado; baixo risco |

## Open Questions

1. **Escopo da auditoria LGPD de "face" no repo**
   - O que sabemos: `models/base_face_weights.pt` + referências em scripts de treino `[teste]` fazem o grep repo-wide por "face" retornar resultados.
   - O que é incerto: se a Fase 1 deve limpar/renomear isso agora ou se fica para a Fase 9 (PRV-03).
   - Recomendação: Fase 1 escopa às **módulos do produto**; registrar o resíduo como dívida para a Fase 9. Não renomear pesos agora (risco de quebrar scripts de treino).

2. **Valor de `track_buffer` para a cena**
   - O que sabemos: `bytetrack.yaml` traz `track_buffer: 30` (frames). A 5 FPS isso são ~6 s de keep-alive.
   - O que é incerto: se ~6 s é adequado sem causar ID switches/dupla contagem na Fase 2.
   - Recomendação: manter o default na Fase 1; tunar só na Fase 2 com cena real.

3. **Fonte padrão do `main.py` (webcam vs arquivo)**
   - O que sabemos: hoje `main.py` abre a webcam (`VideoCapture(0)`); ING-01 exige ambas.
   - O que é incerto: como o usuário seleciona a fonte (argumento de CLI? edição de constante?).
   - Recomendação: aceitar argumento opcional (`python main.py [caminho|indice]`) com default webcam `0`, preservando o comportamento atual se sem argumento.

## Environment Availability

| Dependência | Necessária para | Disponível | Versão | Fallback |
|-------------|-----------------|------------|--------|----------|
| Python | Runtime | ✓ | 3.14.4 | — |
| ultralytics | Detecção + ByteTrack | ✓ | 8.4.121 | — |
| opencv-python (cv2) | Captura/desenho/janela | ✓ | 5.0.0.93 | — |
| numpy | Frames/boxes | ✓ | 2.5.2 | — |
| lap | ByteTrack (atribuição) | ✓ | 0.5.13 | AutoUpdate do Ultralytics (evitar; incluir no requirements) |
| torch + CUDA | Inferência GPU | ✓ | 2.11.0+cu128, cuda True | CPU (`device='cpu'`) |
| Webcam (índice 0) | ING-01 | ✓ | 480x640 (DSHOW/ANY) | Vídeo-amostra em `test/` |
| Vídeo-amostra | ING-01/teste | ✓ | 480 frames @ 24 FPS | — |
| FFmpeg (embutido no cv2) | Decode de arquivo | ✓ | presente no build | — |
| pytest | Validação Nyquist | ✗ | — | Adicionar em Wave 0 (ou validação manual documentada) |

**Dependências ausentes sem fallback:**
- Nenhuma — todo o necessário para o objetivo da fase está presente.

**Dependências ausentes com fallback:**
- `pytest` — necessário apenas para os testes automatizados; fallback é o roteiro de teste manual (rodar `main.py` na webcam/arquivo + auditar disco).

## Validation Architecture

`workflow.nyquist_validation` está `true` em `.planning/config.json` — seção incluída.

### Test Framework
| Propriedade | Valor |
|-------------|-------|
| Framework | Nenhum detectado — **Wave 0 deve adicionar `pytest`** (recomendado; alinhado ao stack de teste do `research/SUMMARY.md`) |
| Arquivo de config | nenhum — ver Wave 0 |
| Comando de execução rápida | `python -m pytest tests/ -x -q` |
| Comando de suíte completa | `python -m pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Comportamento | Tipo de teste | Comando automatizado | Arquivo existe? |
|--------|---------------|---------------|----------------------|-----------------|
| ING-01 | Abre webcam e vídeo-amostra | integration/smoke | `pytest tests/test_captura.py::test_abre_video_amostra -x` | ❌ Wave 0 |
| ING-03 | Rodar o pipeline não cria arquivo de imagem/vídeo em disco | integration | `pytest tests/test_privacidade.py::test_sem_escrita_em_disco -x` | ❌ Wave 0 |
| CNT-01 | Nenhum módulo/dependência de face; detecção só corpo | static/unit | `pytest tests/test_privacidade.py::test_sem_modulos_de_face -x` | ❌ Wave 0 |
| CNT-03 | IDs de rastreio efêmeros (existem em RAM, não persistidos) | unit/integration | `pytest tests/test_rastreio.py::test_ids_efemeros -x` | ❌ Wave 0 |

### Sampling Rate
- **A cada commit de tarefa:** `python -m pytest tests/ -x -q`
- **A cada merge de wave:** `python -m pytest tests/ -q`
- **Gate da fase:** suíte completa verde antes do `/gsd-verify-work`, mais o teste manual visual (webcam + vídeo-amostra exibindo caixas/IDs) e a auditoria de disco.

### Wave 0 Gaps
- [ ] `tests/test_captura.py` — cobre ING-01 (abre o MP4 de `test/`, lê ≥ 1 frame)
- [ ] `tests/test_privacidade.py` — cobre ING-03 (snapshot de diretório antes/depois) e CNT-01 (varredura de tokens proibidos nos módulos do produto)
- [ ] `tests/test_rastreio.py` — cobre CNT-03 (processa ~60 frames, valida `ids` como inteiros e ausência de persistência)
- [ ] `tests/conftest.py` — fixtures compartilhadas (caminho do vídeo-amostra, carregamento do modelo)
- [ ] Instalação do framework: `pip install pytest` (adicionar ao `requirements.txt` ou a um `requirements-dev.txt`)

> Observação de honestidade: parte da aceitação da Fase 1 é **visual/manual** (ver caixas de corpo e IDs na tela sem face). Os testes automatizados cobrem os invariantes objetivos (privacidade, contrato, efemeridade). O roteiro manual com `test/gemini_generated_video_8d21d35f.mp4` e com a webcam (índice 0, verificada) permanece obrigatório.

## Security Domain

`security_enforcement` ausente em config = habilitado.

### Applicable ASVS Categories
| ASVS Category | Aplica | Controle padrão |
|---------------|--------|-----------------|
| V2 Authentication | não | Sem autenticação na Fase 1 (CLI local; API é Fase 4) |
| V3 Session Management | não | Sem sessões de usuário |
| V4 Access Control | não | Sem API/endpoints |
| V5 Input Validation | sim | Validar `fonte` (índice int válido ou caminho existente); guardar `cap.isOpened()`; nunca concatenar entrada em shell |
| V6 Cryptography | não | Sem criptografia na Fase 1 |
| Privacidade de dados (LGPD) | **sim** | Nada em disco; sem face/biometria; IDs efêmeros em RAM; logs só console |

### Known Threat Patterns for stack (Python + OpenCV + Ultralytics)
| Padrão | STRIDE | Mitigação padrão |
|--------|--------|------------------|
| Persistência acidental de frames/imagens (debug, `save=True`, `imwrite`) | Information Disclosure | `save=False`; banir `imwrite`/`VideoWriter`; auditoria de disco automatizada (ING-03/PRV-02) |
| Inclusão de lib de face/biometria (viola LGPD art. 11) | Information Disclosure | `requirements.txt` sem face/contrib; varredura de tokens proibidos (CNT-01/PRV-03) |
| Persistência por-pessoa (track_id/session_id/trilha) | Information Disclosure / Profiling (art. 12 §2º) | IDs só em RAM; nenhuma escrita de ID; logs de console sem ID por-pessoa persistido (CNT-03/PRV-01) |
| Path traversal / entrada de fonte não confiável | Tampering | Validar existência do arquivo de vídeo antes de abrir |
| Consumo de memória/latência por fila não limitada | Denial of Service | Buffer 1 + descarte; sem filas na Fase 1 |

## Sources

### Primary (HIGH confidence)
- Fonte instalado `ultralytics/engine/model.py` — `Model.track()` (assinatura, defaults `conf=0.1`, `batch=1`) e `ultralytics/engine/results.py` — `Boxes.id`/`is_track` (colunas 6 vs 7). Inspeção direta em 2026-10-08.
- `ultralytics/cfg/trackers/bytetrack.yaml` — defaults verificados (`track_high_thresh: 0.25`, `track_buffer: 30`, `match_thresh: 0.8`, `fuse_score: True`).
- Docs Ultralytics — Track mode / datasets track (TrackTrack default; `persist=True`): https://docs.ultralytics.com/modes/track e https://docs.ultralytics.com/datasets/track
- cv2 5.0.0.93 — `CAP_PROP_BUFFERSIZE` presente; `CAP_PROP_OPEN_TIMEOUT_MILLISEC` ausente; `grab()`/`retrieve()` funcionando.
- `main.py` (repo) — resolução de pesos, laço, HUD, conf=0.25/iou=0.60/verbose=True.
- `.planning/research/PITFALLS.md` #5 (dwell), #6 (timestamp), #10 (LGPD); `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` condições 1–4 e 11.

### Secondary (MEDIUM confidence)
- Smoke test local (60 frames do `test/gemini_generated_video_8d21d35f.mp4`) — `is_track=True`, `boxes.id` presente, IDs aparecendo/sumindo; `lap` auto-instalado.
- `.planning/research/SUMMARY.md` / `ARCHITECTURE.md` / `STACK.md` — padrão latest-frame-wins, contrato `capture_ts`, tracking per-camera (padrões corroborados).

### Tertiary (LOW confidence)
- Sugestão de `pytest` (do `research/SUMMARY.md`) — não autoritativa; a definir com o usuário (ver A4).

## Metadata

**Confidence breakdown:**
- Stack padrão: ALTA — versões verificadas por `pip list` + imports reais na máquina.
- Arquitetura (integração do `model.track`): ALTA — assinatura/retorno lidos do fonte instalado e comportamento confirmado por smoke test.
- Armadilhas: ALTA — default TrackTrack e `boxes.id=None` verificados; resíduos de face/contrib verificados por grep/pip.

**Pesquisado em:** 2026-10-08
**Válido até:** ~2026-11-07 (30 dias). Revalidar `tracker=` default e versões se o Ultralytics for atualizado.
