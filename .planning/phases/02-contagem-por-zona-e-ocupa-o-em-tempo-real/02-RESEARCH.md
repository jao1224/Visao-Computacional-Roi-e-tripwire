# Fase 2: Contagem por zona e ocupação em tempo real - Research

**Pesquisado em:** 2026-10-09
**Domínio:** Contagem bidirecional por tripwire (linha) + ocupação instantânea por ROI poligonal em 1 câmera, sobre o pipeline da Fase 1 (YOLO CrowdHuman + ByteTrack efêmero), com invariantes LGPD (nada em disco, IDs efêmeros)
**Confiança:** ALTA no stack e na geometria (verificado na máquina e no fonte instalado); MÉDIA na semântica de cena (debounce/hysteresis dependem do campo real — ver A2)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Novo módulo **`zona.py`** na raiz do projeto (plano, sem pacote, sem `__init__.py`), importado pelo `main.py`. Segue convenção da Fase 1 (nomes em português, funções simples, sem classes).
- **D-02:** Configuração de zonas em **`config/zonas.yaml`** (legível, editável, versionado). Mapeia `camera_id` → lista de zonas (tripwires + ROIs) com coordenadas em pixels da resolução da fonte.
- **D-03:** Integração no `main.py`: após `rastreio.extrair_caixas()` (linha ~74), chamar `zona.verificar_tripwires()`, `zona.atualizar_ocupacao()`, `overlay.desenhar_contadores()` — antes do `desenhar_hud`.
- **D-04:** Estado em RAM mantido em `main()` (dict `estado = {zona_id: {'ocupacao': int, 'entradas': int, 'saidas': int}}` e `track_states = {track_id: {...}}`). Passado para funções de `zona.py` a cada iteração.
- **D-05:** Logs apenas no console (tags `[OK]`/`[Aviso]`/`[Erro]` em pt-BR) — nenhum arquivo de log em disco.
- **D-06:** Suporta **ambos**: tripwire (linha, 2 pontos) para contagem ENTROU/SAÍDA + ROI poligonal para ocupação instantânea. Uma zona pode ter os dois.
- **D-07:** Formato `config/zonas.yaml` conforme exemplo (camera_0 com zonas tipo tripwire/roi, `direcao: "entrada"`, `pontos`, `capacidade: 30`).
- **D-08:** `camera_id` = string (`"camera_0"`, `"camera_1"`, ...) — mapeia 1:1 com a fonte resolvida em `main.py`. Para desenvolvimento: coordenadas manuais no YAML para o vídeo-amostra (1280x720) e webcam.
- **D-09:** Estado por `track_id`: `{'last_zone': None, 'crossed': set(), 'frames_since_first_seen': 0, 'last_cross_ts': 0}`.
- **D-10:** Contagem só quando: (a) centroide bottom-center da caixa cruza a linha do tripwire, (b) `track_id` não tem essa `zona_id` em `crossed`, (c) `frames_since_first_seen >= 3` (debounce — track estável).
- **D-11:** Hysteresis: após cruzar, o track precisa afastar `> 15 px` da linha antes de permitir cruzamento reverso (evita oscilação na borda).
- **D-12:** Direção via produto vetorial: vetor da linha × vetor do movimento → ENTRADA/SAÍDA. Coerente com `direcao` do YAML.
- **D-13:** Evento emitido: `(tipo, zona_id, track_id, ts)` onde `tipo ∈ {'ENTROU', 'SAIU'}`.
- **D-14:** Ocupação recalculada todo frame: `ocupacao[zona_id] = sum(1 for track in tracks if pointPolygonTest(roi, bottom_center(track)) >= 0)`.
- **D-15:** Reset diário: à meia-noite (hora local do hotel) **OU** quando `ocupacao == 0` por `> 10 min` (condição known-empty) → zera `ocupacao`, `entradas`, `saidas`, e limpa `crossed` dos tracks daquela zona.
- **D-16:** Clamp: `max(0, min(ocupacao, capacidade_da_zona))` — `capacidade` vem do YAML por câmera.
- **D-17:** Reconciliação pós-reconexão (preparação Fase 6): ao reabrir fonte (`captura.abrir_fonte`), zera `ocupacao` e `crossed` daquela `camera_id`.
- **D-18:** Estende `overlay.py` com: `desenhar_tripwires(frame, zonas)` (verde entrada, vermelho saída, label `zona_id`), `desenhar_rois(frame, zonas)` (polígonos semi-transparentes azuis, alpha 0.2), `desenhar_contadores(frame, estado)` (cards topo-direita `Zona X: IN 12 | OUT 7 | OCUP 5`).
- **D-19:** Cores: laranja caixas (existente), verde/vermelho tripwires, azul ROIs, branco/preto HUD.
- **D-20:** Novo arquivo `tests/test_zona.py` com fixtures e casos: entrada/saída, sem dupla contagem, ocupação ROI, reset diário (mock time), hysteresis.
- **D-21:** `config/zonas.yaml` inclui definição para `camera_0` (vídeo-amostra 1280x720) com tripwire + ROI de exemplo.

### the agent's Discretion
- Assinatura exata das funções de `zona.py` (parâmetros, ordem, tipos de retorno).
- Estrutura interna do `track_states` (dict vs dataclass simples).
- Como `main.py` obtém `camera_id` a partir da fonte resolvida (webcam 0 → `"camera_0"`, arquivo → `"camera_0"`, RTSP futuro → `"camera_N"`).
- Valores exatos de `debounce_frames=3`, `hysteresis_px=15`, `reset_idle_min=10` — podem virar constantes no topo de `zona.py`.
- Se `desenhar_tripwires`/`desenhar_rois` vão em `overlay.py` ou `zona.py` (preferência: `overlay.py` por ser desenho).

### Deferred Ideas (OUT OF SCOPE)
- MTMCT / Re-ID entre câmeras — FORA DO ESCOPO (LGPD Art. 12 §2º, Fase 7+ se houver base legal).
- Heatmap de densidade — Fase 7 (DWL-02).
- Dashboard CRUD de zonas — Fase 5 (DSH-01/DSH-03).
- Persistência de eventos ENTROU/SAÍDA no PostgreSQL — Fase 3 (API-01).
- Validação contra contagem manual em pico — Fase 8 (QUA-03).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da pesquisa |
|----|-----------|---------------------|
| CNT-02 | Contagem por zona com tripwire bidirecional (entra/sai), sem dupla contagem da mesma pessoa | Algoritmo de travessia por troca de lado (produto vetorial) + debounce 3 frames + hysteresis 15 px + `crossed` por track — Seções "Arquitetura: Padrão 1/2/3" e testes determinísticos D-20. Comportamento de IDs do ByteTrack verificado no fonte instalado (IDs monotônicos, sem reuso intra-sessão; `re_activate` preserva ID em oclusão < track_buffer). |
| CNT-04 | Ocupação instantânea por zona recalculada em tempo real, com reset/clamp diário e reconciliação após reconexão | Recontagem geométrica por frame via `cv2.pointPolygonTest` (semântica verificada em cv2 5.0.0) + clamp `[0, capacidade]` + reset meia-noite (derivado de `capture_ts`) + known-empty 10 min + reconciliação que limpa `track_states` — Seções "Arquitetura: Padrão 4/5" e testes com relógio injetável. |
</phase_requirements>

## Resumo

A Fase 2 transforma o pipeline da Fase 1 (captura → YOLO corpo → ByteTrack → overlay) em um **contador por zona**: tripwires (linhas) geram eventos ENTROU/SAIU por cruzamento bidirecional, e ROIs poligonais medem ocupação instantânea recalculada a cada frame — tudo desenhado no overlay, sem banco nem dashboard. O módulo `zona.py` (plano, funções `snake_case`, sem classes) concentra a lógica pura (geometria + estado por track + reset/clamp), e `overlay.py` ganha três funções de desenho. A configuração vive em `config/zonas.yaml` (PyYAML `safe_load`), com `camera_0` de exemplo para o vídeo-amostra 1280x720. Nada vai a disco: eventos são impressos no console e descartados; estado é RAM efêmera.

O núcleo da dificuldade — e o que a pesquisa resolve — é a **anti-duplicação** (CNT-02). A regra que funciona é: *contar transições de lado, nunca posição* — o âncora bottom-center tem um "lado" geométrico em relação à linha (sinal do produto vetorial); um evento só dispara quando esse lado **muda** entre frames consecutivos, e o mesmo `(track_id, zona_id)` não pode disparar de novo antes de (a) o track ter se afastado > 15 px da linha (hysteresis, D-11) e (b) ter havido uma travessia reversa real. O `crossed` por track funciona como semáforo de meio-ciclo (ENTROU marca, SAIU desmarca), o que torna a contagem estável sob oscilação na borda e sob flicker de caixa (critério 4 da fase). Verifiquei no fonte instalado (`ultralytics/trackers/basetrack.py`) que o ByteTrack **não reutiliza IDs dentro da sessão** (contador monotônico `BaseTrack._count`) e **preserva o ID** quando um track perdido é reativado dentro de `track_buffer` (30 frames ≈ 6 s a 5 FPS) — oclusão leve não causa dupla contagem nem precisa de lógica extra. O único caso em que IDs recomeçam do zero é o **reset do tracker** (troca de fonte/persist) — por isso a reconciliação (D-17) deve limpar `track_states` inteiro, não só `crossed`.

Para a ocupação (CNT-04), a decisão é não derivar de `entradas − saídas` (que deriva ao longo do dia — Pitfall 4): ocupação é **recontada por geometria a cada frame** (`cv2.pointPolygonTest >= 0`, semântica verificada: +1 dentro, 0 na borda contada, −1 fora), com clamp `[0, capacidade]` e dois resets: meia-noite (data derivada de `capture_ts` via `time.localtime`, o que também torna o reset testável com relógio injetável) e known-empty (ocupação == 0 por > 10 min). A reconciliação pós-reabertura é um hook barato agora (limpar estado + track_states) que a Fase 6 reutilizará para reconexões reais.

**Recomendação principal:** implementar `zona.py` com quatro funções puras e determinísticas — `carregar_zonas(camera_id, caminho=None)`, `verificar_tripwires(tracks, zonas, estado, track_states, agora=None)` (devolve eventos `(tipo, zona_id, track_id, ts)` — main imprime e descarta), `atualizar_ocupacao(tracks, zonas, estado, agora=None)` (recalcula, clampeia e aplica resets) e `reconciliar_fonte(estado, track_states)` — com `agora` (epoch) injetável para testes sem clock real. `main.py` chama na ordem: reset diário → tripwires → ocupação → desenho. Teste em `tests/test_zona.py` com cenas sintéticas frame-a-frame (caminhada perpendicular à linha, 10 passos de 20 px), sem modelo, sem vídeo, sem GUI — determinístico em CI.

## Stack Padrão

### Núcleo
| Biblioteca | Versão verificada | Propósito | Por que é padrão |
|------------|-------------------|-----------|------------------|
| Python | 3.14.4 (na máquina) | Runtime | Mesmo da Fase 1. `[VERIFIED: python --version]` |
| opencv-python (cv2) | 5.0.0.93 | Geometria (`pointPolygonTest`), desenho (`line`, `fillPoly`, `addWeighted`, `putText`, `getTextSize`), janela | Já é o stack; todas as funções necessárias **verificadas presentes** e semântica de `pointPolygonTest` confirmada em execução. `[VERIFIED: probe cv2]` |
| numpy | 2.5.2 | Vetores da tripwire (produto vetorial), distância ponto→segmento, contorno do ROI | Transitiva obrigatória; já no requirements. `[VERIFIED]` |
| PyYAML | 6.0.3 | Leitura de `config/zonas.yaml` via `yaml.safe_load` | Já instalada (transitiva do ultralytics: `pyyaml>=5.3.1`); agora é **import direto** do `zona.py` → **adicionar `pyyaml==6.0.3` ao `requirements.txt`** (mesmo motivo do pin de `lap`: evitar AutoUpdate/ambiguidade de versão). `[VERIFIED: importlib.metadata + import yaml]` |
| ultralytics | 8.4.121 | ByteTrack (já em uso; não muda nesta fase) | Nada a instalar; o comportamento de IDs verificado no fonte instalado. `[VERIFIED]` |

### Suporte
| Biblioteca | Versão | Propósito | Quando usar |
|------------|--------|-----------|-------------|
| pytest | 9.1.1 | Testes unitários determinísticos de `zona.py` | Já no `requirements-dev.txt`; suite da Fase 1 (21 testes) verde. `[VERIFIED: pytest --version]` |
| lap | 0.5.13 | ByteTrack (atribuição) | Já pinado (Fase 1). Sem mudança. |

### Alternativas Consideradas
| Em vez de | Poderia usar | Trade-off |
|-----------|--------------|-----------|
| `zona.py` próprio (funções planas, lado via produto vetorial) | `ultralytics.solutions.ObjectCounter` (contagem em linha) + `RegionCounter` (ocupação por região) built-in do YOLO26 | **Rejeitado por decisão travada**: são **classes** (conflita com D-01 "sem classes"), dependem de `shapely`, usam centroide da caixa (não bottom-center, D-10/D-14), a direção do ObjectCounter é heurística por eixo (compara x ou y conforme orientação da linha — frágil em linhas diagonais), e o formato de config deles não é `config/zonas.yaml` (D-02/D-07). O `RegionCounter` **confirma o padrão** de "ocupação = recontagem por frame, nunca total acumulado" — mesma abordagem de D-14. `[CITED: docs.ultralytics.com/guides/object-counting e /guides/region-counting — verificado 2026-10-09]` |
| Cruzamento por interseção de segmentos (shapely `LineString.intersects`) | Troca de lado via produto vetorial (escolhido) | A interseção de segmento é mais "correta" para pedestres que andam em volta da ponta da linha, mas exige dependência (shapely) e é O(1) mais complexa. A troca de lado + guarda de bounding box do segmento cobre o caso da fase (linha transversal à cena) sem dependência nova. Interseção de segmentos fica como refinamento da Fase 8 se a validação de campo exigir. `[ASSUMED: limitação documentada em A2]` |
| Overflow de `entradas − saídas` como ocupação | Recontagem geométrica por frame via `pointPolygonTest` | `entradas − saídas` acumula erro o dia inteiro (Pitfall 4) — um único erro de direção por hora compõe. Recontagem é `O(tracks × zonas)` trivial a 5 FPS e autocorrige. Decisão travada D-14. |
| Relógio real nos resets | `agora`/`capture_ts` injetáveis | Testes determinísticos de meia-noite e known-empty exigem clock controlado; `time.time()` indireto quebra CI. Injeta-se epoch; produção usa `capture_ts` (Pitfall 6). |

### Instalação
```bash
pip install pyyaml==6.0.3   # adicionar ao requirements.txt (import direto em zona.py)
pip install -r requirements-dev.txt  # pytest já presente
```

### Verificação de versões (executado em 2026-10-09)
```
python 3.14.4
cv2 5.0.0   (opencv-python 5.0.0.93) — pointPolygonTest/fillPoly/addWeighted/line/polylines presentes
numpy 2.5.2
pyyaml 6.0.3  (requisito transitivo do ultralytics: pyyaml>=5.3.1 — pin direto recomendado)
pytest 9.1.1
ultralytics 8.4.121 (byte_tracker.py/basetrack.py inspecionados)
```

## Architecture Patterns

### Estrutura recomendada
```
scriptvisaocomput/
├── main.py            # NÃO MUDA a orquestração; ganha 4 chamadas no laço + estado em main()
├── zona.py            # NOVO (D-01): carregar_zonas, verificar_tripwires, atualizar_ocupacao, reconciliar_fonte
├── overlay.py         # GANHA: desenhar_tripwires, desenhar_rois, desenhar_contadores (D-18)
├── config/
│   └── zonas.yaml     # NOVO (D-02/D-21): camera_0 com tripwire + ROI de exemplo
├── tests/
│   └── test_zona.py   # NOVO (D-20): cenas sintéticas, sem modelo/vídeo/GUI
└── requirements.txt   # GANHA: pyyaml==6.0.3
```

### Padrão 1: Travessia de tripwire por troca de lado (o coração do CNT-02)
**O quê:** cada track tem, por zona-tripwire, o lado geométrico em que o âncora esteve no frame anterior. Evento só dispara na **transição de lado** (nunca por posição "em cima da linha").
**Quando usar:** sempre que houver tripwire. É a implementação de D-10/D-11/D-12.
**Passo a passo (determinístico, testável):**
1. âncora `A = bottom-center` da caixa: `( (x1+x2)/2, y2 )` (D-10a; convenção Fase 1: âncora = centro-inferior — mais estável para pessoas em pé).
2. vetor da linha `V = P2 − P1`. Lado do ponto: `lado = sign( Vx*(Ay−P1y) − Vy*(Ax−P1x) )` → `+1` esquerda do vetor, `−1` direita, `0` na linha. Se `lado == 0`, manter o lado anterior (evita piscar).
3. Primeira aparição do track: só inicializar `lado_anterior`; **nunca contar no frame 1** mesmo que já esteja "do outro lado".
4. Se `lado != lado_anterior` (travessia detectada):
   - se `zona_id not in track_states[tid]['crossed']` → **meio-ciclo virgem**: se `frames_vistos >= DEBOUNCE_FRAMES (3)` → conta o evento (direção abaixo) e `crossed.add(zona_id)`.
   - senão (já contou neste meio-ciclo) → exige **hysteresis**: se `dist_ponto_segmento(A, P1, P2) > HYSTERESIS_PX (15)` → conta o evento **reverso** e `crossed.discard(zona_id)`; senão ignora (oscilação dentro da banda — não explode contagem).
   - sempre atualiza `lado_anterior = lado` ao final (a travessia geométrica consumou-se).
5. Direção (D-12): `sinal_mov = sign( Vx*(Ay_mov−P1y) − Vy*(Ax_mov−P1x) )` com `mov = A_atual − A_anterior`; o sinal de `cross(V, mov)` **é igual ao lado de chegada**. Mapeamento com o YAML: o lado positivo (+1, esquerda de P1→P2) corresponde a `direcao` informada no YAML. `lado == lado_entrada` → `ENTROU`; senão → `SAIU`, onde `lado_entrada = +1 se direcao == 'entrada' else −1`.
6. `frames_vistos` (D-10c): incrementa em **cada frame de presença** do track (não exige frames consecutivos — uma oclusão < track_buffer preserva o ID e o contador; é a mesma pessoa).

**Por que funciona:** "contar transições, nunca ocupações" é exatamente o conselho do Pitfall 3 (`PITFALLS.md` #3: sequence-based zone counting, marcar `(track_id, transition)` como já contado); o `crossed` vira o semáforo de meio-ciclo e a banda de 15 px mata a oscilação de borda (Pitfall 3: "someone loitering on the line oscillates and generates repeated crossings"). Prosecução: 1 pessoa parada em cima da linha por 30 s → exatamente 1 ENTROU (ou 0 se nunca cruzou de fato: lado nunca muda).

### Padrão 2: Comportamento dos IDs do ByteTrack (o que a anti-duplicação pode e não pode assumir)
**Fatos verificados no fonte instalado (ultralytics 8.4.121, `trackers/basetrack.py` e `trackers/byte_tracker.py`):**
- `BaseTrack._count` é contador **de classe, monotônico**; `next_id()` incrementa. IDs **nunca são reutilizados dentro da sessão** — track morto não libera o ID. → `crossed`/estado por track não colide com track novo na mesma sessão; a poda do `track_states` é **só para memória** (não para correção). `[VERIFIED: fonte instalado]`
- **Reativação preserva ID:** `re_activate(new_track, frame_id, new_id=False)` — um track em `lost_stracks` re-associado dentro de `track_buffer` (30 frames ≈ 6 s a 5 FPS) **mantém o mesmo track_id**. → oclusão leve (critério 1 da fase) não gera ID novo → não gera dupla contagem — a lógica de `crossed` continua valendo para a mesma pessoa. `[VERIFIED: fonte instalado]`
- **Reset só acontece em troca de fonte com `persist=False`** (`track.py`: `if not persist and vid_path mudou: tracker.reset()` — com `persist=True` o tracker NÃO é resetado entre vídeos). E `BYTETracker.reset()` **zera o contador** (`reset_id()` → `BaseTrack._count = 0`) → após reset, IDs recomeçam do 1. `[VERIFIED: fonte instalado]`
- **Implicação crítica para D-17:** se o estado de um track antigo (ex.: track_id 7 com `crossed={recepcao}`) sobreviver a um reset do tracker, o **novo** track 7 ficaria bloqueado (regra "zona em crossed → ignora") e a ocupação herdaria fantasma. Portanto a reconciliação de reabertura deve limpar `track_states` **inteiro** (não só `crossed`), além de zerar ocupação/entradas/saidas. Na Fase 2 (reabrir = reiniciar o processo), isso é trivial; o hook + teste cobrem o contrato para a Fase 6. `[VERIFIED: fonte + derivação lógica]`

### Padrão 3: Poda do `track_states` (memória em execuções longas)
**O quê:** sem poda, `track_states` cresce com cada ID distinto do dia (centenas/milhares) — memória vaza em execução de horas.
**Quando usar:** todo frame, após processar as caixas.
**Regra recomendada:** `track_states[tid]['ultimo_frame_visto']` (contador de frame do laço de `main()`); se `frame_atual − ultimo_frame_visto > PRUNE_FRAMES (60 = 2× track_buffer)` → `del track_states[tid]`. Margem segura: o ByteTrack descarta lost tracks após 30 frames; 60 frames (≈ 12 s a 5 FPS) garantem que nenhum track vivo é podado por engano. `[VERIFIED: track_buffer=30 em bytetrack.yaml — Fase 1]`
**Detalhe:** usar contador de frame (não `capture_ts`) para poda — é medida relativa intra-sessão, não durações; evita depender de relógio (e é determinístico em teste). O contador de frame já existe implicitamente no laço (`loop`); expor como `frame_idx` na assinatura (área de discrição) ou manter no `estado`.

### Padrão 4: Ocupação por recontagem geométrica + resets (CNT-04)
**O quê:** `estado[zona]['ocupacao']` é **recalculada todo frame** por `cv2.pointPolygonTest(roi, bottom_center, False) >= 0` (D-14), nunca derivada de `entradas − saídas` (Pitfall 4).
**Semântica verificada em cv2 5.0.0:** `pointPolygonTest(contorno_int32, (x, y), False)` → `1.0` dentro, `0.0` na borda (contada com `>= 0` — intencional), `−1.0` fora. Contorno como `np.array(pontos, dtype=np.int32)` formato `(n, 2)` funciona (validado na máquina). `[VERIFIED: probe]`
**Âncora:** bottom-center (D-14). Caixa parcialmente dentro com âncora fora → **não conta** (convenção: "os pés decidem"); o ROI deve ser desenhado incluindo a área do piso onde os pés ficam. Caixa parcialmente dentro com âncora dentro → conta.
**Resets (D-15), ambos dentro de `atualizar_ocupacao(…, agora=None)` (agora = epoch; produção passa `capture_ts`):**
1. **Meia-noite:** `dia = time.localtime(agora).date()`; se `dia != estado['dia_atual']` → zera `ocupacao`, `entradas`, `saidas` de **todas** as zonas da câmera e limpa `crossed`; `estado['dia_atual'] = dia`. Log `[OK] Reset diário (dia trocou)`. Premissa: host em fuso do hotel (A3). Usar **`capture_ts`, nunca `time.time()` no processamento** (Pitfall 6).
2. **Known-empty:** por zona, `estado[zona]['ultima_ocupacao_ts']` atualizado quando a **ocupação computada bruta > 0** (antes do clamp — um clamp-0 não pode "dar vida" ao timer); se `ocupacao_computada == 0` e `agora − ultima_ocupacao_ts > RESET_IDLE_SEG (600)` → zera contadores da zona e limpa `crossed` dos tracks daquela zona. Log `[Aviso] Zona {id} ociosa há 10 min — contadores zerados (known-empty)`. Nota: precisão ao segundo é desnecessária — tolerância de ±1 frame (~0,2 s) é irrelevante.
**Clamp (D-16):** `ocupacao = max(0, min(ocupacao_bruta, capacidade))` aplicado **antes** de armazenar. `capacidade` vem por câmera do YAML (extensão opcional por zona em A6/recomendação).
**Reconciliação (D-17):** `reconciliar_fonte(estado, track_states)` → zera `ocupacao`/`entradas`/`saidas`, limpa `crossed`, **descarta `track_states` inteiro** (Padrão 2). Chamada por `main()` ao reabrir a fonte (na prática da Fase 2, o processo reinicia; o teste cobre o path).

### Padrão 5: Overlay sem dependências (D-18/D-19)
- **Tripwires:** `cv2.line(frame, P1, P2, cor, 2)` — verde `(0, 255, 0)` se `direcao == 'entrada'`, vermelho `(0, 0, 255)` senão (D-19); label `zona_id` no ponto médio: `cv2.putText(..., FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)` com sombra preta (segunda chamada um pixel abaixo) para legibilidade.
- **ROIs semi-transparentes sem dep externa** (verificado): `overlay = frame.copy(); cv2.fillPoly(overlay, [np.array(pontos, np.int32)], (255, 0, 0)); cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)` — alpha 0.2 (D-18); borda: `cv2.polylines(frame, [pts], True, (255, 0, 0), 2)`.
- **Cards de contador (topo-direita):** para cada zona (`Zona {id}: IN {n} | OUT {n} | OCUP {n}`), retângulo preto semitransparente dimensionado por `cv2.getTextSize` (largura = texto + margem 2×8 px; altura = 24 px), empilhado a partir de `(W − card_w − 10, 10)` com gap 8 px; texto branco scale 0.6, espessura 2. Limitar a ~6 cards visíveis (`+N…` excedente) para não cobrir a cena. Mesmo padrão do label da Fase 1 (`getTextSize` + rect + `putText`).
- Nenhuma API de escrita (`imwrite`/`VideoWriter`) — extensão da auditoria de `test_privacidade.py` (adicionar `zona.py` à lista de módulos do produto).

### Ordem de integração no `main.py` (D-03, com o reset antes das contagens)
```
caixas = rastreio.extrair_caixas(result)
zona.verificar_reset(estado, zonas, capture_ts)     # (ou dentro de atualizar_ocupacao)
eventos = zona.verificar_tripwires(caixas, zonas, estado, track_states, capture_ts)
zona.atualizar_ocupacao(caixas, zonas, estado, capture_ts)
for tipo, zid, tid, ts in eventos: print(f'[OK] Zona {zid}: {tipo} track {tid}')  # console, sem acumular
overlay.desenhar_tripwires(frame, zonas)
overlay.desenhar_rois(frame, zonas)
overlay.desenhar_contadores(frame, estado)
overlay.desenhar_hud(frame, fps, len(caixas))
```
`camera_id` na Fase 2: `"camera_0"` fixo (fase single-câmera; D-08 deixa o mapeamento como discrição — recomendação: constante no topo de `main()`, evoluída na Fase 6).

### Anti-Padrões a Evitar
- **Contar por posição ("anchor tocou a linha"):** conta repetida de quem para em cima da linha. Contar **transição de lado**.
- **Ocupação = entradas − saídas:** deriva o dia inteiro (Pitfall 4). Recontar por geometria.
- **Manter `track_states` sem poda:** vazamento de memória em execução longa; podar com margem 2× track_buffer.
- **Reconciliar só `crossed`:** ID recomeça do 1 após reset de tracker → estado velho bloqueia track novo. Descartar `track_states` inteiro.
- **`time.time()` no processamento para reset:** quebra determinismo e viola o contrato de `capture_ts` (Pitfall 6) — usar `capture_ts`/`agora` injetado.
- **Acumular eventos numa lista em RAM:** os eventos ENTROU/SAIU de cada frame são impressos e descartados; a Fase 3 cria a fila persistente. Lista acumulada é vazamento de memória e risco LGPD (trilha em RAM longa).
- **Contar no primeiro frame do track:** mesmo que já apareça "do outro lado" da linha (sem transição observada) e sem debounce ≥ 3 frames (D-10c).
- **Usar centroide da caixa em vez de bottom-center:** D-10a/D-14 travado; centroide pisca mais com oscilação vertical da caixa.

## Don't Hand-Roll

| Problema | Não construir | Use | Por quê |
|----------|---------------|-----|---------|
| Ponto dentro/fora de polígono | Ray-casting próprio | `cv2.pointPolygonTest` | Função nativa estável, testada há décadas; semântica (dentro/borda/fora) verificada em cv2 5.0.0. |
| Parse de YAML | Parser YAML próprio / regex | `yaml.safe_load` (PyYAML) | `safe_load` já bloqueia objetos arbitrários (só dict/list/str/num/bool/None); parser próprio é vetor de bug e de segurança (V5). |
| Preenchimento semitransparente | Canal alpha manual pixel a pixel | `cv2.fillPoly` + `cv2.addWeighted` | Padrão canônico, in-place, 3 linhas. |
| Dimensionamento de texto dos cards | Largura chutada | `cv2.getTextSize` | Mesmo padrão da Fase 1 (`overlay.py:10`); evita texto cortado/sobreposto. |
| Associação temporal (tracking) | Matching próprio por IoU | ByteTrack via `model.track` (Fase 1) | Já resolvido; oclusão e keep-alive são dele (Pitfall 3: "o tracker, não o detector, decide a precisão"). |
| Contador por linha/região | `ultralytics.solutions.ObjectCounter/RegionCounter` | `zona.py` próprio | **Decisão travada** (D-01 sem classes, D-07 YAML próprio, D-10/D-14 bottom-center, D-12 produto vetorial). O built-in usa centroide, heurística de eixo e `shapely` — ver Alternativas. |

**Insight-chave:** distância ponto→segmento **não existe** no OpenCV — são ~6 linhas de numpy (projeção com clamp). É o único "hand-roll" necessário e é trivial e testável; o resto da geometria é cv2.

## Common Pitfalls

### Armadilha 1: Flicker de caixa vira explosão de eventos
**O que dá errado:** caixa que some/reaparece (ou jitter na borda) dispara ENTROU/SAIU em rajada (critério 4 da fase).
**Por que acontece:** o lado muda várias vezes ou o ID morre/nasce perto da linha.
**Como evitar:** (a) só conta transição de lado, (b) debounce 3 frames de presença (D-10c), (c) `crossed` por track+zona (meio-ciclo), (d) hysteresis 15 px para travessia reversa (D-11), (e) ID reativado preserva contador — oclusão < 6 s não recomeça a contagem (Padrão 2).
**Sinal:** mais eventos do que pessoas no overlay; contadores que sobem com cena parada.

### Armadilha 2: Ocupação "aceitável" que deriva até ficar absurda
**O que dá errado:** ocupação 0 à noite vira 14 com o salão vazio — após horas de erros compostos.
**Por que acontece:** derivar de `entradas − saídas` sem correção (Pitfall 4).
**Como evitar:** recontar por geometria todo frame (D-14) — o número **não pode** derivar; clamp `[0, capacidade]`; resets de meia-noite e known-empty.
**Sinal:** ocupação nunca volta a 0; valores negativos; `IN − OUT ≠ OCUP` em qualquer frame.

### Armadilha 3: Track `crossed` velho bloqueia track novo após reset de tracker
**O que dá errado:** depois de reabrir a fonte (ou, na Fase 6, reconexão), o novo track 7 herda o `crossed` do antigo track 7 e a contagem para de funcionar.
**Por que acontece:** `BYTETracker.reset()` zera o contador de IDs (`BaseTrack._count = 0`) — IDs recomeçam do 1 (verificado no fonte).
**Como evitar:** `reconciliar_fonte` descarta `track_states` **inteiro** + `crossed` + contadores (D-17 ampliado). Na Fase 2 (processo reinicia) é gratuito; testar o hook.
**Sinal:** após reiniciar, entradas não incrementam apesar de pessoas cruzando.

### Armadilha 4: `track_states` crescendo sem limite em execução longa
**O que dá errado:** horas de execução → milhares de entradas mortas no dict → RAM cresce (e a poda é barata).
**Por que acontece:** IDs são monotônicos na sessão (nunca reutilizados) — cada pessoa nova é uma chave nova.
**Como evitar:** poda por `ultimo_frame_visto` com margem 2× track_buffer (Padrão 3).
**Sinal:** `len(track_states)` crescendo monotonicamente com cena vazia.

### Armadilha 5: YAML com erro silencioso → fase roda "sem zonas"
**O que dá errado:** typo em `tipo`/`pontos`/tag errada faz o sistema rodar lindamente... sem contar nada.
**Por que acontece:** convenção do repo é falhar suave (`[Aviso]` e seguir) — sem validação, zona inválida vira zona inexistente.
**Como evitar:** `carregar_zonas` valida e loga `[Aviso]` por zona inválida (skip) e `[Erro]` se o arquivo não existir; `main()` imprime `[OK] N zonas carregadas (camera_0)` para o usuário ver que a config entrou. Testes validam o YAML real de exemplo.
**Sinal:** overlay sem tripwire/ROI e sem card; sem mensagem de zonas carregadas.

### Armadilha 6: Travessia perdida em 5 FPS (pessoa "pula" a linha entre frames)
**O que dá errado:** com 5 FPS, um passo rápido pode mover o âncora de +30 px para −30 px em um frame.
**Por que acontece:** detecção por "ponto próximo da linha" falha quando o ponto nunca fica perto.
**Como evitar:** a **troca de lado** por produto vetorial detecta mesmo saltos de um frame (não depende de distância à linha); a guarda de bounding box do segmento (± margem) rejeita apenas "passar pela ponta da linha". Interpolação entre frames é desnecessária nesta fase.
**Sinal:** contagem menor que o esperado com andarilhos rápidos (revisitar na Fase 8 com cena real).

### Armadilha 7: Reset de meia-noite depende do fuso da máquina
**O que dá errado:** reset às 00:00 do fuso do servidor, não do hotel (se diferirem).
**Por que acontece:** `time.localtime(capture_ts)` usa o TZ do host.
**Como evitar:** documentar a premissa (host com TZ do hotel — A3); em produção, definir `TZ` no serviço. Manter UTC só no banco (Fase 3).
**Sinal:** resets em horário "errado" de ponto de vista do hotel.

### Armadilha 8: Eventos acumulados em RAM
**O que dá errado:** manter a lista de eventos da sessão para "debug" — memória cresce e a lista vira trilha individual em RAM (risco LGPD Art. 12 §2º — mesmo sem disco, trilha longa em RAM é indesejável e a Fase 3 terá fila própria).
**Por que acontece:** natural guardar os eventos na primeira implementação.
**Como evitar:** `verificar_tripwires` devolve eventos **do frame atual**; `main()` imprime e descarta. Sem acumulação.
**Sinal:** `len(eventos_acumulados)` crescendo; testes de memória de longa duração falhando.

## Code Examples

### Geometria da tripwire (zona.py — núcleo testável)
```python
# Source: derivado de PITFALLS.md #3 e verificado na máquina (numpy/cv2 5.0.0)
import numpy as np

def _bottom_center(xyxy):
    x1, y1, x2, y2 = xyxy
    return ((x1 + x2) / 2.0, y2)  # D-10a: âncora centro-inferior

def _lado(p1, p2, ponto):
    """Lado do ponto em relação ao vetor p1->p2: +1 esquerda, -1 direita, 0 na linha."""
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    wx, wy = ponto[0] - p1[0], ponto[1] - p1[1]
    s = vx * wy - vy * wx
    return 1 if s > 0 else (-1 if s < 0 else 0)

def _dist_ponto_segmento(p1, p2, ponto):
    """Distância euclidiana do ponto ao segmento p1-p2 (numpy, sem deps)."""
    p1, p2, q = np.asarray(p1, float), np.asarray(p2, float), np.asarray(ponto, float)
    ab = p2 - p1
    t = np.clip(np.dot(q - p1, ab) / np.dot(ab, ab), 0.0, 1.0)
    return float(np.linalg.norm(q - (p1 + t * ab)))
```

### Lógica de travessia (pseudocódigo por frame — transcrever no PLAN)
```python
# Por zona tripwire e por track presente:
# estado_do_track = track_states[tid]  (criado se novo; 'frames_vistos' += 1 neste frame)
# if estado_do_track['frames_vistos'] == 1:  # primeira aparição: só inicializa
#     track_states[tid]['posicoes'][zona_id]['lado_anterior'] = _lado(p1, p2, A); continue
# lado = _lado(p1, p2, A) or lado_anterior
# if lado != lado_anterior:
#     dist = _dist_ponto_segmento(p1, p2, A)
#     if zona_id not in crossed:
#         if frames_vistos >= 3:  # debounce D-10c
#             evento = 'ENTROU' if lado == lado_entrada else 'SAIU'   # lado_entrada = +1 se direcao=='entrada' else -1
#             crossed.add(zona_id); emite(evento)
#     elif dist > 15:  # hysteresis D-11 (só a travessia reversa é gated)
#         evento = 'ENTROU' if lado == lado_entrada else 'SAIU'
#         crossed.discard(zona_id); emite(evento)
#     lado_anterior = lado
```

### Ocupação + resets (zona.py)
```python
# Ocupação por frame (D-14); semântica pointPolygonTest verificada: 1.0 dentro, 0.0 borda, -1.0 fora
def _ocupacao_zona(tracks, zona):
    roi = np.array(zona['pontos'], dtype=np.int32)
    return sum(1 for _tid, xyxy, _conf in tracks
               if cv2.pointPolygonTest(roi, _bottom_center(xyxy), False) >= 0)

# Clamp (D-16) + resets (D-15), com 'agora' (epoch) injetável:
#   ocupacao = max(0, min(ocupacao_bruta, capacidade))
#   dia = time.localtime(agora).date(); if dia != estado['dia_atual']: zerar tudo + crossed; atualizar dia
#   if ocupacao_bruta > 0: estado[zona]['ultima_ocupacao_ts'] = agora
#   elif agora - estado[zona]['ultima_ocupacao_ts'] > 600: zerar contadores + crossed (known-empty)
```

### Overlay — ROI semitransparente (overlay.py, D-18)
```python
# Source: padrão canônico cv2 (fillPoly + addWeighted), funções verificadas em cv2 5.0.0
def desenhar_rois(frame, zonas):
    for zona in zonas:
        if zona['tipo'] != 'roi' and not zona.get('roi_pontos'):
            continue
        pts = np.array(zona['roi_pontos'] if zona.get('roi_pontos') else zona['pontos'],
                       dtype=np.int32)
        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], (255, 0, 0))          # azul (D-19)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)  # alpha 0.2 (D-18)
        cv2.polylines(frame, [pts], True, (255, 0, 0), 2)
```

### Fixture de teste determinística (tests/test_zona.py — D-20)
```python
# Cena sintética: track 1 anda perpendicular à linha y=240, de y=140 até y=340, 10 passos de 20 px
def caixa_bottom(tid, cx, y2, w=40, h=100):
    x1, x2 = cx - w / 2, cx + w / 2
    return (tid, [x1, y2 - h, x2, y2], 0.9)

def rodar_verificacao(cena, zonas, estado, track_states, agora=0.0):
    eventos = []
    for frame_idx, posicoes in enumerate(cena):
        tracks = [caixa_bottom(tid, cx, y2) for tid, cx, y2 in posicoes]
        eventos += zona.verificar_tripwires(tracks, zonas, estado, track_states,
                                            agora=agora + frame_idx / 5.0)
        zona.atualizar_ocupacao(tracks, zonas, estado, agora=agora + frame_idx / 5.0)
    return eventos

# test_tripwire_entrada_saida:
#   cena = [ [(1, cx, 140)], [(1, cx, 160)], ... [(1, cx, 340)] ]  -> 1 ENTROU
#   reverso  -> 1 SAIU (após dist > 15 px da linha)
# test_sem_dupla_contagem: cruzar, voltar dentro de 10 px da linha 2x -> só 1 ENTROU
# test_reset_diario: agora = 23:59:59.0 depois 00:00:01.0 -> contadores zerados
```
**Determinismo:** nenhuma chamada a `time.time()` no código de teste — `agora` e `frame_idx` são injetados; nenhum modelo, vídeo ou `cv2.imshow` necessário nos testes unitários → rodam em qualquer CI, < 1 s.

## State of the Art

| Abordagem antiga | Abordagem atual | Quando mudou | Impacto |
|------------------|-----------------|--------------|---------|
| Contagem por "ponto na linha" | Contagem por **transição de lado** (evento de cruzamento) | Sempre foi o padrão de produção (Pitfall 3) | Contar transições é o que elimina dupla contagem e explosão de eventos; posição é apenas estado auxiliar. |
| Ocupação = `entradas − saídas` | **Recontagem geométrica por frame** (`pointPolygonTest`) | Padrão de produção atual (Ultralytics RegionCounter confirma: "counts restart every frame... current occupancy") | Autocorreção total; o valor exibido é sempre verdade geométrica do frame. `[CITED: docs.ultralytics.com/guides/region-counting]` |
| `sv.ByteTrack` (supervision) | `model.track(tracker='bytetrack.yaml')` built-in | supervision 0.31 removeu ByteTrack; Ultralytics embute | Mantido da Fase 1; verificar de novo só se atualizar o ultralytics. |
| Tracker padrão ByteTrack | Tracker padrão **TrackTrack** | Ultralytics 8.4.x | **Continuar passando `tracker='bytetrack.yaml'` explicitamente** (Fase 1, Armadilha 1). |
| Contador por linha/região hand-roll com shapely | `solutions.ObjectCounter/RegionCounter` (built-in) | YOLO26 (2026) | Alternativa madura, **mas rejeitada** pelas decisões travadas (classes, centroide, heurística de eixo) — ver Alternativas. |

**Descontinuado/obsoleto:**
- `supervision.ByteTrack` — removido; não usar.
- Contagem por interseção de Linestring com shapely — desnecessária nesta fase (A2); adotar em Fase 8 só se validação de campo exigir.

## Assumptions Log

| # | Suposição | Seção | Risco se errado |
|---|-----------|-------|-----------------|
| A1 | Dentro da sessão, IDs do ByteTrack são monotônicos e **não** reutilizados (verificado no fonte 8.4.121); poda do `track_states` é só por memória | Padrão 2/3 | Baixo — verificado em fonte; se uma atualização do ultralytics mudar o comportamento, o reset de contador na reconciliação protege contra colisão (a poda vira 60 frames de janela de colisão, aceitável). |
| A2 | Troca de lado + guarda de bounding box do segmento é suficiente para a cena da fase (linha transversal, pedestres a 5 FPS) | Padrão 1, Alternativas | Médio — pedestre que passa **pela ponta** de uma linha curta pode gerar falso evento; com linha larga (amostra 1280x720) é improvável. Revisitar com interseção de segmentos na Fase 8 (QUA-03) se campo exigir. |
| A3 | Host roda no fuso do hotel → `time.localtime(capture_ts)` = "hora local do hotel" (D-15) | Padrão 4 | Baixo-médio — se o fuso divergir, o reset acontece em horário errado; em produção definir `TZ` do serviço. |
| A4 | Pin `pyyaml==6.0.3` no `requirements.txt` é aceitável (já instalada como transitiva do ultralytics) | Stack | Baixo — é upgrade de explicitude, não de versão. |
| A5 | `O(tracks × zonas)` por frame é desprezível a 5 FPS (< ~50 pessoas) | Padrão 4 | Baixo — 50 tracks × 4 zonas = 200 `pointPolygonTest` (microsegundos cada); medir só em pico real (Fase 8). |
| A6 | Semântica de `direcao` no YAML: o lado **positivo** do vetor P1→P2 é o sentido rotulado (`direcao: 'entrada'` → cruzar para a esquerda de P1→P2 = ENTROU); inverter P1/P2 (ou `direcao: 'saida'`) inverte o sentido | Padrão 1 | Médio — precisa de validação visual na primeira execução com o MP4 (se o usuário vir "Saiu" quando entrou, inverte-se o YAML, não o código). Registrar como convenção no PLAN. |

## Open Questions

1. **O vídeo-amostra tem alguém cruzando a linha y=240 proposta no `camera_0`?**
   - O que sabemos: o MP4 tem pessoas (614 caixas, 18 IDs em 60 frames — Fase 1), mas as trajetórias reais não foram inspecionadas; ninguém sabe se cruzam a linha de exemplo.
   - O que é incerto: se as coordenadas de exemplo do YAML produzem contagens não-zero na execução real.
   - Recomendação: o teste de integração sobre o MP4 usa **invariantes** (nunca negativo, monotônico, ocupação ≤ capacidade, sem exceção) — nunca contagens específicas (evita teste frágil); a **aceitação visual** (critério 1 da fase) é quem valida as coordenadas, e ajustar o YAML de exemplo é esperado na primeira execução.

2. **`capacidade` por câmera (D-07/D-16) vs. por zona?**
   - O que sabemos: decisão travada = `capacidade` no nível da câmera (`camera_0: capacidade: 30`), clamp aplicado à ocupação de cada zona.
   - O que é incerto: se o usuário quer tetos distintos por zona (ex.: recepção 10, hall 30).
   - Recomendação: implementar exatamente o travado (por câmera). Extensão futura (Fase 5, CRUD de zonas) deve permitir `capacidade` por zona com precedência — registrar como dívida, não implementar agora.

3. **`tipo: 'ambos'` (D-06: "uma zona pode ter os dois") no formato D-07?**
   - O que sabemos: D-07 mostra `tipo: "tripwire"` ou `tipo: "roi"` com um único `pontos`. D-06 diz que uma zona pode ter tripwire E ROI.
   - O que é incerto: como expressar os dois no YAML sem quebrar o formato travado.
   - Recomendação: chave opcional **`roi_pontos`** na zona `tipo: "tripwire"` (a linha usa `pontos`, o ROI usa `roi_pontos` com ≥ 3 pontos) — extensão mínima, compatível com o exemplo D-07 (que não a usa). Alternativa zero-extensão: duas entradas com o mesmo `id` (uma tripwire, uma roi) — o carregador funde por `id`. O planner escolhe; ambas são testáveis.

## Environment Availability

| Dependência | Necessária para | Disponível | Versão | Fallback |
|-------------|-----------------|------------|--------|----------|
| Python | Runtime | ✓ | 3.14.4 | — |
| opencv-python (cv2) | Geometria + overlay | ✓ | 5.0.0.93 (`pointPolygonTest`, `fillPoly`, `addWeighted` verificados) | — |
| numpy | Vetores/distância | ✓ | 2.5.2 | — |
| PyYAML | `config/zonas.yaml` | ✓ | 6.0.3 (transitiva do ultralytics) | Adicionar `pyyaml==6.0.3` ao `requirements.txt` (import direto) |
| ultralytics | ByteTrack (inalterado) | ✓ | 8.4.121 | — |
| pytest | Testes unitários | ✓ | 9.1.1 (requirements-dev) | — |
| Vídeo-amostra | Aceitação visual + integração | ✓ | `test/gemini_generated_video_8d21d35f.mp4` (480 frames @ 24 FPS) | — |
| Webcam (índice 0) | Aceitação visual | ✓ | verificada na Fase 1 | Vídeo-amostra |
| `config/` | Diretório do YAML | ✓ | já existe (contém `data.yaml`) | — |
| RTSP | — | ✗ (fora da fase) | — | Fase 6 |

**Dependências ausentes sem fallback:**
- Nenhuma — todo o necessário está presente ou é criado nesta fase (`config/zonas.yaml`, `zona.py`, `tests/test_zona.py`).

**Dependências ausentes com fallback:**
- Nenhuma.

## Validation Architecture

`workflow.nyquist_validation` está `true` em `.planning/config.json` — seção incluída.

### Test Framework
| Propriedade | Valor |
|-------------|-------|
| Framework | pytest 9.1.1 (instalado, suite da Fase 1 com 21 testes verdes) |
| Arquivo de config | nenhum — `tests/conftest.py` (fixtures `caminho_modelo`, `caminho_video_amostra` com skip) |
| Comando de execução rápida | `python -m pytest tests/ -x -q` |
| Comando de suíte completa | `python -m pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Comportamento | Tipo de teste | Comando automatizado | Arquivo existe? |
|--------|---------------|---------------|----------------------|-----------------|
| CNT-02 | Travessia entrada/saída conta exatamente 1+1 | unit (cena sintética) | `pytest tests/test_zona.py::test_tripwire_entrada_saida -x` | ❌ Wave 0 |
| CNT-02 | Sem dupla contagem: cruzar/voltar na borda conta só 1 | unit | `pytest tests/test_zona.py::test_sem_dupla_contagem -x` | ❌ Wave 0 |
| CNT-02 | Hysteresis: oscilar na linha não dispara rajada | unit | `pytest tests/test_zona.py::test_hysteresis -x` | ❌ Wave 0 |
| CNT-02 | Debounce: track instável (< 3 frames) não conta | unit | `pytest tests/test_zona.py::test_debounce_frames -x` | ❌ Wave 0 |
| CNT-02 | Poda: track morto some do `track_states` | unit | `pytest tests/test_zona.py::test_poda_track_states -x` | ❌ Wave 0 |
| CNT-02 | Invariantes no MP4 (monotônico, não-negativo, sem exceção) | integration (opcional, tolerante) | `pytest tests/test_integracao.py::test_contagem_amostra_invariantes -x` | ❌ Wave 0 |
| CNT-04 | Ocupação por `pointPolygonTest`: dentro/fora/borda | unit | `pytest tests/test_zona.py::test_ocupacao_roi -x` | ❌ Wave 0 |
| CNT-04 | Clamp `[0, capacidade]` | unit | `pytest tests/test_zona.py::test_clamp_capacidade -x` | ❌ Wave 0 |
| CNT-04 | Reset de meia-noite (relógio injetado) | unit | `pytest tests/test_zona.py::test_reset_diario -x` | ❌ Wave 0 |
| CNT-04 | Known-empty 10 min zera contadores | unit | `pytest tests/test_zona.py::test_reset_known_empty -x` | ❌ Wave 0 |
| CNT-04 | Reconciliação pós-reabertura limpa estado + track_states | unit | `pytest tests/test_zona.py::test_reconciliacao_fonte -x` | ❌ Wave 0 |
| CNT-02/CNT-04 | Validação do YAML de exemplo + tokens proibidos em `zona.py` | unit/static | `pytest tests/test_zona.py::test_zonas_yaml_camera0` + ampliar `test_privacidade.py` | ❌ Wave 0 |

### Sampling Rate
- **A cada commit de tarefa:** `python -m pytest tests/ -x -q`
- **A cada merge de wave:** `python -m pytest tests/ -q`
- **Gate da fase:** suíte completa verde antes do `/gsd-verify-work`, mais a verificação visual no MP4 (contadores subindo/descendo conforme pessoas cruzam a linha; ocupação coerente; `q` encerra; zero arquivos novos) — mesmo padrão humano da Fase 1 (`01-VERIFICATION.md`).

### Wave 0 Gaps
- [ ] `tests/test_zona.py` — cobre CNT-02/CNT-04 (11+ testes unitários determinísticos, sem modelo/vídeo/GUI)
- [ ] `tests/test_integracao.py` — novo teste de invariantes de contagem no MP4 (opcional, tolerante)
- [ ] `tests/test_privacidade.py` — adicionar `zona.py` à lista `_produto_files()` (varredura de tokens banidos) e manter o snapshot de disco
- [ ] `requirements.txt` — adicionar `pyyaml==6.0.3` (import direto)
- [ ] `config/zonas.yaml` — camera_0 com tripwire + ROI de exemplo (D-21); fixture de teste carrega o arquivo real

## Security Domain

`security_enforcement` ausente em config = habilitado.

### Applicable ASVS Categories
| ASVS Category | Aplica | Controle padrão |
|---------------|--------|-----------------|
| V2 Authentication | não | CLI local, sem autenticação (API é Fase 4) |
| V3 Session Management | não | Sem sessões de usuário |
| V4 Access Control | não | Sem API/endpoints |
| V5 Input Validation | **sim** | `yaml.safe_load` (nunca `yaml.load`); validação de schema de zonas (tipo, pontos ≥ 2/≥ 3, direcao, capacidade int > 0); zona inválida → `[Aviso]` + skip, arquivo ausente → `[Erro]` + execução sem zonas; coordenadas validadas como numéricas finitas |
| V6 Cryptography | não | Sem criptografia na fase |
| Privacidade de dados (LGPD) | **sim** | Nada em disco; eventos impressos e descartados; `track_states` em RAM com poda; nenhum track_id em arquivo; sem face/biometria (invariantes da Fase 1 mantidas) |

### Known Threat Patterns for stack (Python + OpenCV + Ultralytics)
| Padrão | STRIDE | Mitigação padrão |
|--------|--------|------------------|
| YAML com objetos arbitrários (`yaml.load`) | Tampering | `yaml.safe_load` + validação de tipos por zona (V5) |
| Persistência acidental de frame/evento (debug, acumular eventos) | Information Disclosure / Profiling (Art. 12 §2º) | Eventos do frame descartados após print; proibição de `imwrite`/`VideoWriter` estendida a `zona.py`; auditoria de disco automatizada |
| Trilha individual em RAM longa (eventos acumulados, track_states sem poda) | Profiling (Art. 12 §2º) | Poda do `track_states` por frame; eventos não acumulados; reconciliação limpa tudo na reabertura |
| Falso evento por geometria (contagem errada = decisão errada de gestão) | Tampering (lógica) | Transição de lado + debounce + hysteresis; testes determinísticos de CNT-02 |

## Sources

### Primary (HIGH confidence)
- Fonte instalado `ultralytics/trackers/basetrack.py` (8.4.121) — `BaseTrack._count` monotônico, `next_id()`, `reset_id()`; verificado 2026-10-09.
- Fonte instalado `ultralytics/trackers/byte_tracker.py` (8.4.121) — `STrack.activate/re_activate` (ID preservado), `BYTETracker.reset()`; verificado 2026-10-09.
- Fonte instalado `ultralytics/trackers/track.py` (8.4.121) — `on_predict_postprocess_end`: reset do tracker só com `persist=False` e troca de vídeo; verificado 2026-10-09.
- Probe executado na máquina (2026-10-09): `cv2.pointPolygonTest` (1.0/0.0/−1.0), `fillPoly`, `addWeighted`, `line`, `polylines`, `getTextSize`, `putText` presentes em cv2 5.0.0.93; `yaml` 6.0.3; pytest 9.1.1.
- `ultralytics/cfg/trackers/bytetrack.yaml` — `track_buffer: 30` (Fase 1, revalidado).
- `.planning/research/PITFALLS.md` — Pitfalls 3 (dupla contagem), 4 (drift de ocupação), 6 (timestamps), 10 (LGPD) — diretrizes incorporadas.
- `.planning/phases/01-.../01-RESEARCH.md`, `01-VALIDATION.md`, `01-VERIFICATION.md` — padrões de teste, comandos e formato (reutilizados 1:1).

### Secondary (MEDIUM confidence)
- Docs Ultralytics — Object Counting (tripwire com `ObjectCounter`) e Region Counting (ocupação por frame): https://docs.ultralytics.com/guides/object-counting e https://docs.ultralytics.com/guides/region-counting (verificados 2026-10-09; usados como alternativas e confirmação de padrão, não como stack da fase).

### Tertiary (LOW confidence)
- Nenhum — sem achados não verificados nesta pesquisa (as suposições A1–A6 estão sinalizadas e derivam de fonte instalado ou derivação lógica).

## Metadata

**Confidence breakdown:**
- Stack padrão: ALTA — versões e funções verificadas por probe na máquina e leitura do fonte instalado.
- Arquitetura (travessia/anti-duplicação): ALTA na lógica de transição de lado e no comportamento dos IDs (fonte instalado); MÉDIA na suficiência para cena real (A2 — debounce/hysteresis precisam de calibração visual na primeira execução, que é critério de aceitação da fase).
- Armadilhas: ALTA — derivadas de verificação na máquina e de `PITFALLS.md` #3/#4/#6/#10.
- Config YAML/resets: MÉDIA — schema travado em D-07; extensão `roi_pontos`/`tipo: ambos` é recomendação (Open Question 3); fuso do reset é premissa documentada (A3).

**Pesquisado em:** 2026-10-09
**Válido até:** ~2026-11-08 (30 dias). Revalidar comportamento de IDs/tracker do ByteTrack se o ultralytics for atualizado; revalidar coordenadas do `camera_0` na primeira execução do MP4.