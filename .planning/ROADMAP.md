# Roadmap: Visão Computacional para Hotelaria (Analytics de Fluxo)

## Overview

O sistema nasce do detector existente (`main.py`, YOLO CrowdHuman) e evolui em 9 fases verticais: primeiro uma fatia single-câmera que prova que a **contagem está correta** (captura → detecção → ByteTrack efêmero → tripwire/ocupação), depois a camada de produto (PostgreSQL com fila em lote → FastAPI → dashboard), em seguida a escala (multi-câmera RTSP com reconexão), a profundidade de analytics (dwell + heatmap de densidade agregado) e, por fim, validação de qualidade e a auditoria formal de LGPD (RIPD/LIA/ROPA, encarregado, plano de incidente) como gate antes de produção. Invariante em todas as fases: **saída exclusivamente agregada — zero tracking entre câmeras, zero frames em disco, zero dado por-pessoa** (LGPD art. 12 §2º). Invariante adicional: **nenhum stream real com hóspedes é ligado antes do gate da Fase 9** — fases 1–8 rodam exclusivamente com webcam, vídeos-amostra e MediaMTX local (sem titulares reais de hotel em tratamento).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): planned milestone work
- Decimal phases (2.1, 2.2): urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Fatia vertical single-câmera (captura, detecção, rastreio efêmero)** - Webcam/vídeo-amostra → YOLO corpo → ByteTrack em RAM com overlay, sem nada em disco
- [ ] **Phase 2: Contagem por zona e ocupação em tempo real** - Tripwire bidirecional sem dupla contagem e ocupação instantânea por zona (overlay)
- [ ] **Phase 3: Persistência PostgreSQL (fila + escrita em lote)** - Schema só com configuração e métricas agregadas; I/O de banco fora do loop de vídeo
- [ ] **Phase 4: API FastAPI de métricas e conformidade Marco Civil** - Endpoints somente-leitura, TTL de retenção e logs de acesso de 6 meses
- [ ] **Phase 5: Dashboard web de ocupação e séries** - Ocupação ao vivo (WebSocket), séries com filtro de período e ambiente reproduzível (docker-compose)
- [ ] **Phase 6: Multi-câmera e ingestão RTSP** - Múltiplos streams simultâneos com reconexão, watchdog e reconexão sem corromper contagens
- [ ] **Phase 7: Analytics de permanência e heatmap agregado** - Dwell por zona (ROI) e heatmap de densidade agregado exibidos no dashboard
- [ ] **Phase 8: Validação de qualidade e testes automatizados** - Suíte de testes das regras críticas e acurácia contra marcação manual em pico
- [ ] **Phase 9: Conformidade LGPD e preparação para produção** - Auditoria de código, RIPD/LIA/ROPA, aviso/encarregado e plano de resposta a incidente

## Phase Details

### Phase 1: Fatia vertical single-câmera (captura, detecção, rastreio efêmero)

**Goal**: Usuário tem o pipeline mínimo de visão funcionando em 1 câmera (webcam ou vídeo-amostra) — detecção de corpo + rastreio efêmero em RAM — com a base de privacidade (nada em disco) estabelecida desde o início
**Depends on**: Nothing (first phase)
**Requirements**: ING-01, ING-03, CNT-01, CNT-03
**Success Criteria** (what must be TRUE):
  1. Usuário processa webcam e arquivos de vídeo-amostra e vê caixas de corpo em tempo real na tela (overlay), sem qualquer detecção de face
  2. Rodar o pipeline não cria nenhum arquivo de imagem/frame/crop em disco (verificável por inspeção de diretórios antes/depois)
  3. IDs de rastreamento existem apenas enquanto a pessoa está no quadro — nada de ID, trilha ou log por-pessoa é gravado em arquivo ou banco
  4. Nenhum módulo ou dependência de face/biometria/demografia existe no código (busca no repositório vem vazia)

**Plans:** 4 plans
Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Fundação: requirements + captura.py (fonte + capture_ts) + overlay.py + harness pytest
- [ ] 01-02-PLAN.md — Rastreio efêmero: rastreio.py (YOLO + ByteTrack explícito, só corpo, guard boxes.id)

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 01-03-PLAN.md — Integração: main.py como ponto de entrada único (webcam/arquivo por CLI)

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 01-04-PLAN.md — Auditoria automatizada de privacidade (nada em disco, sem face) + verificação visual

### Phase 2: Contagem por zona e ocupação em tempo real

**Goal**: Usuário obtém contagem bidirecional e ocupação instantânea corretas por zona — a incerteza real do projeto ("a contagem está certa?") respondida visualmente, antes de qualquer banco ou dashboard
**Depends on**: Phase 1
**Requirements**: CNT-02, CNT-04
**Success Criteria** (what must be TRUE):
  1. Usuário vê pessoas entrando/saindo pela tripwire e o contador por zona incrementa/descrementa corretamente, sem contar a mesma pessoa duas vezes (inclusive sob jitter/occlusão leve)
  2. Ocupação instantânea por zona é recalculada em tempo real e exibida no overlay durante a execução
  3. Reiniciar a fonte de vídeo (parar/retomar) não corrompe a ocupação: valores reconciliados, com reset/clamp de dia aplicado
  4. Sob rajada de detecções (flicker de caixa), não há explosão de eventos ENTROU/SAIU — contagem é estável

**Plans**: TBD

### Phase 3: Persistência PostgreSQL (fila + escrita em lote)

**Goal**: Eventos agregados ganham verdade durável no PostgreSQL sem nunca tocar o loop de vídeo — fila em memória + batch writer idempotente, schema apenas de configuração e métricas agregadas
**Depends on**: Phase 2
**Requirements**: API-01, QUA-01
**Success Criteria** (what must be TRUE):
  1. Eventos de contagem chegam ao PostgreSQL via fila em lote (size-or-time), e nenhuma operação de banco acontece dentro do loop de vídeo (verificável por código/review e métrica de FPS)
  2. O banco contém apenas tabelas de configuração (câmeras, zonas) e métricas agregadas — nenhuma tabela ou coluna por-pessoa (sessões, traces, rotas) existe no schema; eventos ENTROU/SAIU são gravados **sem qualquer chave de pessoa** (sem track_id — só zona, direção e timestamp de janela)
  3. Latência do loop permanece ≤ 5 ms/frame em GPU mesmo com o escritor ativo
  4. Reentregar um lote após interrupção não duplica contagens (idempotência via evento UUID)

**Plans**: TBD

### Phase 4: API FastAPI de métricas e conformidade Marco Civil

**Goal**: Consumidores (dashboard, futuros integrantes) consultam métricas somente-leitura via API, com retenção documentada e logs de acesso conforme o Marco Civil
**Depends on**: Phase 3
**Requirements**: API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. Cliente consulta endpoints somente-leitura de contagem, ocupação, séries temporais, histogramas e heatmap agregado e recebe JSON válido
  2. TTL de retenção está documentado por tipo de métrica e aplicado de fato (registro antigo some após o prazo)
  3. Cada acesso à API gera log com IP/data/hora/ação (mínimo funcional) e logs são retidos exatamente 6 meses, sob sigilo
  4. Nenhum endpoint da API expõe dado por-pessoa (auditando rotas e respostas)

**Plans**: TBD

### Phase 5: Dashboard web de ocupação e séries

**Goal**: Gestão do hotel vê ocupação ao vivo e tendências no navegador, com ambiente reproduzível de ponta a ponta
**Depends on**: Phase 4
**Requirements**: DSH-01, DSH-02, OPS-02
**Success Criteria** (what must be TRUE):
  1. Usuário abre o dashboard e vê a ocupação instantânea por zona atualizando em tempo real via WebSocket (sem refresh)
  2. Usuário filtra séries temporais de contagem/ocupação por período e vê o gráfico responder
  3. Novo ambiente sobe com um comando (docker-compose: PostgreSQL + API + dashboard) e o sistema funciona de ponta a ponta
  4. Dashboard indica frescor/health da métrica (o usuário nunca confere dado velho como se fosse ao vivo)

**Plans**: TBD
**UI hint**: yes

### Phase 6: Multi-câmera e ingestão RTSP

**Goal**: Sistema processa múltiplos streams simultâneos com a robustez de produção (reconexão, watchdog) sem corromper contagens — exercitado via MediaMTX/amostras antes de os DVRs reais chegarem
**Depends on**: Phase 5
**Requirements**: ING-02, OPS-01
**Success Criteria** (what must be TRUE):
  1. Sistema processa múltiplas câmeras RTSP simultaneamente (fonte local MediaMTX/vídeos-amostra) com tracker por câmera
  2. Derrubar um stream e reconectá-lo (teste de cable-pull) não corrompe contagens: sessões fechadas, ocupação reconciliada, tracker resetado
  3. Stream que trava é detectado pelo watchdog (staleness) e reconectado com backoff exponencial, sem intervenção manual
  4. Com N câmeras, a latência/frescor por câmera permanece dentro do orçamento (benchmark no hardware real documentado)

**Plans**: TBD

### Phase 7: Analytics de permanência e heatmap agregado

**Goal**: Usuário enxerga quanto tempo as pessoas permanecem em cada zona e onde o fluxo se concentra — sempre como agregados, nunca como traço por pessoa
**Depends on**: Phase 6
**Requirements**: DWL-01, DWL-02, DSH-03
**Success Criteria** (what must be TRUE):
  1. Dwell time por zona é calculado em RAM com timeout de saída e fechamento de sessões zumbis; no banco persistem somente histograma/soma/n por zona×janela — nenhuma linha por pessoa
  2. Heatmap de densidade agregado (célula × janela de tempo) é gerado por câmera/zona a partir de posições efêmeras, sem qualquer histórico por-pessoa
  3. Usuário vê no dashboard o heatmap de densidade e o histograma de permanências
  4. Auditoria do schema confirma que dwell e heatmap não gravaram nenhum identificador individual

**Plans**: TBD
**UI hint**: yes

### Phase 8: Validação de qualidade e testes automatizados

**Goal**: Regras críticas do sistema cobertas por testes automatizados e acurácia da contagem medida contra marcação manual em condições de pico (webcam/amostra)
**Depends on**: Phase 7
**Requirements**: QUA-02, QUA-03
**Success Criteria** (what must be TRUE):
  1. Suíte de testes automatizados cobre tripwire, dwell+timeout, fila, ocupação e reconexão — e passa de ponta a ponta com um comando
  2. Contagem validada contra marcação manual em vídeo de pico (webcam/amostra), com relatório de acurácia (erro médio + faixa) documentado
  3. Definição escrita de "quem conta" (ex.: exclui equipe?) é aplicada na validação e registrada no relatório

**Plans**: TBD

### Phase 9: Conformidade LGPD e preparação para produção

**Goal**: Auditoria formal de LGPD aprovada e documentação de compliance (RIPD/LIA/ROPA, encarregado, plano de incidente) prontas — gate antes de qualquer implantação real
**Depends on**: Phase 8
**Requirements**: PRV-01, PRV-02, PRV-03, PRV-04, PRV-05, OPS-03
**Success Criteria** (what must be TRUE):
  1. Auditoria de código automatizada roda e passa: nada por-pessoa é gravado (busca por track_id/session_id persistido, trilha, rota, embedding), nenhum frame em disco, nenhum módulo de face/biometria
  2. RIPD + LIA (interesse legítimo, art. 10 §3) + registro de operações (art. 37) existem como documentos revisados, anteriores a produção
  3. Aviso de monitoramento está afixado nas áreas monitoradas e encarregado indicado com contato publicado (art. 41, Res. ANPD 18/2024)
  4. Plano de resposta a incidente de segurança documentado, incluindo comunicação à ANPD e titulares (art. 48)

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Fatia vertical single-câmera | 0/4 | Not started | - |
| 2. Contagem por zona e ocupação | 0/TBD | Not started | - |
| 3. Persistência PostgreSQL | 0/TBD | Not started | - |
| 4. API FastAPI + Marco Civil | 0/TBD | Not started | - |
| 5. Dashboard web | 0/TBD | Not started | - |
| 6. Multi-câmera e RTSP | 0/TBD | Not started | - |
| 7. Dwell e heatmap agregado | 0/TBD | Not started | - |
| 8. Validação de qualidade | 0/TBD | Not started | - |
| 9. Conformidade LGPD | 0/TBD | Not started | - |
