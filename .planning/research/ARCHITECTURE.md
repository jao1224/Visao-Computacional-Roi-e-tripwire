# Pesquisa de Arquitetura (Architecture Research)

**Domínio:** Analytics de vídeo em tempo real / contagem de pessoas (fluxo de pessoas em hotelaria)
**Pesquisado em:** 2026-10-08
**Confiança:** ALTA (formato do pipeline, threading, lógica de zonas) / MÉDIA (práticas de produção MTMCT, ordem de construção)

> **⚠️ DOCUMENTO DE PESQUISA — DATADO (2026-10-08) E PARCIALMENTE SUPERADO.**
> Preservado como **registro de referência técnica**, não como plano. Índice, mapa de validade e equivalências da numeração antiga: [`README.md`](README.md) (nesta pasta).
> - **Roadmap canônico:** [`../ROADMAP.md`](../ROADMAP.md) — **9 fases**. O roadmap de fases sugerido neste documento é de **6** e **não** é o plano.
> - **Vetos definitivos (mantidos):** MTMCT, Re-ID, `session_traces`/`sessoes`, embeddings de aparência e qualquer persistência de `track_id`/`session_id` estão **fora do escopo para sempre** (LGPD art. 12 §2º). Ignore as seções/patterns/fases que os mencionem. Permitido: associação efêmera em RAM + métricas agregadas.
> - **Escopo e requisitos:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · **estado:** [`../STATE.md`](../STATE.md).

---

## Arquitetura Padrão

### Visão Geral do Sistema

A análise de projetos industriais e acadêmicos de contagem de pessoas e analytics de vídeo converge para um padrão estrutural em camadas. O achado fundamental é a separação estrita de **dois loops que jamais devem se tocar**:

```
┌────────────────────────── HOT LOOP (Somente RAM, ≤5 ms/frame) ──────────────────────────┐
│                                                                                        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐     │
│  │  INGESTÃO    │   │  MOTOR       │   │  ANALYTICS   │   │  ASSOCIACÃO EFÊMERA  │     │
│  │  (RTSP /     │──▶│  DE IA       │──▶│  DE ZONA     │──▶│  (ByteTrack em RAM)  │     │
│  │   Webcam)    │   │ (YOLO Cuerpo)│   │  (ROI/Área)  │   │                      │     │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                                                           │
                                                        Fila em Memória    │ (Batch Writer)
                                                                           ▼
┌────────────────────────── COLD LOOP (Assíncrono, I/O de Banco) ────────────────────────┐
│                                                                                        │
│  ┌──────────────────────┐                       ┌──────────────────────────────────┐   │
│  │  POSTGRESQL          │◄──────────────────────│  API FASTAPI & DASHBOARD         │   │
│  │  (Métricas Agregadas)│                       │  (Somente Leitura)               │   │
│  └──────────────────────┘                       └──────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Princípios Arquiteturais Chave
1. **Isolamento de I/O:** O hot loop (processamento de vídeo) roda com máxima velocidade em CPU/GPU sem bloqueios de disco ou banco de dados.
2. **Volatilidade de Dados:** Frames e IDs individuais existem apenas na memória RAM por frações de segundo.
3. **Agregação Estrita:** Apenas dados estatísticos agregados por janela temporal e zona alimentam o banco de dados.
