# 03. MAPEAMENTO DE CÂMERAS, PLANTAS E ZONAS DE INTERESSE (ROIs)

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

---

## 3. Zonas de Interesse (ROIs) e Linhas Virtuais
- **Linhas de Cruzamento (Tripwires):** Linhas virtuais desenhadas sobre os frames para incrementar contadores (`entradas` e `saidas`) no momento em que o centroide do rastreio cruza a linha.
- **Polígonos de Área (ROIs):** Áreas delimitadas por coordenadas $(x, y)$ onde o tempo de permanência (`dwell_time`) é contabilizado enquanto o indivíduo estiver contido no polígono.
