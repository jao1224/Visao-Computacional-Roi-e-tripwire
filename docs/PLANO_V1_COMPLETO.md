# Plano Completo v1 — Visão Computacional para Hotelaria (Analytics de Fluxo)

> **Documento único de referência do v1** — une requisitos, roadmap e detalhamento das 9 fases do v1.
> Data: 2026-10-08 · **Última atualização: 2026-10-21** · Status: **aprovado · Fases 1 e 2 concluídas (2/9)**
> Base legal verificada: LGPD (Lei 13.709/2018) e Marco Civil (Lei 12.965/2014) — ver `DOCUMENTACAO_PROJETO_E_LGPD/07` e verificação completa em `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md`
>
> 📌 **Estado do projeto:** ver a [seção 9 — Status de execução](#9-status-de-execução-atual-2026-10-21). A Fase 2 foi reorientada para **exclusivamente ROI/ocupação por área** (tripwire comentado no código, não removido).

---

## 1. O que é o sistema

Câmeras de segurança do hotel viram sensores de negócio: **contagem de pessoas por zona, ocupação em tempo real, tempo de permanência (dwell) e mapa de calor de fluxo** — para o hotel saber *quantas pessoas estão em cada lugar, quando e por quanto tempo ficam*, sem nunca identificar ninguém.

**Base do projeto:** o detector já existente (`main.py`, YOLO CrowdHuman, ~320 FPS em GPU) — todo o resto (tracking, zonas, banco, API, dashboard) é construído do zero conforme a documentação 01–08.

### Invariantes obrigatórios em todas as fases

| Invariante | Base legal |
|---|---|
| Saída **exclusivamente agregada** — nenhum dado por-pessoa é gravado | LGPD art. 12 §2º |
| **Zero associação entre câmeras** — nem por ID, nem por silhueta, nem por aparência | LGPD art. 12 §2º + decisão do usuário |
| **Frames de vídeo nunca tocam disco** — imagem vive só na RAM durante a inferência | LGPD art. 6º III (minimização) |
| Face, biometria, demografia **nunca** existem no código | LGPD art. 11 (dado sensível) |
| IDs de rastreamento (ByteTrack) morrem ao sair do quadro, **intra-câmera** | LGPD art. 6º III |
| **Nenhum stream real com hóspedes antes do gate da Fase 9** — fases 1–8 usam só webcam, vídeos-amostra e MediaMTX local | LGPD art. 7º IX + art. 10 §3 (LIA formal só existe ao fim da Fase 9) |

**Risco se violado:** multa de até **2% do faturamento, teto R$ 50 milhões por infração** (LGPD art. 52), além de bloqueio/eliminação de dados.

---

## 2. Requisitos v1 (27 — aprovados em 2026-10-08)

> **Legenda:** `[x]` concluído e verificado por testes · `[ ]` planejado (fase futura).
> **Fonte de verdade do status:** `.planning/REQUIREMENTS.md` (mesmos 27 requisitos, com rastreabilidade por fase).

### Ingestão (ING)
- [x] **ING-01**: Sistema processa webcam e arquivos de vídeo-amostra como fonte de vídeo (v1 = desenvolvimento)
- [ ] **ING-02**: Processa múltiplas câmeras RTSP simultaneamente, com reconexão automática (backoff exponencial) e watchdog de latência/staleness
- [x] **ING-03**: Frames são voláteis (RAM) e descartados após inferência — nenhuma imagem/frame/crop toca disco, log ou backup

### Contagem (CNT)
- [x] **CNT-01**: Detecção de pessoas apenas por corpo (YOLO CrowdHuman) — nenhum módulo de face/biometria no código
- [x] **CNT-02**: Contagem e ocupação por zona com ROI poligonal em tempo real, sem dupla contagem (ocupação por área via interseção Área(Objeto) ∩ Área(ROI) e presença)
- [x] **CNT-03**: Associação intra-câmera efêmera (ByteTrack, segundos, RAM) — IDs morrem ao sair do quadro, nunca persistidos, **nunca comparados entre câmeras (nem por silhueta/aparência)**
- [x] **CNT-04**: Ocupação instantânea por zona recalculada em tempo real (número de pessoas e % de área ocupada), com reset/clamp diário e reconciliação após reconexão

### Permanência e Fluxo (DWL)
- [ ] **DWL-01**: Dwell time por zona (ROI poligonal) com timeout de saída — cálculo em RAM; **somente histograma/soma/n por zona×janela persistido** (nunca linha por pessoa)
- [ ] **DWL-02**: Heatmap de **densidade agregado** (célula × janela de tempo) por câmera/zona — apenas contadores somados de posições efêmeras; nenhum histórico por pessoa

### Dados/API (API)
- [ ] **API-01**: PostgreSQL armazena **apenas** configuração (câmeras, zonas) e métricas agregadas — sem `session_traces`/`sessoes`/traces por pessoa
- [ ] **API-02**: FastAPI expõe métricas somente-leitura (contagem, ocupação, séries, histogramas, heatmap agregado)
- [ ] **API-03**: TTL de retenção documentado e aplicado por tipo de métrica (LGPD art. 16)
- [ ] **API-04**: Logs de acesso retidos exatamente 6 meses, sob sigilo, mínimo funcional (Marco Civil art. 15)

### Dashboard (DSH)
- [ ] **DSH-01**: Ocupação instantânea por zona em tempo real (WebSocket)
- [ ] **DSH-02**: Séries temporais de contagem/ocupação com filtro de período
- [ ] **DSH-03**: Exibição do heatmap de densidade agregado e do histograma de permanências

### Privacidade (PRV)
- [ ] **PRV-01**: Auditoria de código automatizada prova que **nada por-pessoa** é gravado (busca proibida: track_id/session_id persistido, trilha, rota, embedding, silhueta)
- [x] **PRV-02**: Nenhum frame/vídeo/crop em disco (inclui logs, backups, dumps de erro) — coberto por `tests/test_privacidade.py`
- [x] **PRV-03**: Nenhum módulo de face, biometria, demografia ou emoção — coberto por `tests/test_privacidade.py`
- [ ] **PRV-04**: RIPD + LIA (interesse legítimo, art. 10 §3) + registro de operações (art. 37) antes de produção
- [ ] **PRV-05**: Aviso de monitoramento nas áreas (art. 6º IV) + encarregado indicado com contato publicado (art. 41, Res. ANPD 18/2024)

### Qualidade (QUA)
- [ ] **QUA-01**: Latência ≤ 5 ms/frame em GPU; I/O de banco fora do loop de vídeo (fila em lote)
- [ ] **QUA-02**: Testes automatizados das regras críticas (ocupação por área/interseção, dwell+timeout, fila, reconexão)
- [ ] **QUA-03**: Contagem validada contra marcação manual em condições de pico (webcam/amostra)

### Operação (OPS)
- [ ] **OPS-01**: Falha/reconexão de câmera não corrompe contagens (sessões fechadas, ocupação reconciliada)
- [ ] **OPS-02**: Ambiente reproduzível (docker-compose: PostgreSQL + API + dashboard)
- [ ] **OPS-03**: Plano de resposta a incidente com comunicação à ANPD/titulares (LGPD art. 48)

### v2 (adiados)
Queue analytics, alertas, integração PMS/BI (só agregados), rollups/particionamento, otimização ONNX/TensorRT.

### Fora do escopo para sempre
Face/biometria/demografia/emoção (art. 11) · controle de acesso/catraca · **MTMCT/Re-ID/associação entre câmeras, inclusive por silhueta** (art. 12 §2º) · `session_traces`/`sessoes`/IDs persistidos/embeddings · rota/jornada · heatmap por indivíduo · gravação de vídeo de clientes · cross-site tracking.

---

## 3. Roadmap — 9 fases (27/27 requisitos cobertos ✓)

| # | Fase | Objetivo | Requisitos |
|---|------|----------|-----------|
| 1 | Fatia vertical single-câmera | Webcam/vídeo → YOLO corpo → ByteTrack em RAM; base de privacidade desde o início | ING-01, ING-03, CNT-01, CNT-03 |
| 2 | Contagem por zona e ocupação | Ocupação em tempo real por zona ROI (interseção de área) + clamp/reset/reconciliação | CNT-02, CNT-04 |
| 3 | Persistência PostgreSQL | Fila + escrita em lote; schema só config + agregados | API-01, QUA-01 |
| 4 | API FastAPI + Marco Civil | Somente-leitura, TTL, logs de acesso 6 meses | API-02, API-03, API-04 |
| 5 | Dashboard web | Ocupação ao vivo (WebSocket), séries, docker-compose | DSH-01, DSH-02, OPS-02 |
| 6 | Multi-câmera e RTSP | Streams simultâneos, backoff/watchdog (MediaMTX antes dos DVRs) | ING-02, OPS-01 |
| 7 | Dwell e heatmap agregado | Permanência + densidade agregada no dashboard (nunca traço por pessoa) | DWL-01, DWL-02, DSH-03 |
| 8 | Validação de qualidade | Testes automatizados + acurácia vs. marcação manual em pico | QUA-02, QUA-03 |
| 9 | Conformidade LGPD | Auditoria de código + RIPD/LIA/ROPA + aviso/encarregado + plano de incidente — **gate antes de produção** | PRV-01..05, OPS-03 |

**Execução:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 (cada fase só começa após os critérios da anterior).

**Lógica da ordem:** primeiro provar que a **contagem está certa** (1–2, maior risco técnico) → construir a **plataforma** (3–5) → **escalar** (6) → **profundizar** (7) → **validar e formalizar** (8–9).

---

## 4. Plano de fases detalhado

### Fase 1 — Fatia vertical single-câmera
**Constrói:** captura (webcam/vídeo-amostra) → YOLO CrowdHuman (já existente) → ByteTrack efêmero em RAM → overlay com caixas e IDs temporários (só debug).
**Por quê primeiro:** é o cimento de tudo; e os hábitos de privacidade (nada em disco) entram desde a primeira linha — mudar depois seria refazer metade do sistema.
**Critérios de sucesso:**
1. Webcam/vídeo processados com caixas de corpo em tempo real, **sem face**
2. Rodar não cria **nenhum arquivo** de imagem em disco (inspeção de diretórios antes/depois)
3. IDs existem só enquanto a pessoa está no quadro — nada por-pessoa gravado
4. Busca por módulos/dependências de face/biometria vem vazia

### Fase 2 — Contagem por zona e ocupação em tempo real
**Constrói:** zonas (ROIs poligonais nomeadas) configuradas em `config/zonas.yaml`, ocupação instantânea por zona no overlay (presença + interseção de área), clamp `[0, capacidade]`, reset diário e por inatividade, reconciliação ao reiniciar a fonte.
**Por quê antes da infra:** um bug de contagem/ocupação é 100× mais barato de descobrir na tela do que depois reprocessando no banco. É a lógica de maior risco do sistema.
**Escopo vigente (2026-10-21):** o **tripwire bidirecional foi desativado** — o código existe, porém **comentado** em `zona.py`, `overlay.py` e `main.py`. O foco exclusivo da fase é **ocupação por área (ROI)**; o suporte a tripwire permanece no código para reativação futura.
**Critérios de sucesso:**
1. Ocupação exibida ao vivo no overlay durante a execução, coerente com a presença real dentro do ROI
2. Interseção de área calculada a cada frame (percentual de área ocupada), estável sob flicker de caixa
3. Reiniciar a fonte não corrompe a ocupação (reset/clamp/reconciliação aplicados)
4. Sob rajada de detecções, a métrica mantém-se estável e sem dupla contagem espúria

### Fase 3 — Persistência PostgreSQL (fila + escrita em lote)
**Constrói:** fila em memória (loop publica eventos e segue), batch writer idempotente (N eventos ou T segundos, UUID por lote), schema mínimo (câmeras, zonas, `metricas_fluxo_zona` — derivado do doc 06 **sem** `sessoes`/`session_traces`), métrica de latência.
**Por quê assim:** I/O de banco dentro do loop derruba os FPS (proibido pelo doc 08) — padrão "loop quente / caminho frio" confirmado na pesquisa.
**Critérios de sucesso:**
1. Zero operação de banco no loop de vídeo (verificável por review + métrica de FPS)
2. Schema só com configuração e agregados — nenhuma tabela/coluna por-pessoa; eventos ENTROU/SAIU **sem qualquer chave de pessoa** (sem track_id — só zona, direção, timestamp de janela)
3. Latência ≤ 5 ms/frame em GPU com escritor ativo
4. Reentrega de lote não duplica contagens (idempotência UUID)

### Fase 4 — API FastAPI de métricas e conformidade Marco Civil
**Constrói:** endpoints somente-leitura (contagem, ocupação, séries, histogramas, heatmap agregado), TTL documentado+aplicado (art. 16), logs de acesso mínimo (IP/data/hora/ação) retidos **exatamente 6 meses sob sigilo** (Marco Civil art. 15), guard que impede rota/resposta com dado por-pessoa.
**Critérios de sucesso:**
1. Cliente consulta todos os endpoints e recebe JSON válido
2. TTL aplicado de fato (registro antigo some após o prazo)
3. Todo acesso gera log; logs 6 meses sob sigilo
4. Auditoria de rotas/respostas: nenhum dado por-pessoa exposto

### Fase 5 — Dashboard web de ocupação e séries
**Constrói:** ocupação ao vivo via **WebSocket** (sem refresh), séries temporais com filtro de período, indicador de frescor/health da métrica, docker-compose (PostgreSQL + API + dashboard em um comando). Stack da pesquisa: React + Vite + ECharts.
**Critérios de sucesso:**
1. Ocupação por zona atualiza em tempo real sem refresh
2. Filtro de período responde no gráfico
3. Ambiente novo sobe com um comando, ponta a ponta
4. Dashboard indica frescor do dado (nunca confere dado velho achando que é ao vivo)

### Fase 6 — Multi-câmera e ingestão RTSP
**Constrói:** ingestão RTSP multi-stream com **PyAV** (OpenCV corrompe frames RTSP após 15–35 s — consta na pesquisa), fila por câmera com drop-oldest, watchdog de staleness com backoff exponencial, **tracker estritamente por câmera** (reconexão reseta o tracker), **MediaMTX local** como servidor RTSP de teste para exercitar produção sem os DVRs reais.
**Privacidade reforçada:** trackers são por câmera; **não existe código que compare câmera 1 com câmera 2** (nem por ID, silhueta ou aparência) — art. 12 §2º.
**Critérios de sucesso:**
1. Múltiplas câmeras simultâneas com tracker por câmera
2. Cable-pull não corrompe contagens (sessões fechadas, ocupação reconciliada, tracker resetado)
3. Stream travado → watchdog reconecta sozinho com backoff
4. Com N câmeras, latência/frescor dentro do orçamento (benchmark documentado)

### Fase 7 — Analytics de permanência e heatmap agregado
**Constrói:** dwell por zona com timeout de saída e fechamento de sessões zumbis; agregação por zona×janela (**só** `n`, `soma_segundos`, `mín/máx`, histograma de faixas 0–2/2–5/5–15/15+ min); heatmap de densidade (célula × janela) somando posições efêmeras; telas no dashboard.
**Como funciona:**
```
RAM (efêmero):                         Banco (agregado):
trilha entrou 14:02:11                  zona | janela  | n | soma_seg | faixas
saio   14:10:43 → duração 8min32s  ──▶  recep|14:02-03 | 9 |  4320    | 0-2min:4 ...
(dado morre aqui — nunca é gravado)
```
Permitido: "média de permanência na recepção por horário". Impossível (por design): "quanto tempo *Aqueleindivíduo* ficou ontem" — a linha necessária jamais existe.
**Critérios de sucesso:**
1. No banco só histograma/soma/n por zona×janela — nenhuma linha por pessoa
2. Heatmap gerado só de posições efêmeras, sem histórico por-pessoa
3. Usuário vê heatmap e histograma no dashboard
4. Auditoria do schema confirma zero identificadores individuais

### Fase 8 — Validação de qualidade e testes automatizados
**Constrói:** suíte de testes (ocupação por área/interseção, dwell+timeout, fila, reconexão) com um comando; protocolo de marcação manual (ground truth) em vídeo de pico; relatório de acurácia (erro médio + faixa); definição escrita de "quem conta" (ex.: equipe conta ou não).
**Nota honesta:** acurácia em cenário de hotel real **não pode ser julgada sem os DVRs** — validação de campo fica pendente dos streams reais; a fase documenta a limitação.
**Critérios de sucesso:**
1. Suíte cobre as 5 regras críticas e passa com um comando
2. Contagem validada vs. marcação manual, com relatório documentado
3. Definição de "quem conta" escrita e aplicada

### Fase 9 — Conformidade LGPD e preparação para produção (gate)
**Constrói:**
1. **Auditoria de código automatizada** (PRV-01): falha se encontrar gravação de ID/trilha/rota/embedding, frame em disco, ou módulo de face/biometria
2. **RIPD** (art. 5º XVII, art. 38): dados coletados, metodologia de segurança, mitigações
3. **LIA** (art. 10 §3): interesse legítimo do hotel vs. privacidade, com salvaguardas
4. **ROPA** (art. 37): inventário de operações, finalidades, bases legais, retenções
5. **Aviso de monitoramento** afixado (art. 6º IV) + **encarregado** com contato publicado (art. 41, Res. ANPD 18/2024)
6. **Plano de resposta a incidente** com comunicação ANPD/titulares (art. 48)
**Por que a última:** os documentos descrevem o sistema *como construído* — mas a obrigação é inegociável: sem esta fase, não vai ao ar.
**Critérios de sucesso:**
1. Auditoria de código roda e passa (zero nada por-pessoa, zero frame em disco, zero face)
2. RIPD + LIA + ROPA revisados e **anteriores a produção**
3. Aviso afixado e encarregado publicado
4. Plano de incidente documentado

---

## 5. Como o tempo de permanência é salvo (resumo para dúvidas frequentes)

1. **RAM:** trilha entra na zona → `t_entrada` anotado em memória; sai → `duração = saída − entrada`. Trilha e timestamp morrem ali.
2. **Banco:** só o agregado por zona × janela de 1 min:

| zona | janela | n_permanências | soma_segundos | média | histograma |
|---|---|---|---|---|---|
| Recepção | 14:02–14:03 | 9 | 4 320 | 8m00s | 0–2min: 4 · 2–5min: 3 · 5–15min: 2 |

3. **Nunca gravado:** "pessoa X ficou 12 min às 14h03" — essa linha não existe em lugar nenhum (banco, log, backup).
4. **Resultado:** a linha agregada é anônima irreversível (art. 12 caput) → a LGPD não se aplica ao conteúdo persistido.

## 6. Como o ByteTrack se adequa à LGPD (resumo)

- Durante a inferência, sim, há tratamento de dado pessoal (art. 5º I) → base legal = **art. 7º VII** (proteção da vida) + **art. 7º IX** (interesse legítimo, com LIA formal na Fase 9); consentimento não é usado (não é livre em monitoramento contínuo).
- ByteTrack é autorizado pelo princípio da **necessidade (art. 6º III)**: sem ele, a mesma pessoa é contada 2–3 vezes — ele é o mínimo indispensável para a finalidade "contar certo".
- Ele toca **só** posição de caixas + número temporário (sem rosto, biometria ou silhueta persistente), vive **segundos em RAM**, e sua saída são **agregados**.
- **Teste legal simples:** se, ao a pessoa sair do quadro, não sobra *nada* gravado dela, estamos na lei. Se sobra qualquer coisa rastreável → art. 12 §2º (infração) → é exatamente o que a auditoria da Fase 9 (PRV-01) varre por grep.

---

## 7. Mapa de cobertura (27 requisitos → 9 fases)

| Fase | Requisitos |
|------|-----------|
| 1 | ING-01, ING-03, CNT-01, CNT-03 |
| 2 | CNT-02, CNT-04 |
| 3 | API-01, QUA-01 |
| 4 | API-02, API-03, API-04 |
| 5 | DSH-01, DSH-02, OPS-02 |
| 6 | ING-02, OPS-01 |
| 7 | DWL-01, DWL-02, DSH-03 |
| 8 | QUA-02, QUA-03 |
| 9 | PRV-01, PRV-02, PRV-03, PRV-04, PRV-05, OPS-03 |

**Cobertura: 27/27 — nenhum requisito órfão, nenhum duplicado.**

---

## 8. Pontos de atenção para a equipe

1. **RTSP real só na Fase 6** — enquanto não há DVRs, desenvolve-se com webcam, vídeos-amostra e MediaMTX (servidor RTSP local de teste).
2. **Validação em hotel real fica para depois** dos streams reais (Fase 8 documenta a limitação).
3. **A Fase 9 é gate:** nada vai a produção sem auditoria de código + RIPD/LIA/ROPA + aviso + encarregado + plano de incidente.
4. **Proibido para sempre** (não é "para depois"): face, MTMCT/Re-ID (inclusive por silhueta), `session_traces`/`sessoes`, embeddings, trilha individual, gravação de vídeo.
5. **Stack real (implementada hoje, 2026-10-21):** Python 3.14.4 (venv `.venv/`) · `ultralytics==8.4.121` (YOLO + ByteTrack) · `opencv-python==5.0.0.93` · `numpy==2.5.2` · `lap==0.5.13` · `pyyaml==6.0.3` · `pytest>=8.0` (dev). Ver `requirements.txt` / `requirements-dev.txt`.
6. **Stack-alvo (Fases 3–7, planejada — não implementada):** PyAV (ingestão RTSP — OpenCV corrompe frames RTSP após 15–35 s) · MediaMTX (servidor RTSP local de teste) · PostgreSQL 18 + `asyncpg` · FastAPI + WebSocket · React + Vite + ECharts · docker-compose.
7. **Relatório de conformidade para a gestão:** `docs/relatorios/RELATORIO-CONFORMIDADE-LGPD-v1.0-2026-10-21.pdf` (gerado por `scripts/gerar_relatorio_lgpd.py`, dependência opcional `reportlab` fora do `requirements.txt` do produto).

---

## 9. Status de execução (2026-10-21)

| Fase | Status | Data | Evidência |
|---|---|---|---|
| 1 — Fatia vertical single-câmera | ✅ Concluída | 2026-10-08 | 4/4 planos · `tests/test_captura.py`, `test_rastreio.py`, `test_main.py`, `test_integracao.py` |
| 2 — Contagem por zona e ocupação | ✅ Concluída | 2026-10-12 | 4/4 planos · `tests/test_zona.py` (10), `test_overlay.py` (4) |
| 3 — Persistência PostgreSQL | ⏳ Não iniciada | — | `API-01`, `QUA-01` |
| 4 — API FastAPI + Marco Civil | ⏳ Não iniciada | — | `API-02..04` |
| 5 — Dashboard web | ⏳ Não iniciada | — | `DSH-01..02`, `OPS-02` |
| 6 — Multi-câmera e RTSP | ⏳ Não iniciada | — | `ING-02`, `OPS-01` |
| 7 — Dwell e heatmap agregado | ⏳ Não iniciada | — | `DWL-01..02`, `DSH-03` |
| 8 — Validação de qualidade | ⏳ Não iniciada | — | `QUA-02..03` |
| 9 — Conformidade LGPD (gate) | ⏳ Não iniciada | — | `PRV-01..05`, `OPS-03` |

**Progresso: 2/9 fases (22%) · 6/27 requisitos concluídos.**

### Entregue até aqui
- Pipeline single-câmera com captura (webcam/arquivo), YOLO corpo + ByteTrack efêmero em RAM.
- Zonas ROI por câmera (`config/zonas.yaml`), ocupação instantânea por zona e **interseção de área** `Área(Objeto) ∩ Área(ROI)` — clamp `[0, capacidade]`, reset diário e por inatividade, reconciliação ao reabrir a fonte.
- Filtro de renderização por ROI no overlay (só desenha quem intersecta a zona) + destaque da interseção.
- Auditoria automatizada de privacidade (`tests/test_privacidade.py`) — prova ausência de face e de escrita em disco.
- **33 testes** verdes (`./.venv/bin/python -m pytest`).
- Demarcador interativo de ROI (`scripts/demarcar_zona.py`) — utilitário de desenvolvimento, fora do pipeline de produção.
- Relatório de conformidade LGPD/Marco Civil em PDF para a gestão do projeto (`docs/relatorios/`).

### Divergência conhecida e registrada
O tripwire bidirecional (previsto na versão original desta Fase 2) foi **desativado por decisão do usuário**: o código está comentado, não removido, em `zona.py`, `overlay.py` e `main.py`. O roadmap (`.planning/ROADMAP.md`) e os requisitos (`.planning/REQUIREMENTS.md`) já refletem o escopo **ROI-only**; este documento foi alinhado em 2026-10-21.

---

_Documento normativo vivo. Última atualização: 2026-10-21 — status de execução, escopo ROI-only e stack real._
