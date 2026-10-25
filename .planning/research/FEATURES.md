# Pesquisa de Funcionalidades (Feature Research): Analytics de Fluxo em Hotelaria (Somente Corpo, Somente Analytics)

> **⚠️ DOCUMENTO DE PESQUISA — DATADO (2026-10-08) E PARCIALMENTE SUPERADO.**
> Preservado como **registro de referência técnica**, não como plano. Índice, mapa de validade e equivalências da numeração antiga: [`README.md`](README.md) (nesta pasta).
> - **Roadmap canônico:** [`../ROADMAP.md`](../ROADMAP.md) — **9 fases**. O roadmap de fases sugerido neste documento é de **6** e **não** é o plano.
> - **Vetos definitivos (mantidos):** MTMCT, Re-ID, `session_traces`/`sessoes`, embeddings de aparência e qualquer persistência de `track_id`/`session_id` estão **fora do escopo para sempre** (LGPD art. 12 §2º). Ignore as seções/patterns/fases que os mencionem. Permitido: associação efêmera em RAM + métricas agregadas.
> - **Escopo e requisitos:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · **estado:** [`../STATE.md`](../STATE.md).
> - **Tripwire desativado:** o escopo vigente é **ROI/ocupação por área** (`Interseção = Área(Objeto) ∩ Área(ROI)`); o tripwire bidirecional ficou comentado no código, não removido.

**Domínio:** Contagem de pessoas por visão computacional e analytics de zona para hotelaria
**Pesquisado em:** 2026-10-08
**Confiança:** ALTA
**Escopo:** Apenas analytics (sem face, sem biometria, sem controle de acesso)

---

## 1. Funcionalidades Essenciais (Table Stakes)

Recursos básicos que os usuários esperam encontrar em um sistema de analytics de fluxo:

| Funcionalidade | Por que é esperada | Complexidade | Notas |
|----------------|---------------------|--------------|-------|
| **Contagem por Zona (ROI)** | Hotéis precisam saber a ocupação do lobby, restaurante, piscina, academia e lounge. | BAIXA | Uso de polígonos ROI + interseção de área em tempo real (já implementado na Fase 2). |
| **Ocupação em Tempo Real** | Monitoramento de lotação instantânea por área. | BAIXA | Contagem e percentual de capacidade ocupada exibidos no overlay e dashboard. |
| **Tempo de Permanência (Dwell Time)** | Saber quanto tempo os clientes ficam em determinadas áreas. | MÉDIA | Histograma agregado de permanência por faixa de tempo (Fase 7). |
| **Mapas de Calor (Heatmaps)** | Visualização de densidade de fluxo nas áreas monitoradas. | MÉDIA | Agregação espacial de posições efêmeras ao longo do tempo. |

---

## 2. Diferenciais (Delight)
- **Conformidade LGPD por Design:** Zero gravação de frames, zero biometria, saída 100% agregada.
- **Alta Performance:** Processamento em GPU com latência ≤ 5 ms por frame.
- **Arquitetura Desacoplada:** Processamento de vídeo isolado do banco de dados e da API.
