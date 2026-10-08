# REQUIREMENTS — Visão Computacional para Hotelaria (Analytics de Fluxo)

**Milestone:** v1 (primeiro release)
**Data:** 2026-10-08 — aprovado pelo usuário
**Base:** PROJECT.md + pesquisa (`.planning/research/`) + verificação legal (`COMPLIANCE-LGPD-MARCO-CIVIL.md`, 11 condições vinculantes)
**Regra de ouro:** saída exclusivamente agregada; qualquer dado por-pessoa é proibido (LGPD art. 12 §2º).

---

## v1 Requirements

### Ingestão (ING)
- [ ] **ING-01**: Sistema processa webcam e arquivos de vídeo-amostra como fonte de vídeo (v1 = desenvolvimento)
- [ ] **ING-02**: Processa múltiplas câmeras RTSP simultaneamente, com reconexão automática (backoff exponencial) e watchdog de latência/staleness
- [ ] **ING-03**: Frames são voláteis (RAM) e descartados após inferência — nenhuma imagem/frame/crop toca disco, log ou backup

### Contagem (CNT)
- [ ] **CNT-01**: Detecão de pessoas apenas por corpo (YOLO CrowdHuman) — nenhum módulo de face/biometria no código
- [ ] **CNT-02**: Contagem por zona com tripwire bidirecional (entra/sai), sem dupla contagem da mesma pessoa
- [ ] **CNT-03**: Associação intra-câmera efêmera (ByteTrack, segundos, RAM) — IDs morrem ao sair do quadro, nunca persistidos, **nunca comparados entre câmeras (nem por silhueta/aparência)**
- [ ] **CNT-04**: Ocupação instantânea por zona recalculada em tempo real, com reset/clamp diário e reconciliação após reconexão

### Permanência e Fluxo (DWL)
- [ ] **DWL-01**: Dwell time por zona (ROI poligonal) com timeout de saída e fechamento de sessões zumbis — cálculo em RAM; **somente histograma/soma/n por zona×janela persistido** (nunca linha por pessoa)
- [ ] **DWL-02**: Heatmap de **densidade agregado** (célula × janela de tempo) por câmera/zona — apenas contadores somados de posições efêmeras; nenhum histórico por pessoa

### Dados/API (API)
- [ ] **API-01**: PostgreSQL armazena **apenas** configuração (câmeras, zonas) e métricas agregadas (`metricas_fluxo_zona`, agregados de dwell, buckets de heatmap) — sem `session_traces`/`sessoes`/traces por pessoa
- [ ] **API-02**: FastAPI expõe métricas somente-leitura (contagem, ocupação, séries temporais, histogramas, heatmap agregado) para o dashboard
- [ ] **API-03**: TTL de retenção documentado e aplicado por tipo de métrica (LGPD art. 16)
- [ ] **API-04**: Logs de acesso à API/dashboard retidos exatamente 6 meses, sob sigilo, mínimo funcional (IP/data/hora/ação; Marco Civil art. 15) — se expostos à internet

### Dashboard (DSH)
- [ ] **DSH-01**: Ocupação instantânea por zona em tempo real (WebSocket)
- [ ] **DSH-02**: Séries temporais de contagem/ocupação com filtro de período
- [ ] **DSH-03**: Exibição do heatmap de densidade agregado e do histograma de permanências

### Privacidade (PRV)
- [ ] **PRV-01**: Auditoria de código automatizada prova que **nada por-pessoa** é gravado (busca proibida: track_id/session_id persistido, trilha, rota, jornada, embedding, silhueta/vetor de aparência, "por pessoa")
- [ ] **PRV-02**: Nenhum frame/vídeo/crop/armazenamento derivado de imagens em disco (inclui logs, backups, dumps de erro)
- [ ] **PRV-03**: Nenhum módulo de face, biometria, demografia ou emoção no código
- [ ] **PRV-04**: RIPD + LIA (interesse legítimo, art. 10 §3) + registro de operações (art. 37) produzidos antes de produção
- [ ] **PRV-05**: Aviso de monitoramento nas áreas monitoradas (art. 6º IV) + encarregado indicado e contato publicado (art. 41, Res. ANPD 18/2024)

### Qualidade (QUA)
- [ ] **QUA-01**: Latência ≤ 5 ms/frame em GPU; I/O de banco sempre fora do loop de vídeo (fila em lote/batch writer)
- [ ] **QUA-02**: Testes automatizados das regras críticas (tripwire, dwell+timeout, fila, ocupação, reconexão)
- [ ] **QUA-03**: Contagem validada contra marcação manual em condições de pico (webcam/amostra; validação em campo real depois)

### Operação (OPS)
- [ ] **OPS-01**: Falha/reconexão de câmera não corrompe contagens (sessões fechadas, ocupação reconciliada, tracker resetado)
- [ ] **OPS-02**: Ambiente reproduzível (docker-compose: PostgreSQL + API + dashboard)
- [ ] **OPS-03**: Plano de resposta a incidente de segurança com comunicação à ANPD/titulares (LGPD art. 48)

---

## v2 Requirements (adiados)
- [ ] **V2-01**: Queue analytics (fila por zona)
- [ ] **V2-02**: Alertas (ocupação acima do limite, etc.)
- [ ] **V2-03**: Integração PMS/BI via API de agregados (sem troca de PII)
- [ ] **V2-04**: Rollups/materialized views + particionamento por retenção
- [ ] **V2-05**: Otimização de inferência (ONNX/TensorRT) se necessário

## Out of Scope (exclusões explícitas)
- **Face/reconhecimento facial, biometria, demografia, emoção** — dado sensível (LGPD art. 11), sem base legal para analytics
- **MTMCT / Re-ID / associação entre câmeras, inclusive por silhueta ou aparência** — perfil comportamental (art. 12 §2º); câmera 2 nunca identifica alguém da câmera 1; proibido para sempre
- **Persistência de track_id/session_id, `session_traces`, `sessoes`, rotas, jornadas, embeddings** — trilha individual (art. 12 §2º); não implementar as tabelas do doc 06
- **Heatmap/traço por indivíduo** — reconstrução de rotina; somente densidade agregada
- **Controle de acesso (catracas/portas)** — função de controle, não analytics; fora do produto
- **Gravação/armazenamento de vídeo ou frames de clientes** — desnecessário à finalidade (art. 6º III)
- **Cross-site/tenant identity correlation** — expansão de escopo e risco de identificação

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ING-01 | Phase 1: Fatia vertical single-câmera | Pending |
| ING-03 | Phase 1: Fatia vertical single-câmera | Pending |
| CNT-01 | Phase 1: Fatia vertical single-câmera | Pending |
| CNT-03 | Phase 1: Fatia vertical single-câmera | Pending |
| CNT-02 | Phase 2: Contagem por zona e ocupação | Pending |
| CNT-04 | Phase 2: Contagem por zona e ocupação | Pending |
| API-01 | Phase 3: Persistência PostgreSQL | Pending |
| QUA-01 | Phase 3: Persistência PostgreSQL | Pending |
| API-02 | Phase 4: API FastAPI + Marco Civil | Pending |
| API-03 | Phase 4: API FastAPI + Marco Civil | Pending |
| API-04 | Phase 4: API FastAPI + Marco Civil | Pending |
| DSH-01 | Phase 5: Dashboard web | Pending |
| DSH-02 | Phase 5: Dashboard web | Pending |
| OPS-02 | Phase 5: Dashboard web | Pending |
| ING-02 | Phase 6: Multi-câmera e RTSP | Pending |
| OPS-01 | Phase 6: Multi-câmera e RTSP | Pending |
| DWL-01 | Phase 7: Dwell e heatmap agregado | Pending |
| DWL-02 | Phase 7: Dwell e heatmap agregado | Pending |
| DSH-03 | Phase 7: Dwell e heatmap agregado | Pending |
| QUA-02 | Phase 8: Validação de qualidade | Pending |
| QUA-03 | Phase 8: Validação de qualidade | Pending |
| PRV-01 | Phase 9: Conformidade LGPD | Pending |
| PRV-02 | Phase 9: Conformidade LGPD | Pending |
| PRV-03 | Phase 9: Conformidade LGPD | Pending |
| PRV-04 | Phase 9: Conformidade LGPD | Pending |
| PRV-05 | Phase 9: Conformidade LGPD | Pending |
| OPS-03 | Phase 9: Conformidade LGPD | Pending |

**Coverage:** 27/27 requisitos v1 mapeados — nenhum órfão, nenhuma duplicação ✓

_(Criado pelo roadmap em 2026-10-08 — ver `.planning/ROADMAP.md`)_
