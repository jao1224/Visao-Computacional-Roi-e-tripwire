# Visão Computacional para Hotelaria (Analytics de Fluxo)

## What This Is

Sistema de inteligência artificial com visão computacional que transforma câmeras de segurança convencionais do hotel em sensores de inteligência de negócios: contagem de pessoas por zona, tempo de permanência (dwell time), mapas de calor e ocupação em tempo real. Usuário final: gestão do hotel (equipes operacionais, recepção, segurança). Desenvolvimento parte do detector de corpo atual (`main.py`, YOLO CrowdHuman) e evolui conforme a documentação em `DOCUMENTACAO_PROJETO_E_LGPD/`.

## Core Value

Contagem, fluxo e permanência por zona — confiáveis e em tempo real — com **zero biometria**: usar somente detecção de corpo/silhueta, mantendo o sistema 100% conforme a LGPD.

## Requirements

### Validated

- ✓ Detecção de corpo em tempo real via webcam com YOLO CrowdHuman — existente em `main.py` (~84% precisão, ~320 FPS em GPU)
- ✓ Associação efêmera de detecções em RAM (ByteTrack, segundos) — entregue na Fase 1, verificado por `tests/test_rastreio.py`
- ✓ Frames voláteis e nada gravado em disco — verificado por `tests/test_privacidade.py` (Fase 1)
- ✓ Ocupação instantânea por zona ROI e interseção de área `Área(Objeto) ∩ Área(ROI)` — entregue na Fase 2, verificado por `tests/test_zona.py` (10 testes) e `tests/test_overlay.py` (4 testes)
- ✓ Nenhum módulo de face, biometria, demografia ou emoção no código — verificado por `tests/test_privacidade.py`

### Active

- [ ] Processar múltiplas câmeras simultaneamente (webcam/vídeo-amostra no v1 de desenvolvimento, RTSP de DVRs depois)
- [ ] Tempo de permanência (dwell time) por zona (ROIs poligonais) — persistido apenas como agregado por zona×janela
- [ ] Heatmap de **densidade agregado** por zona/câmera/janela de tempo (fluxo) — posições efêmeras em RAM somam contadores por célula; nenhum histórico por pessoa
- [ ] Séries temporais de ocupação (agregadas)
- [ ] Banco PostgreSQL apenas com tabelas de configuração (câmeras, zonas) e métricas agregadas — derivar do doc 06 **sem** `session_traces`/`sessoes`/`traces`
- [ ] Backend FastAPI expondo métricas para o dashboard
- [ ] Dashboard web com ocupação instantânea e tendências
- [ ] Conformidade LGPD por design: somente detecção de corpo, frames descartados após inferência, sem armazenamento de imagens de pessoas
- [ ] Nenhum identificador individual persistido: proibido por código gravar track_id, session_id, trilha, rota, embedding ou qualquer dado por-pessoa — apenas agregados
- [ ] Logs de acesso à API retidos por 6 meses (Marco Civil Art. 15), se houver API exposta

### Out of Scope

- Detecção/reconhecimento facial — decisão do usuário: projeto abandonou face detection; todo o fluxo é por corpo
- Controle de acesso (catracas/portas com chave facial) — não teremos controle de acesso facial
- **Rastreamento de indivíduos entre câmeras (MTMCT) e Re-ID — inclusive por silhueta/aparência** — perfil comportamental (LGPD Art. 12 §2º); câmera 2 nunca pode "reconhecer" alguém da câmera 1; proibido para sempre
- **Tabelas `session_traces` e `sessoes` do doc 06** — não implementar: persistem trilha individual = perfil de trajetória (Art. 12 §2º)
- **Persistência de track_id/session_id, embeddings de aparência, rotas ou jornadas** — qualquer dado por-pessoa, inclusive "para testes"
- Embeddings biométricos ou snapshots de rostos — sem base legal para analytics (LGPD Art. 11)
- Identificação nominal de pessoas — apenas contagem anônima agregada
- Armazenamento de frames/vídeo bruto de clientes — frames são voláteis (RAM), descartados após inferência
- Heatmaps individuais (traços de movimento por pessoa) — proibidos por LGPD Art. 12 §2º; só densidade agregada (decisão do usuário: "mapa de calor para ver o fluxo")

## Context

- Código existente: `main.py` (aplicativo principal, inferência webcam/arquivo), `captura.py`, `rastreio.py`, `zona.py`, `overlay.py` (pipeline de produção) e `entender_zonas.py` (utilitário). `scripts/` contém ferramentas de desenvolvimento e documentação (download/treino/validação do detector, demarcador interativo de ROI, gerador do relatório LGPD) — **fora do pipeline de produção**.
- Documentação obrigatória: `docs/DOCUMENTACAO_PROJETO_E_LGPD/` (docs 01–09) — fonte primária de verdade para arquitetura, requisitos e restrições legais. Os documentos foram **revisados em 2026-10-21** para refletirem o escopo vigente (sem face, sem catraca, sem MTMCT, sem `session_traces`); os docs 04 e 05 permanecem como **registro histórico** de escopos superados.
- Plano mestre: `docs/PLANO_V1_COMPLETO.md` (requisitos + roadmap + 9 fases + status de execução).
- Mapa do codebase: `.planning/codebase/` (7 documentos, atualizados em 2026-10-21)
- Verificação legal completa (LGPD art. por artigo + Marco Civil): `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` — 11 condições vinculantes (ROPA, RIPD/LIA, encarregado, logs 6 meses, veto total a rastreio)
- Relatório de conformidade para a gestão do projeto: `docs/relatorios/` (PDF gerado por `scripts/gerar_relatorio_lgpd.py`)
- Arquitetura-alvo (doc 02): 5 camadas — ingestão RTSP → motor YOLO+ByteTrack → estado voláriel em RAM (sem sessões persistentes) → PostgreSQL → FastAPI/dashboard
- Desenvolvimento começa com webcam/vídeos-amostra; RTSP real vem depois (usuário não tem DVRs disponíveis agora)
- Banco: derivar do doc 06 **apenas** tabelas de configuração (cameras, zonas) e métricas agregadas (`metricas_fluxo_zona`, `dwell_agregado_zona`, `heatmap_densidade_camada`); **não implementar** `sessoes`/`session_traces`

## Constraints

- **LGPD**: somente detecção de corpo (sem biometria); frames nunca persistidos; métricas anonimizadas (Art. 6º III, Art. 12)
- **Performance**: latência ≤ 5 ms por frame em GPU; I/O de banco nunca dentro do loop de vídeo (doc 08)
- **Marco Civil**: logs de acesso à API por 6 meses sob sigilo (Art. 15)
- **Idioma**: código e mensagens em português (pt-BR), convenções atuais do repo
- **Hardware**: GPU NVIDIA para inferência (~320 FPS); desenvolvimento local pode usar CPU/webcam

## Key Decisions

| Decisão | Racional | Desfecho |
|----------|-----------|---------|
| Eliminar detecção facial e controle de acesso do escopo | Decisão do usuário: só detecção de corpo; simplifica LGPD e escopo | ✓ Definitivo (2026-10-08) |
| Eliminar MTMCT/Re-ID, session_traces e todo rastreamento persistente | LGPD Art. 12 §2º: reconstruir rotas = perfil comportamental; auditado em 2026-10-08 com base na lei + FAQ ANPD + doc 07 | ✓ Definitivo (2026-10-08) |
| Associação efêmera em RAM é permitida ( ByteTrack) | Minimização/necessidade (Art. 6º III): evita dupla contagem; nada é persistido, saída só agregada | ✓ Definitivo |
| Analytics apenas com detecção de corpo (CrowdHuman) | Conformidade total com LGPD sem risco de multa (doc 07) | ✓ Definitivo |
| Desenvolver primeiro com webcam/vídeos-amostra | Sem DVRs/RTSP disponíveis no momento | — Pendente |
| Construir o sistema conforme os docs 01–09 | Documentação consolidada é fonte primária de verdade | — Pendente |
| Desativar o tripwire bidirecional; foco exclusivo em ROI/ocupação por área | O tripwire depende de travessia de linha, frágil sob oclusão e perspectiva; a recontagem por frame + interseção de área é mais estável e auditável. Código **comentado**, não removido, para reativação | ✓ Definitivo (2026-10-21) |
| Adotar `Interseção = Área(Objeto) ∩ Área(ROI)` como métrica de ocupação | Mede ocupação efetiva da área, não apenas presença de ponto — é o insumo do heatmap agregado da Fase 7 | ✓ Definitivo (2026-10-21) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-21 — reconciliação documental com o planejamento vigente (Fases 1–2 concluídas, escopo ROI-only, interseção de área).*
