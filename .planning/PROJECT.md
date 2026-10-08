# Visão Computacional para Hotelaria (Analytics de Fluxo)

## What This Is

Sistema de inteligência artificial com visão computacional que transforma câmeras de segurança convencionais do hotel em sensores de inteligência de negócios: contagem de pessoas por zona, tempo de permanência (dwell time), mapas de calor e ocupação em tempo real. Usuário final: gestão do hotel (equipes operacionais, recepção, segurança). Desenvolvimento parte do detector de corpo atual (`main.py`, YOLO CrowdHuman) e evolui conforme a documentação em `DOCUMENTACAO_PROJETO_E_LGPD/`.

## Core Value

Contagem, fluxo e permanência por zona — confiáveis e em tempo real — com **zero biometria**: usar somente detecção de corpo/silhueta, mantendo o sistema 100% conforme a LGPD.

## Requirements

### Validated

- ✓ Detecção de corpo em tempo real via webcam com YOLO CrowdHuman — existente em `main.py` (~84% precisão, ~320 FPS em GPU)

### Active

- [ ] Processar múltiplas câmeras simultaneamente (webcam/vídeo-amostra no v1 de desenvolvimento, RTSP de DVRs depois)
- [ ] Rastreamento sem duplicação (ByteTrack): a mesma pessoa não é contada duas vezes
- [ ] Contagem por zona (tripwires) com entradas/saídas em tempo real
- [ ] Tempo de permanência (dwell time) por zona (ROIs poligonais)
- [ ] Mapas de calor e séries temporais de ocupação
- [ ] Banco PostgreSQL com zonas, câmeras, sessões, traces e métricas agregadas (schema pronto no doc 06)
- [ ] Backend FastAPI expondo métricas para o dashboard
- [ ] Dashboard web com ocupação instantânea, heatmaps e tendências
- [ ] Conformidade LGPD por design: somente detecção de corpo, frames descartados após inferência, sem armazenamento de imagens de pessoas
- [ ] Logs de acesso à API retidos por 6 meses (Marco Civil Art. 15), se houver API exposta

### Out of Scope

- Detecção/reconhecimento facial — decisão do usuário: projeto abandonou face detection; todo o fluxo é por corpo
- Controle de acesso (catracas/portas com chave facial) — não teremos controle de acesso facial
- Embeddings biométricos ou snapshots de rostos — sem base legal para analytics (LGPD Art. 11)
- Identificação nominal de pessoas — apenas contagem anônima agregada
- Armazenamento de frames/vídeo bruto de clientes — frames são voláteis (RAM), descartados após inferência

## Context

- Código existente: `main.py` (aplicativo principal, inferência webcam), demais arquivos (`run_pipeline.py`, `treinar_crowdhuman.py`, `scripts/`) são apenas para teste
- Documentação obrigatória: `DOCUMENTACAO_PROJETO_E_LGPD/` (docs 01–08) — fonte primária de verdade para arquitetura, requisitos e restrições legais; notar que os docs ainda mencionam face/catraca em alguns pontos — o escopo vigente é o definido aqui
- Mapa do codebase: `.planning/codebase/` (7 documentos)
- Arquitetura-alvo (doc 02): 5 camadas — ingestão RTSP → motor YOLO+ByteTrack → sessões/filas → PostgreSQL → FastAPI/dashboard
- Desenvolvimento começa com webcam/vídeos-amostra; RTSP real vem depois (usuário não tem DVRs disponíveis agora)
- Banco: schema PostgreSQL completo já especificado no doc 06 (zonas, cameras, sessoes, session_traces, metricas_fluxo_zona)

## Constraints

- **LGPD**: somente detecção de corpo (sem biometria); frames nunca persistidos; métricas anonimizadas (Art. 6º III, Art. 12)
- **Performance**: latência ≤ 5 ms por frame em GPU; I/O de banco nunca dentro do loop de vídeo (doc 08)
- **Marco Civil**: logs de acesso à API por 6 meses sob sigilo (Art. 15)
- **Idioma**: código e mensagens em português (pt-BR), convenções atuais do repo
- **Hardware**: GPU NVIDIA para inferência (~320 FPS); desenvolvimento local pode usar CPU/webcam

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Eliminar detecção facial e controle de acesso do escopo | Decisão do usuário: só detecção de corpo; simplifica LGPD e escopo | ✓ Definitivo (2026-10-08) |
| Analytics apenas com detecção de corpo (CrowdHuman) | Conformidade total com LGPD sem risco de multa (doc 07) | ✓ Definitivo |
| Desenvolver primeiro com webcam/vídeos-amostra | Sem DVRs/RTSP disponíveis no momento | — Pending |
| Construir o sistema conforme os docs 01–08 | Documentação consolidada é fonte primária de verdade | — Pending |

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
*Last updated: 2026-10-08 after initialization*
