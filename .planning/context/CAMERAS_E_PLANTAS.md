# 03. MAPEAMENTO DE CÂMERAS, PLANTAS E ZONAS DE INTERESSE (ROIs)

> **Escopo vigente (2026-10-21):** o mapeamento abaixo é o **planejamento de cobertura** do hotel. A implementação atual opera com **uma câmera por vez** (`camera_0`) e **ROIs poligonais** — o tripwire bidirecional foi **desativado** (código comentado, não removido). Ver `../REQUIREMENTS.md`, `../ROADMAP.md` e o aviso no `README.md` desta pasta.
>
> Documento normativo vivo. Última atualização: **2026-10-21**.

---

## 1. Topologia Física das Câmeras no Hotel

A distribuição de câmeras foi planejada para cobrir os pontos nevrálgicos de circulação sem pontos cegos críticos:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PLANTA FÍSICA DO HOTEL                        │
├────────────────────────────────────────────────────────────────────────┤
│ 3º ANDAR: QUARTOS                                                      │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                  │
│ │   Quarto 301  │ │   Quarto 302  │ │   Quarto 303  │                  │
│ └───┬───────────┘ └───┬───────────┘ └───┬───────────┘                  │
│     │ Corredor 3º Andar                                                │
│     └─► [CÂMERA 8: Elevador] ───────────► [CÂMERA 9: Fim do Corredor]  │
├────────────────────────────────────────────────────────────────────────┤
│ 2º ANDAR: QUARTOS                                                      │
│     └─► [CÂMERA 6: Elevador] ───────────► [CÂMERA 7: Fim do Corredor]  │
├────────────────────────────────────────────────────────────────────────┤
│ 1º ANDAR: QUARTOS                                                      │
│     └─► [CÂMERA 4: Elevador] ───────────► [CÂMERA 5: Fim do Corredor]  │
├────────────────────────────────────────────────────────────────────────┤
│ TÉRREO: ÁREAS SOCIAIS E LAZER                                          │
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────┐ │
│ │ [CÂMERA 1: Entrada]  │ │ [CÂMERA 2: Recepção] │ │ [CÂMERA 3: Rest.]│ │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────┘ │
│ ┌───────────────────────────────────────────────┐                      │
│ │ [CÂMERA 10: Área da Piscina & Deck Externo]  │                      │
│ └───────────────────────────────────────────────┘                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tabela de Mapeamento de Câmeras para Zonas

| ID Câmera | Código Câmera | Localização Física | Zona Associada (`zone_id`) | Finalidade Principal |
| :---: | :--- | :--- | :--- | :--- |
| **Cam 1** | `CAM_ENTRADA_01` | Portaria Principal / Hall | Zona Externa / Acesso | Contagem de fluxo total de pedestres |
| **Cam 2** | `CAM_LOBBY_01` | Balcão da Recepção | Zona de Check-in | Tempo de fila e atendimento |
| **Cam 3** | `CAM_REST_01` | Salão do Restaurante | Zona de Alimentação | Ocupação de mesas e horário de pico |
| **Cam 4** | `CAM_CORR_1A` | Hall Elevador 1º Andar | Zona de Circulação 1 | Fluxo de hóspedes no 1º andar |
| **Cam 5** | `CAM_CORR_1B` | Final do Corredor 1º | Zona de Circulação 1 | Fluxo de quartos 101-120 |
| **Cam 6** | `CAM_CORR_2A` | Hall Elevador 2º Andar | Zona de Circulação 2 | Fluxo de hóspedes no 2º andar |
| **Cam 7** | `CAM_CORR_2B` | Final do Corredor 2º | Zona de Circulação 2 | Fluxo de quartos 201-220 |
| **Cam 8** | `CAM_CORR_3A` | Hall Elevador 3º Andar | Zona de Circulação 3 | Fluxo de hóspedes no 3º andar |
| **Cam 9** | `CAM_CORR_3B` | Final do Corredor 3º | Zona de Circulação 3 | Fluxo de quartos 301-320 |
| **Cam 10**| `CAM_PISCINA_01` | Área de Lazer Externa | Zona de Lazer | Horários de uso da piscina |

> ⚠️ **Estado real da implementação (2026-10-21):** a tabela acima é o **planejamento de cobertura** (10 câmeras). O código atual suporta **uma câmera por execução**, identificada por `camera_id` (`camera_0` por padrão), e lê as ROIs de `config/zonas.yaml`. A multi-câmera simultânea é a **Fase 6** do roadmap — e cada câmera terá seu **próprio tracker**, sem qualquer associação entre elas (LGPD art. 12 §2º).

---

## 3. Zonas de Interesse (ROIs) — método vigente

- **Polígonos de área (ROIs):** áreas delimitadas por coordenadas $(x, y)$ configuradas em `config/zonas.yaml`, por câmera e por zona (`id`, `tipo: roi`, `pontos`, `capacidade`).
- **Ocupação instantânea por zona:** recontagem a cada frame das pessoas cujo pé, centro ou borda cai dentro do polígono, com clamp `[0, capacidade]`.
- **Interseção de área:** `Interseção = Área(Objeto) ∩ Área(ROI)` — percentual da área do ROI efetivamente coberta pelas pessoas, exibido no overlay.
- **Tempo de permanência (`dwell_time`):** previsto para a **Fase 7**, calculado em RAM e persistido **apenas como agregado** por zona×janela (histograma/soma/n) — nunca uma linha por pessoa.
- **Linhas de cruzamento (tripwires):** ⚠️ **desativadas** — o código existe, porém comentado em `zona.py`, `overlay.py` e `main.py`. Mantido apenas para reativação futura; o escopo atual é **exclusivamente ROI/ocupação por área**.

---

## 4. Configuração prática das zonas

Exemplo real em `config/zonas.yaml` (câmera `camera_0`):

```yaml
camera_0:
  capacidade: 50
  zonas:
  - id: hall
    tipo: roi
    pontos:
    - [29, 44]
    - [611, 44]
    - [611, 429]
    - [29, 429]
```

- `capacidade` é o teto físico da área (usado no clamp da ocupação).
- `id` identifica a zona nos cards do overlay e nas métricas agregadas.
- As coordenadas são em **pixels do frame** — o demarcador interativo (`scripts/demarcar_zona.py`) grava exatamente esse formato.

> Utilitário de **desenvolvimento**, fora do pipeline de produção: grava apenas coordenadas em texto YAML, nunca imagens ou dados de pessoas.
