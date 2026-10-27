# Plano Completo v1 (Mestre) — Visão Computacional para Hotelaria (Analytics de Fluxo)

> **Documento mestre de referência e alinhamento** — une requisitos, roadmap e detalhamento técnico de cada uma das 9 fases do v1, adaptado ao cenário operacional vigente.
> **Data de atualização:** 2026-10-26 · **Status:** Fases 1 e 2 concluídas (33 testes verdes) · Pronto para a Fase 3.
> **Base legal verificada:** LGPD (Lei 13.709/2018) e Marco Civil da Internet (Lei 12.965/2014) — ver `.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md`, `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` e `.planning/context/PERGUNTAS_FREQUENTES_TECNICAS.md`.

---

## 1. O que é o sistema

Câmeras de segurança do hotel viram sensores de negócio: **contagem de pessoas por zona, ocupação em tempo real, tempo de permanência (dwell) e mapa de calor de fluxo** — para o hotel saber *quantas pessoas estão em cada lugar, quando e por quanto tempo ficam*, sem nunca identificar ninguém.

**Base do projeto:** o detector já existente (`main.py`, YOLO CrowdHuman, ~320 FPS em GPU) — evoluindo de forma vertical e incremental pelas fases planejadas, sempre com **privacidade por construção**.

### Invariantes obrigatórios em todas as fases

| Invariante | Base legal / Operacional |
|---|---|
| Saída **exclusivamente agregada** — nenhum dado por-pessoa é gravado | LGPD art. 12 §2º |
| **Zero associação entre câmeras** — nem por ID, nem por silhueta, nem por aparência (sem MTMCT/Re-ID) | LGPD art. 12 §2º + decisão do projeto |
| **Frames de vídeo nunca tocam disco** — imagem vive só na RAM durante a inferência | LGPD art. 6º III (minimização) |
| Face, biometria, demografia ou emoção **nunca** existem no código | LGPD art. 11 (dado sensível) |
| IDs de rastreamento (ByteTrack) morrem ao sair do quadro, **intra-câmera** e nunca persistidos | LGPD art. 6º III (necessidade) |
| **Auditoria automatizada como guarda técnica** — `tests/test_privacidade.py` varre o repositório e **falha o build** caso haja violação (IDs individuais, trilhas, frames em disco ou dados sensíveis). | LGPD arts. 6º III e 12 §2º + *Privacy by Design* |
| **Nenhum stream real com hóspedes antes do gate da Fase 9** — fases 1–8 usam só webcam, vídeos-amostra e MediaMTX local | LGPD art. 7º IX + art. 10 §3 (LIA formal ao fim da Fase 9) |

**Risco se violado:** sanções administrativas previstas na **LGPD art. 52** (multa de até **2% do faturamento, limitado a R$ 50.000.000,00 por infração**), além de advertência, publicação da infração, bloqueio ou eliminação dos dados, conforme o caso.

### 1.1 Fundamentos legais e adequação à LGPD

O desenho deste projeto busca adequação à **LGPD (Lei nº 13.709/2018)** e ao **Marco Civil da Internet (Lei nº 12.965/2014)** com base nos seguintes fundamentos:

| Dispositivo | Fundamento | Aplicação prática no projeto |
|---|---|---|
| **LGPD art. 5º, I** | Conceito de dado pessoal | Reconhece-se que, **durante a inferência**, há tratamento de dado pessoal (imagem/caixas). Esse tratamento é **efêmero**: ocorre apenas em RAM, **não** é gravado em disco e é descartado assim que a inferência é finalizada. |
| **LGPD art. 6º, I–III** | Princípios da boa-fé, adequação, necessidade e minimização | **Apenas o estritamente necessário.** Usa-se detecção por **corpo**, rastreamento **intra-câmera efêmero** (ByteTrack), **ROI-only** com interseção de área e **saída exclusivamente agregada**. Frames **nunca** vão para disco. |
| **LGPD art. 7º, IX** | Interesse legítimo | Base legal prevista para o v1. Será formalizada por meio da **LIA** (*Legitimate Interest Assessment*) na **Fase 9**, demonstrando necessidade, proporcionalidade e equilíbrio com os direitos e liberdades dos titulares. |
| **LGPD art. 11** | Tratamento de dados sensíveis | **Vedado.** Não há tratamento de dados biométricos, faciais, de origem étnica/racial, religiosa, política, genética ou de saúde. O código é auditado para garantir essa vedação. |
| **LGPD art. 12, caput e §2º** | Dado anonimizado / agregação | O objetivo é que os dados **persistidos** sejam **anônimos irreversíveis**. Apenas estatísticas por **zona × janela** (médias, contagens, histogramas, heatmap agregado) são gravadas. **Após a agregação, toda informação individual é descartada.** O próprio sistema **não mantém chaves, mapeamentos ou índices** capazes de reverter esses agregados para um indivíduo. Se não houver **meios razoáveis** de reidentificação a partir do banco, incide o art. 12 da LGPD. |
| **LGPD art. 37** | **ROPA** (*Registro das Operações de Tratamento*) | Será elaborado e mantido atualizado na **Fase 9**, registrando finalidades, categorias de dados tratados (efêmeros x agregados), medidas de segurança e minimização. |
| **LGPD art. 38** | **RIPD** (*Relatório de Impacto à Proteção de Dados*) | Obrigatório antes de qualquer **stream real com hóspedes**. Deve avaliar riscos, impactos e as medidas mitigadoras adotadas por *Privacy by Design*. |
| **LGPD art. 41** | Encarregado (**DPO**) | Designação formal com **nome e canal de contato** divulgado, apto a receber solicitações de titulares e atuar perante a **ANPD**. |
| **LGPD art. 46** | Segurança do tratamento | Medidas técnicas e administrativas para proteção dos dados: acesso restrito ao PostgreSQL/API, credenciais em `.env` (fora do repositório), princípio do menor privilégio, escrita fora do *hot-loop*, logs segregados e com acesso restrito, **frames e trilhas apenas em RAM**, **nunca** gravados em disco. |
| **LGPD art. 48** | Comunicação de incidente de segurança | Previsto no **Plano de Resposta a Incidentes** da **Fase 9**, com critérios para contenção, avaliação, eventual comunicação à ANPD e, quando cabível, aos titulares. |
| **Marco Civil da Internet (Lei nº 12.965/2014) art. 15** | Registros de acesso a aplicações de internet | Justifica a geração de **logs de acesso** na **API** (Fase 4), com **retenção por 6 meses**, sob sigilo, finalidade exclusiva de auditoria e segurança. |

> **Regra de ouro (critérios de conformidade):** *"Se for possível reconstituir o trajeto ou o tempo individual de alguém consultando o banco, está errado. Se só for possível obter médias, contagens, histogramas e dados agregados por zona/tempo, está correto."*  
> **Teste decisivo da Fase 9:** inspecionar código + consultar o banco e comprovar que **não existem meios razoáveis** de reidentificação a partir dos dados persistidos.

---



## 2. Resumo de Requisitos e Status Atual (v1)

* **Status atual:** **6/27** requisitos concluídos (**ING-01, ING-03, CNT-01, CNT-02, CNT-03, CNT-04**).
* **Escopo vigente:** Contagem **ROI-only** (ocupação por área via interseção $\text{Área}(\text{Objeto}) \cap \text{Área}(\text{ROI})$). O **tripwire bidirecional** foi desativado por decisão do projeto e permanece **comentado** no código (`zona.py`, `overlay.py`, `main.py`), não removido.
* **Testes:** **33/33** verdes (`./.venv/bin/python -m pytest`).
* **Verificação GSD:** Fase 1 (`01-VERIFICATION.md`) e Fase 2 (`02-VERIFICATION.md`) aprovadas com status **PASSED**.

### Categorias de Requisitos

| Categoria | Abrangência | Status |
|---|---|---|
| **ING (Ingestão)** | Webcam, vídeos-amostra e futuras câmeras RTSP. Frames voláteis em RAM. | 2/3 concluídos |
| **CNT (Contagem & Ocupação)** | Detecção apenas por corpo, ByteTrack efêmero intra-câmera, ocupação por ROI e interseção de área. | 4/4 concluídos |
| **DWL (Permanência & Fluxo)** | Dwell time e heatmap de densidade **apenas agregados**. | 0/2 pendentes |
| **API (Dados/API)** | PostgreSQL restrito a configuração + agregados, FastAPI somente-leitura, TTL e logs de acesso 6 meses (Marco Civil). | 0/4 pendentes |
| **DSH (Dashboard)** | Ocupação ao vivo, séries temporais, dwell e heatmap agregados. | 0/3 pendentes |
| **PRV (Privacidade)** | Auditoria automatizada, RIPD/LIA/ROPA, aviso de monitoramento, encarregado (DPO), sem dado por-pessoa. | 0/5 pendentes |
| **QUA (Qualidade)** | Latência ≤ 5ms/frame, escrita fora do loop, testes críticos, acurácia vs marcação manual. | 0/3 pendentes |
| **OPS (Operação)** | Multi-câmera/RTSP, reconexão/watchdog, ambiente reproduzível, plano de resposta a incidente. | 0/3 pendentes |

**Cobertura v1:** 27/27 requisitos mapeados no roadmap, sem órfãos.

### 2.1 Mapeamento dos requisitos citados (ING e CNT)

Os IDs abaixo são os que já foram validados e constam como concluídos nas Fases 1 e 2. A fonte oficial deles é [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md).

| ID | Categoria | Descrição | Status | Evidência |
|---|---|---|---|---|
| **ING-01** | Ingestão (ING) | Suportar ingestão via **webcam** para desenvolvimento e testes locais. | **Concluído** | `main.py`, `captura.py` |
| **ING-03** | Ingestão (ING) | Suportar ingestão de **vídeos-amostra locais** para validação, sem gravação de frames em disco. | **Concluído** | `main.py`, `captura.py`, `tests/test_privacidade.py` |
| **CNT-01** | Contagem & Ocupação (CNT) | Realizar **detecção apenas por corpo** utilizando o modelo **YOLO CrowdHuman**. Sem detecção facial, biometria ou classificação demográfica. | **Concluído** | `main.py`, `.planning/phases/01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero/` |
| **CNT-02** | Contagem & Ocupação (CNT) | Contagem por **zona poligonal** definida em `config/zonas.yaml`, com suporte a múltiplas ROIs por câmera. | **Concluído** | `zona.py`, `config/zonas.yaml`, `tests/test_zona.py` |
| **CNT-03** | Contagem & Ocupação (CNT) | Rastreamento **efêmero e intra-câmera** com **ByteTrack** para evitar dupla contagem da mesma pessoa entre frames consecutivos. Os IDs morrem ao sair do quadro e **nunca** são persistidos. | **Concluído** | `rastreio.py`, `main.py`, `tests/test_rastreio.py` |
| **CNT-04** | Contagem & Ocupação (CNT) | Calcular ocupação por **interseção de área** `Área(Objeto) ∩ Área(ROI)`, priorizando o **centro-inferior da bounding box** (pé no chão) para o teste de presença, em linha com o escopo **ROI-only**. | **Concluído** | `zona.py`, `overlay.py`, `tests/test_zona.py`, `tests/test_overlay.py` |

> **Observação:** Os demais requisitos listados na tabela abaixo permanecem **pendentes** conforme `.planning/REQUIREMENTS.md` e `.planning/ROADMAP.md`. Estes 6 são exatamente os que foram auditados e aprovados na verificação GSD das Fases 1 e 2.

### 2.2 Mapeamento completo dos requisitos citados neste plano

Todos os IDs abaixo aparecem nos cabeçalhos `*Requisitos:*` das Fases 3–9. Fonte oficial: [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md).

#### Ingestão (ING)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **ING-02** | Suportar ingestão via **RTSP** com reconexão automática e tolerância a falhas de stream. | **Pendente** | Fase 6 |

#### Contagem & Ocupação (CNT)

*Todos os requisitos CNT do v1 já foram concluídos (ver 2.1).*

#### Persistência & Dados / API (API)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **API-01** | Persistir **apenas métricas agregadas** no PostgreSQL, com escrita assíncrona em lote fora do loop de vídeo. | **Pendente** | Fase 3 |
| **API-02** | Disponibilizar **API FastAPI somente-leitura** para consulta de métricas agregadas. | **Pendente** | Fase 4 |
| **API-03** | Implementar **logs de acesso** auditáveis com retenção por **6 meses** conforme Marco Civil da Internet (Lei 12.965/2014). | **Pendente** | Fase 4 |
| **API-04** | Aplicar **política de TTL/expurgo** para métricas, respeitando os princípios de minimização e limitação de retenção. | **Pendente** | Fase 4 |

#### Analytics & Permanência (DWL)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **DWL-01** | Calcular **tempo de permanência (dwell time)** por zona, em **RAM efêmero**, com agregação imediata e **descartar** o dado individual. | **Pendente** | Fase 7 |
| **DWL-02** | Gerar **heatmap de densidade agregado** por célula×janela, **sem** traços, rotas ou histórico por-pessoa. | **Pendente** | Fase 7 |

#### Dashboard (DSH)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **DSH-01** | Exibir **ocupação em tempo real** por zona no dashboard operacional. | **Pendente** | Fase 5 |
| **DSH-02** | Exibir **séries temporais históricas** das métricas agregadas com filtros por período. | **Pendente** | Fase 5 |
| **DSH-03** | Exibir **histograma de permanência** e **heatmap agregado** de densidade. | **Pendente** | Fase 7 |

#### Qualidade (QUA)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **QUA-01** | Garantir **isolamento do hot-loop**: nenhuma chamada SQL dentro do `while True`. Latência **≤ 5 ms/frame**. | **Pendente** | Fase 3 |
| **QUA-02** | Cobrir regras críticas com **testes automatizados** (zona, dwell/timeout, fila/batch writer, reconexão, watchdog). | **Pendente** | Fase 8 |
| **QUA-03** | Realizar **validação de campo** com marcação manual (definir e aplicar **"quem conta"**) e documentar relatório de acurácia. | **Pendente** | Fase 8 |

#### Operação (OPS)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **OPS-01** | Suportar **múltiplas câmeras RTSP** com workers isolados, **reconexão exponencial** e **watchdog** de staleness. | **Pendente** | Fase 6 |
| **OPS-02** | Disponibilizar **ambiente reproduzível** via `docker-compose.yml` (PostgreSQL + API + Dashboard). | **Pendente** | Fase 5 |
| **OPS-03** | Elaborar e aprovar **plano de resposta a incidentes** como parte do gate da Fase 9. | **Pendente** | Fase 9 |

#### Privacidade & Governança (PRV)

| ID | Descrição | Status | Fase |
|---|---|---|---|
| **PRV-01** | Executar **auditoria automatizada** repo-wide em busca de `track_id`, `session_id`, `sessoes`, `session_traces`, `embedding`, rota/jornada. Garantir **zero frames em disco** e **sem face/biometria**. | **Pendente** | Fase 9 |
| **PRV-02** | Elaborar **RIPD** (Relatório de Impacto à Proteção de Dados). | **Pendente** | Fase 9 |
| **PRV-03** | Elaborar **LIA** (Legitimate Interest Assessment) com análise de necessidade, proporcionalidade e equilíbrio. | **Pendente** | Fase 9 |
| **PRV-04** | Elaborar **ROPA** (Registro das Operações de Tratamento) e definir formalmente o **Encarregado (DPO)** com canal de contato. | **Pendente** | Fase 9 |
| **PRV-05** | Garantir **aviso de monitoramento** nas áreas, revisar logs/API com retenção por 6 meses e obter **parecer jurídico-técnico favorável** para liberação de streams reais com hóspedes. | **Pendente** | Fase 9 |

---





## 3. Detalhamento Foco a Foco das 9 Fases

### Fase 1 — Fatia vertical single-câmera (captura, detecção, rastreio efêmero)
* **Status:** Concluída (2026-10-08)
* **Dependências:** Nenhuma
* **Requisitos:** ING-01, ING-03, CNT-01, CNT-03

**O que constrói:**
Pipeline mínimo funcional em `main.py`: captura (`captura.py`), detecção de corpo com **YOLO CrowdHuman**, rastreamento efêmero com **ByteTrack** intra-câmera (`rastreio.py`) e renderização em tempo real (`overlay.py`), sem qualquer persistência.

**Como funciona:**
1. Fonte definida por argumento (webcam/arquivo). `capture_ts` carimbado imediatamente após `cap.read()`.
2. Inferência restrita a `classes=[0]` (apenas corpo). Sem detecção facial ou módulos de biometria.
3. `model.track` com `tracker='bytetrack.yaml'`, `persist=True`. IDs existem **apenas enquanto a pessoa permanece no quadro**.
4. Extração com guarda: caso `boxes.id` seja `None`, retorna lista vazia.
5. Overlay desenha in-place no `ndarray`. **Nenhum** `cv2.imwrite`, `cv2.VideoWriter` ou gravação de arquivo.

**Garantias:**
- Frames voláteis em RAM, descartados após inferência.
- IDs efêmeros, nunca gravados em arquivo ou banco.
- Sem face, biometria, demografia ou emoção.
- Auditoria automatizada via `tests/test_privacidade.py`.

**Critérios atendidos:** 21 testes da fase integrados à suíte atual (33/33 verdes). Verificação GSD aprovada.

---

### Fase 2 — Contagem por zona e ocupação em tempo real (ROI-only)
* **Status:** Concluída (2026-10-12)
* **Dependências:** Fase 1
* **Requisitos:** CNT-02, CNT-04

**O que constrói:**
Módulo `zona.py` para definição e validação de polígonos ROI em `config/zonas.yaml`. Cálculo de ocupação instantânea por **presença** e por **interseção de área** (`Área(Objeto) ∩ Área(ROI)`). Integração com `overlay.py` e `main.py`, com clamp por capacidade, reset diário, reconciliação ao reiniciar a fonte e poda de `track_states`.

**Como funciona:**
1. **Carregamento:** `carregar_zonas()` lê e normaliza ROIs com validação de schema. Uso exclusivo de `yaml.safe_load`.
2. **Âncora para presença:** Prioritariamente o **centro-inferior da bounding box** (`_bottom_center`) para aproximar o pé no chão. Teste com `cv2.pointPolygonTest`. Há *fallback* com centro geométrico e tratamento para pessoas cortadas pela borda inferior.
3. **Interseção de área:** Máscara do ROI gerada com `cv2.fillPoly`. Máscara das pessoas gerada com o **terço inferior** da bounding box por padrão (`modo='base'`), reduzindo superestimação por perspectiva. `intersecao = np.logical_and(pessoas_mask, roi_mask)`. `pct_area = (área_interseção / área_ROI) * 100`.
4. **Estabilização:** `clamp([0, capacidade])`, reset diário, `reconciliar_fonte()` ao trocar/reabrir fonte, `podar_track_states()` para limpar tracks inativos.
5. **Visualização:** Polígonos ROI, interseção destacada e contadores por zona exibidos no overlay, **sem gravação**.

**Garantias:**
- Foco estritamente **ROI-only**. O tripwire bidirecional permanece **comentado** em `zona.py`, `overlay.py` e `main.py`.
- Sem dupla contagem espúria e estável sob *flicker*.
- Mantém todos os invariantes de privacidade da Fase 1.
- Geometria avaliada *on-the-fly*: alteração dos pontos passa a valer no próximo frame (sem cache congelado).

**Critérios atendidos:** 10 testes em `tests/test_zona.py` + integração com overlay. Verificação GSD aprovada.

---

### Fase 3 — Persistência PostgreSQL (fila + escrita em lote)
* **Status:** Pendente
* **Dependências:** Fase 2
* **Requisitos:** API-01, QUA-01

**Objetivo:** Tornar as métricas **apenas agregadas** duradouras, sem jamais impactar o *hot-loop* de processamento de vídeo e sem persistir qualquer dado por-pessoa.

**O que constrói:**
Schema relacional PostgreSQL restrito a **configuração e métricas agregadas**. Fila assíncrona em memória com *batch writer* isolado do processamento de frames. Infraestrutura pronta para alimentar API e Dashboard nas fases seguintes.

**Como será feito (detalhado):**

1. **Schema estritamente restrito**
   - **Permitidas:** `cameras`, `zonas`, `metricas_fluxo_zona`. Nas fases corretas também `dwell_agregado_zona` e `heatmap_densidade_camada`.
   - **Vedadas:** `sessoes`, `session_traces` e qualquer tabela com trilha/jornada. **Nunca** conter colunas `track_id`, `session_id`, `id_rastreio_local`, `embedding`, `rota`, `jornada`.

2. **Gravação por janela temporal (não por frame)**
   - Ao fechar cada janela de tempo (sugerido **1 minuto**), o sistema calcula valores agregados por zona com base no `estado` corrente.
   - **Nunca** são gravados frames, caixas, coordenadas ou históricos individuais.
   - É gerada **1 linha agregada por (zona_id, janela_inicio, janela_fim)**.

3. **Fila em memória + Batch Writer fora do loop**
   - O worker de vídeo monta apenas **eventos agregados** e os coloca numa fila em memória.
   - Um *Batch Writer* em thread separada consome essa fila em lote (*size-or-time*: ex. N registros ou X segundos) e executa o `INSERT` no PostgreSQL.
   - **Nenhum** `cursor.execute()`, `commit()` ou chamada SQL pode ocorrer dentro do `while True` de captura/detecção/rastreamento. A latência do loop deve permanecer **≤ 5 ms/frame**.

4. **Idempotência e segurança**
   - Cada lote terá um identificador único (`batch_id`, UUID) para evitar duplicação em caso de reinício/reenvio.
   - Testes **negativos** obrigatórios: devem falhar caso se tente inserir `track_id`, criar `sessoes` ou `session_traces`.
   - Auditoria de schema para garantir ausência total de identificadores individuais.

**Estrutura alvo inicial (`metricas_fluxo_zona`):**

| Campo | Tipo | Finalidade |
|---|---|---|
| `id` | `BIGSERIAL` | Chave técnica |
| `zona_id` | `INT` FK → `zonas(id)` | Zona monitorada |
| `janela_inicio` | `TIMESTAMP WITH TIME ZONE` | Início da janela agregada |
| `janela_fim` | `TIMESTAMP WITH TIME ZONE` | Fim da janela agregada |
| `ocupacao_media` | `REAL` | Média da ocupação no intervalo |
| `pct_area_media` | `REAL` | Média do % de área ocupada no intervalo |
| `criado_em` | `TIMESTAMP WITH TIME ZONE` | Timestamp da gravação do agregado |

**Exemplo prático:** Para "Recepção" entre `14:00:00` e `14:01:00`, grava-se **exatamente 1 linha** com médias daquele intervalo. É **impossível** recuperar "quanto tempo ficou a pessoa X" a partir dessa linha.

**Critérios de sucesso:**
1. Banco criado **apenas** com tabelas de configuração e métricas agregadas (sem tabelas de rastreio/sessões).
2. Escrita em lote assíncrona, **completamente fora do loop de vídeo**.
3. Latência do loop ≤ 5 ms/frame mesmo com *batch writer* ativo.
4. Idempotência validada.
5. Testes automatizados de conexão e escrita agregada, além de **testes negativos** contra persistência por-pessoa.

---

### Fase 4 — API FastAPI de métricas e conformidade Marco Civil
* **Status:** Pendente
* **Dependências:** Fase 3
* **Requisitos:** API-02, API-03, API-04

**O que constrói:**
API **somente-leitura** com FastAPI para consulta das métricas já agregadas. Governança com política de **TTL**, logs de acesso auditáveis por **6 meses** sob sigilo (Marco Civil da Internet — Lei 12.965/2014).

**Como será feito:**
1. **Rotas restritas:** Apenas `GET`. Sem criação/edição/exclusão de dados.
2. **Resposta 100% agregada:** JSON com médias, contagens, ocupação, séries temporais, histogramas e heatmap agregado. **Nunca** retornar IDs individuais, trilhas ou identificadores.
3. **Logs de acesso:** Registrar IP, data/hora e ação consultada, com rotina de retenção/expurgo por **6 meses**.
4. **TTL por tipo de métrica:** Documentado e aplicado conforme necessidade operacional e minimização.
5. **Documentação interativa:** Swagger/OpenAPI para facilitar consumo pelo dashboard.

**Critérios de sucesso:**
1. Endpoints respondem **exclusivamente** com dados agregados.
2. Logs de acesso gerados e retidos exatamente por 6 meses sob sigilo.
3. TTL documentado e aplicado.
4. Auditoria confirma ausência de qualquer dado por-pessoa nas respostas.

---

### Fase 5 — Dashboard operacional de ocupação em tempo real
* **Status:** Pendente
* **Dependências:** Fase 4
* **Requisitos:** DSH-01, DSH-02, OPS-02

**O que constrói:**
Interface web leve conectada à API para visualização em tempo real da ocupação por zona, indicadores claros de lotação e séries temporais para apoio à gestão.

**Como será feito:**
1. **Tempo real:** Atualização via WebSocket para ocupação instantânea por zona.
2. **Séries históricas:** Filtros por período com gráficos objetivos.
3. **Indicador de frescor:** Exibir "atualizado há X segundos" para evitar confusão entre dado ao vivo e histórico.
4. **Ambiente reproduzível:** `docker-compose.yml` subindo PostgreSQL + API + Dashboard com um único comando.
5. **Foco operacional:** Interface simples, voltada a recepção/operação do hotel.

**Critérios de sucesso:**
1. Ocupação ao vivo por zona atualizando em tempo real.
2. Séries temporais filtráveis por período.
3. Ambiente ponta-a-ponta reproduzível via `docker-compose`.
4. Indicador de saúde/frescor da métrica.

---

### Fase 6 — Multi-câmera RTSP com reconexão e watchdog
* **Status:** Pendente
* **Dependências:** Fase 5
* **Requisitos:** ING-02, OPS-01

**O que constrói:**
Processamento paralelo de múltiplos fluxos RTSP com robustez para produção. Cada câmera com seu próprio worker e tracker **estritamente intra-câmera**.

**Como será feito:**
1. **Ingestão robusta:** Migração para abordagem mais estável com **PyAV** para fluxos RTSP.
2. **Workers por câmera:** Um worker dedicado por stream. Tracker, estado e zonas **totalmente isolados** entre câmeras.
3. **Reconexão automática:** Backoff exponencial em caso de perda de conexão.
4. **Watchdog de staleness:** Detecção de stream travado/congelado e disparo de reconexão sem derrubar o processo principal.
5. **Reconciliação segura:** Ao reconectar, estado reconciliado sem corromper contagens.
6. **Sem cruzamento:** **Proibido terminantemente** qualquer forma de associação entre câmeras (IDs, aparência, trajetória).

**Critérios de sucesso:**
1. Múltiplas câmeras RTSP processando simultaneamente.
2. Recuperação automática após queda de rede.
3. Watchdog funcional.
4. Contagens íntegros após reconexão.
5. **Isolamento absoluto** entre câmeras comprovado.

---

### Fase 7 — Analytics de permanência e heatmap agregado
* **Status:** Pendente
* **Dependências:** Fase 6
* **Requisitos:** DWL-01, DWL-02, DSH-03

**O que constrói:**
Módulo de *dwell time* e mapa de calor de densidade **exclusivamente agregados**. Exibidos no dashboard com total conformidade à LGPD.

**Como funciona (Privacy by Design):**

```text
RAM (efêmero):                         Banco (agregado):
trilha entra na zona 14:02:11          zona | janela  | n | soma_seg | min | max | histograma
sai ou some às 14:10:43 (duração 8m32s) ──▶ recepção | 14:02-14:03 | 9 | 4320 | 47 | 842 | 0-2:4 | 2-5:3 | 5-15:2 | 15+:0
(dados individuais morrem aqui — nunca gravados)
```

**Detalhamento:**

1. **Dwell em RAM:** Ao entrar na ROI, registra-se o timestamp efêmero. Ao sair ou ao desaparecer do quadro, calcula-se a duração **naquele instante**.
2. **Agregação imediata:** Soma-se à janela `zona × tempo`. São persistidos **apenas** `n_permanencias`, `soma_segundos`, `min_segundos`, `max_segundos` e `histograma` nas faixas **0–2, 2–5, 5–15, 15+ minutos**.
3. **Descartar individual:** Após agregar, **toda** informação que permita vincular àquela passagem específica é descartada da memória.
4. **Heatmap agregado:** Posições efêmeras são somadas por **célula × janela**. Gera-se um contador agregado por quadrícula. **Nunca** um traço, rota ou trajeto por pessoa.
5. **Fechamento de zumbis:** Mecanismo de *timeout* para fechar permanências não finalizadas corretamente.
6. **Dashboard:** Exibição de histograma de permanências e heatmap de densidade agregado.

**Garantias inegociáveis:**
- **Nenhuma linha por pessoa** em `dwell_agregado_zona`.
- **Nenhum identificador individual** em `heatmap_densidade_camada`.
- **Impossível** consultar "quanto tempo ficou X pessoa" via SQL.
- **Permitido** apenas perguntas agregadas: "Média de permanência por zona/horário".

**Critérios de sucesso:**
1. Apenas histograma/soma/n por `zona × janela` persistidos.
2. Heatmap gerado exclusivamente a partir de posições efêmeras, sem histórico individual.
3. Visualização funcional no dashboard.
4. Auditoria de schema confirma **zero** identificadores individuais.

---

### Fase 8 — Suíte de testes de carga, resiliência e validação de campo
* **Status:** Pendente
* **Dependências:** Fase 7
* **Requisitos:** QUA-02, QUA-03

**O que constrói:**
Bateria robusta de testes para validar regras críticas, resiliência e acurácia real do sistema.

**Como será feito:**
1. **Cobertura crítica:** Testes para ocupação por área/interseção, dwell+timeout, fila/batch writer, reconexão e watchdog.
2. **Resiliência:** Simulações de queda de banco, estouro de fila, perda/reconexão de câmeras.
3. **Carga leve:** Validação com múltiplos streams e comportamento sob carga.
4. **Validação manual:** Comparação com contagem feita manualmente em vídeo de pico (webcam/amostra). Definição escrita de **"quem conta"** aplicada e registrada.
5. **Relatório de acurácia:** Documentação com erro médio, faixa observada, limitações e justificativas.

**Critérios de sucesso:**
1. Suíte automatizada cobre regras críticas e passa integralmente.
2. Validação contra marcação manual documentada com relatório de acurácia.
3. "Quem conta" definido, aplicado e registrado.

---

### Fase 9 — Auditoria formal LGPD (RIPD/LIA/ROPA) e liberação de produção
* **Status:** Pendente
* **Dependências:** Fase 8
* **Requisitos:** PRV-01, PRV-02, PRV-03, PRV-04, PRV-05, OPS-03

**O que constrói:**
Auditoria jurídica-técnica completa e **gate obrigatório** antes de qualquer ligação de stream real com hóspedes.

**Atividades obrigatórias:**

| Item | Base Legal | Finalidade |
|---|---|---|
| **Auditoria de código automatizada** | PRV-01 | Varredura repo-wide por `track_id`, `session_id`, `session_traces`, `sessoes`, `embedding`, rota/jornada. Verificar ausência de frames em disco e ausência de face/biometria. |
| **RIPD (Relatório de Impacto à Proteção de Dados)** | LGPD art. 5º XVII, art. 38 | Identificação de riscos, medidas mitigadoras e avaliação geral. |
| **LIA (Legitimate Interest Assessment)** | LGPD art. 10 §3º | Justificativa do interesse legítimo, necessidade, proporcionalidade e equilíbrio com direitos dos titulares. |
| **ROPA (Registro das Operações de Tratamento)** | LGPD art. 37 | Registro completo das operações realizadas. |
| **Aviso de monitoramento** | LGPD art. 6º IV | Placas visíveis nas áreas monitoradas, em linguagem clara. |
| **Encarregado (DPO)** | LGPD art. 41, Res. ANPD 18/2024 | Indicação formal com nome e canal de contato publicado. |
| **Plano de resposta a incidente** | LGPD art. 48 | Procedimento para identificação, contenção, avaliação e comunicação à ANPD e, quando cabível, aos titulares. |
| **Revisão de logs/API** | Marco Civil art. 15 | Conferir logs de acesso com retenção por 6 meses sob sigilo. |

**Teste prático decisivo:** Tentar, por inspeção de código e por consulta ao banco, **reconstituir o trajeto ou o tempo individual de uma pessoa**. Se for possível → **não liberar**. Se for **impossível** → segue para gate.

**Critérios de sucesso:**
1. Auditoria automatizada passa sem achados críticos.
2. RIPD, LIA e ROPA revisados e aprovados.
3. Aviso de monitoramento afixado e Encarregado (DPO) definido/publicado.
4. Plano de resposta a incidente aprovado.
5. **Parecer jurídico-técnico favorável** e **gate de liberação assinado** para streams reais com hóspedes.

---

## 4. Organização do Repositório e Documentação

| Local | Finalidade |
|---|---|
| **`.planning/`** | Fonte única da verdade (GSD): `ROADMAP.md`, `REQUIREMENTS.md`, `PROJECT.md`, `STATE.md`, fases, pesquisas e histórico. |
| **`.planning/context/`** | Manuais de engenharia, arquitetura, modelagem de banco, parecer LGPD/Marco Civil, diretrizes e `PLANO_V1_COMPLETO.md`. |
| **`.planning/phases/`** | Snapshots por fase com `PLAN`, `SUMMARY`, `CONTEXT`, `RESEARCH`, `VALIDATION`, `VERIFICATION`. |
| **`main.py`, `captura.py`, `rastreio.py`, `zona.py`, `overlay.py`** | Pipeline de produção. |
| **`config/zonas.yaml`** | Configuração de ROIs por câmera. |
| **`tests/`** | Suíte automatizada (33 testes). Inclui `test_privacidade.py` como guarda de privacidade. |
| **`scripts/`** | Ferramentas de desenvolvimento (demarcação de ROI, treino/validação, gerador de relatório). **Fora do pipeline de produção.** |
| **`docs/`** | Documentação adicional e relatórios para gestão/conformidade. |

---

## 5. Referências Cruzadas

| Documento | Aplicação |
|---|---|
| [`.planning/ROADMAP.md`](.planning/ROADMAP.md) | Cronograma, fases, progresso e rastreabilidade. |
| [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md) | Requisitos v1 (27), status e traceability. |
| [`.planning/PROJECT.md`](.planning/PROJECT.md) | Visão, escopo, decisões-chave e evolução. |
| [`.planning/STATE.md`](.planning/STATE.md) | Estado atual, foco e progresso. |
| [`.planning/context/MODELAGEM_BANCO_DE_DADOS.md`](.planning/context/MODELAGEM_BANCO_DE_DADOS.md) | Schema permitido x vetado (`sessoes`/`session_traces` proibidas). |
| [`.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md`](.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md) | Análise jurídico-técnica e pendências da Fase 9. |
| [`.planning/context/PERGUNTAS_FREQUENTES_TECNICAS.md`](.planning/context/PERGUNTAS_FREQUENTES_TECNICAS.md) | Dwell, ByteTrack, cálculo de ocupação e mudança de polígono. |
| [`.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md`](.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md) | Verificação normativa artigo por artigo. |
| [`.planning/context/DIRETRIZES_PARA_AGENTE_IA.md`](.planning/context/DIRETRIZES_PARA_AGENTE_IA.md) | Regras obrigatórias para desenvolvimento. |

---

## 6. Glossário de Siglas

| Sigla | Significado | Observação |
|---|---|---|
| **ANPD** | Autoridade Nacional de Proteção de Dados | Órgão fiscalizador da LGPD. |
| **API** | Application Programming Interface | Interface para consulta das métricas agregadas (FastAPI). |
| **CNT** | Contagem & Ocupação | Requisitos relacionados à detecção, rastreamento efêmero e ocupação por zona/ROI. |
| **DPO** | Data Protection Officer (Encarregado) | Responsável pelo canal de atendimento de titulares e pela interface com a ANPD. |
| **DSH** | Dashboard | Requisitos relacionados à interface web operacional. |
| **DWL** | Dwell | Referente a tempo de permanência (*dwell time*). |
| **FPS** | Frames Per Second | Quadros por segundo. |
| **GSD** | Get Shit Done | Metodologia/fluxo utilizado para planejamento e execução das fases. |
| **ING** | Ingestão | Captura de vídeo (webcam, arquivo, RTSP). |
| **LIA** | Legitimate Interest Assessment | Avaliação de Interesse Legítimo exigida no art. 10 §3º da LGPD. |
| **LGPD** | Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018) | Lei aplicável ao tratamento de dados pessoais no Brasil. |
| **MTMCT** | Multi-Target Multi-Camera Tracking | Rastreamento entre câmeras. **Proibido** neste projeto. |
| **OPS** | Operação | Requisitos relacionados à robustez, multi-câmera, reconexão, watchdog e ambiente. |
| **PRV** | Privacidade | Itens relacionados a conformidade com LGPD/Marco Civil. |
| **QUA** | Qualidade | Testes, acurácia, latência e resiliência. |
| **RAM** | Random Access Memory | Memória volátil. Frames e trilhas efêmeras vivem apenas aqui. |
| **Re-ID** | Re-Identification / Re-identificação | Tentativa de associar pessoas entre frames/câmeras por aparência. **Proibido** neste projeto. |
| **RIPD** | Relatório de Impacto à Proteção de Dados | Exigido quando o tratamento pode gerar riscos elevados aos titulares. |
| **ROI** | Region of Interest (Região de Interesse) | Polígono delimitado no frame para contagem/ocupação. |
| **ROPA** | Registro das Operações de Tratamento de Dados Pessoais | Registro exigido pelo art. 37 da LGPD. |
| **RTSP** | Real Time Streaming Protocol | Protocolo para ingestão de câmeras IP. |
| **SQL** | Structured Query Language | Linguagem utilizada pelo PostgreSQL. |
| **TTL** | Time To Live | Política de expiração/retenção de métricas e logs. |
| **UUID** | Universally Unique Identifier | Identificador único utilizado para idempotência de lotes (`batch_id`). |
| **YOLO** | You Only Look Once | Modelo de detecção utilizado (YOLO CrowdHuman). |

---

**Documento gerado na branch `docs/refatoracao-organizacao-documentacao`.** Fiel ao escopo vigente: **ROI-only, saída exclusivamente agregada, zero associação entre câmeras, frames voláteis, sem face/biometria, sem dados por-pessoa.**
