# Phase 2: Contagem por zona e ocupação em tempo real - Context

**Gathered:** 2026-10-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Contagem bidirecional por zona (tripwire) + ocupação instantânea por zona (ROI poligonal) em **1 câmera** (webcam ou vídeo-amostra), sobre o pipeline da Fase 1 (captura → YOLO corpo → ByteTrack efêmero). Base de privacidade mantida: nada em disco, IDs efêmeros, sem face/biometria.

Requisitos da fase: **CNT-02** (tripwire bidirecional sem dupla contagem), **CNT-04** (ocupação instantânea com reset/clamp diário e reconciliação).

Depende de: Fase 1 (módulos `captura.py`, `rastreio.py`, `overlay.py`, `main.py` funcionando).
</domain>

<decisions>
## Implementation Decisions

### Estrutura do Código

- **D-01:** Novo módulo **`zona.py`** na raiz do projeto (plano, sem pacote, sem `__init__.py`), importado pelo `main.py`. Segue convenção da Fase 1 (nomes em português, funções simples, sem classes).
- **D-02:** Configuração de zonas em **`config/zonas.yaml`** (legível, editável, versionado). Mapeia `camera_id` → lista de zonas (tripwires + ROIs) com coordenadas em pixels da resolução da fonte.
- **D-03:** Integração no `main.py`: após `rastreio.extrair_caixas()` (linha ~74), chamar `zona.verificar_tripwires()`, `zona.atualizar_ocupacao()`, `overlay.desenhar_contadores()` — antes do `desenhar_hud`.
- **D-04:** Estado em RAM mantido em `main()` (dict `estado = {zona_id: {'ocupacao': int, 'entradas': int, 'saidas': int}}` e `track_states = {track_id: {...}}`). Passado para funções de `zona.py` a cada iteração.
- **D-05:** Logs apenas no console (tags `[OK]`/`[Aviso]`/`[Erro]` em pt-BR) — nenhum arquivo de log em disco.

### Zonas e Tripwires

- **D-06:** Suporta **ambos**: tripwire (linha, 2 pontos) para contagem ENTROU/SAÍDA + ROI poligonal para ocupação instantânea. Uma zona pode ter os dois.
- **D-07:** Formato `config/zonas.yaml`:
```yaml
camera_0:  # webcam / vídeo-amostra
  zonas:
    - id: "recepcao"
      tipo: "tripwire"
      pontos: [[100, 240], [540, 240]]  # linha y=240
      direcao: "entrada"          # sentido que conta como ENTRADA
    - id: "hall"
      tipo: "roi"
      pontos: [[50, 50], [590, 50], [590, 360], [50, 360]]
  capacidade: 30
```
- **D-08:** `camera_id` = string (`"camera_0"`, `"camera_1"`, ...) — mapeia 1:1 com a fonte resolvida em `main.py` (`resolver_fonte`). Para desenvolvimento: define-se manualmente as coordenadas no YAML para o vídeo-amostra (1280x720) e webcam (resolução nativa).

### Lógica Anti-Duplicação (CNT-02)

- **D-09:** Estado por `track_id`: `{'last_zone': None, 'crossed': set(), 'frames_since_first_seen': 0, 'last_cross_ts': 0}`.
- **D-10:** Contagem só quando: (a) centroide bottom-center da caixa cruza a linha do tripwire, (b) `track_id` não tem essa `zona_id` em `crossed`, (c) `frames_since_first_seen >= 3` (debounce — track estável).
- **D-11:** Hysteresis: após cruzar, o track precisa afastar `> 15 px` da linha antes de permitir cruzamento reverso (evita oscilação na borda).
- **D-12:** Direção via produto vetorial: vetor da linha × vetor do movimento → ENTRADA/SAÍDA. Coerente com `direcao` do YAML.
- **D-13:** Evento emitido: `(tipo, zona_id, track_id, ts)` onde `tipo ∈ {'ENTROU', 'SAIU'}`.

### Ocupação Instantânea + Reset/Clamp (CNT-04)

- **D-14:** Ocupação recalculada todo frame: `ocupacao[zona_id] = sum(1 for track in tracks if pointPolygonTest(roi, bottom_center(track)) >= 0)`.
- **D-15:** Reset diário: à meia-noite (hora local do hotel) **OU** quando `ocupacao == 0` por `> 10 min` (condição known-empty) → zera `ocupacao`, `entradas`, `saidas`, e limpa `crossed` dos tracks daquela zona.
- **D-16:** Clamp: `max(0, min(ocupacao, capacidade_da_zona))` — `capacidade` vem do YAML por câmera.
- **D-17:** Reconciliação pós-reconexão (preparação Fase 6): ao reabrir fonte (`captura.abrir_fonte`), zera `ocupacao` e `crossed` daquela `camera_id`.

### Overlay Visual

- **D-18:** Estende `overlay.py` com:
  - `desenhar_tripwires(frame, zonas)` — linhas: verde (entrada), vermelho (saída), label com `zona_id`.
  - `desenhar_rois(frame, zonas)` — polígonos semi-transparentes (azul, alpha 0.2).
  - `desenhar_contadores(frame, estado)` — cards no canto superior direito: `Zona X: IN 12 | OUT 7 | OCUP 5`.
- **D-19:** Cores: laranja caixas (existente), verde/vermelho tripwires, azul ROIs, branco/preto HUD.

### Testes

- **D-20:** Novo arquivo `tests/test_zona.py` com fixtures:
  - `zonas_config` carrega `config/zonas.yaml` (ou dict inline para isolamento).
  - `test_tripwire_entrada_saida`: track cruza linha → conta 1 entrada, 1 saída.
  - `test_sem_dupla_contagem`: mesmo track cruza/volta → conta só 1.
  - `test_ocupacao_roi`: tracks dentro/fora do polígono → ocupação bate.
  - `test_reset_diario`: mock time → meia-noite zera tudo.
  - `test_hysteresis`: track oscila na linha → não conta duplicado.
- **D-21:** `config/zonas.yaml` inclui definição para `camera_0` (vídeo-amostra 1280x720) com tripwire + ROI de exemplo.

### Agent's Discretion

- Assinatura exata das funções de `zona.py` (parâmetros, ordem, tipos de retorno).
- Estrutura interna do `track_states` (dict vs dataclass simples).
- Como `main.py` obtém `camera_id` a partir da fonte resolvida (webcam 0 → `"camera_0"`, arquivo → `"camera_0"`, RTSP futuro → `"camera_N"`).
- Valores exatos de `debounce_frames=3`, `hysteresis_px=15`, `reset_idle_min=10` — podem virar constantes no topo de `zona.py`.
- Se `desenhar_tripwires`/`desenhar_rois` vão em `overlay.py` ou `zona.py` (preferência: `overlay.py` por ser desenho).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §Phase 2 — goal, success criteria (4 itens) e requisitos CNT-02, CNT-04
- `.planning/REQUIREMENTS.md` — CNT-02 (tripwire bidirecional), CNT-04 (ocupação instantânea com reset/clamp)
- `.planning/context/DESENHO_POR_FASE.md` §Fase 2 — detalhamento (antes em `docs/DOCUMENTACAO_PROJETO_E_LGPD/09_PLANO_DE_FASES_V1.md`)

### Conformidade (obrigatório em toda decisão de código)
- `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` — 11 condições vinculantes
- `.planning/PROJECT.md` — Out of Scope permanente, Core Value, Key Decisions

### Convenções e código existente (Fase 1)
- `AGENTS.md` — regras do projeto
- `main.py`, `captura.py`, `rastreio.py`, `overlay.py` — referência atual
- `.planning/codebase/STRUCTURE.md` — papéis dos arquivos
- `.planning/codebase/CONVENTIONS.md` — nomenclatura, imports, estilo
- `.planning/phases/01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero/01-CONTEXT.md` — decisões D-01..D-06 da Fase 1

### Pesquisa técnica
- `.planning/research/PITFALLS.md` — Pitfalls 3, 4, 5 (double counting, occupancy drift, dwell fragments) — endereçados aqui
- `.planning/research/SUMMARY.md` — arquitetura recomendada, stack
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (Fase 1)
- `captura.abrir_fonte/capturar` — fonte de vídeo + `capture_ts`
- `rastreio.carregar_modelo/rastrear/extrair_caixas` → lista de `(id, xyxy, conf)`
- `overlay.desenhar_caixas/desenhar_hud` — desenho in-place no frame
- `main.resolver_fonte/resolver_modelo` — CLI + fallback de pesos
- Laço `while` em `main.py:65-90` — ponto de integração

### Established Patterns
- Módulos planos na raiz, funções `snake_case`, imports stdlib→terceiros
- `base_dir = os.path.dirname(os.path.abspath(__file__))` para caminhos
- Logs console `[OK]`/`[Aviso]`/`[Erro]` pt-BR
- `cv2.rectangle`, `cv2.putText`, `cv2.pointPolygonTest` para geometria
- Guard `if __name__ == "__main__": main()`

### Integration Points
- `main.py` importa `zona` e chama no laço após `extrair_caixas`
- `config/zonas.yaml` lido uma vez no startup por `zona.carregar_zonas(camera_id)`
- Estado (`estado`, `track_states`) vive em `main()` e é passado por referência
- Futuro: `config/zonas.yaml` ← dashboard (Fase 5) → PostgreSQL (Fase 3)
</code_context>

<specifics>
## Specific Ideas

- "Zonas são configuração, não código" — YAML editável, recarregável sem restart.
- Tripwire + ROI na mesma zona: tripwire conta, ROI mede ocupação.
- Bottom-center da caixa como âncora (não centro) — mais estável para pessoas em pé.
- Reset por known-empty é mais robusto que só meia-noite (cobre madrugada cedo).
- Clamp evita ocupação negativa (bug visual) e acima da capacidade (sinal de erro).

</specifics>

<deferred>
## Deferred Ideas

- MTMCT / Re-ID entre câmeras — FORA DO ESCOPO (LGPD Art. 12 §2º, Fase 7+ se houver base legal).
- Heatmap de densidade — Fase 7 (DWL-02).
- Dashboard CRUD de zonas — Fase 5 (DSH-01/DSH-03).
- Persistência de eventos ENTROU/SAÍDA no PostgreSQL — Fase 3 (API-01).
- Validação contra contagem manual em pico — Fase 8 (QUA-03).

</deferred>

---

*Phase: 02-contagem-por-zona-e-ocupa-o-em-tempo-real*
*Context gathered: 2026-10-08*