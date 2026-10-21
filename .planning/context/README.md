# Contexto do Projeto — documentação de negócio, arquitetura, banco, parecer e diretrizes

> Pasta de **contexto** do planejamento. Este material **não substitui** o plano: ele dá o
> contexto que o plano consome (negócio, hotel, plantas, schema, parecer jurídico, diretrizes
> de engenharia). O que uma fase **é** (objetivo, requisitos, critérios de sucesso) continua
> definido em um único lugar: [`../ROADMAP.md`](../ROADMAP.md).

> **⚠ AVISO DE ESCOPO — LEIA ANTES DE QUALQUER COISA (vigente desde 2026-10-08, revisto em 2026-10-21)**
> O escopo vigente deste projeto foi **redefinido pelo usuário** e **auditado contra a LGPD e o Marco Civil**. Fonte da verdade do escopo atual:
> - **[`../REQUIREMENTS.md`](../REQUIREMENTS.md)** — 27 requisitos canônicos (§Out of Scope com as exclusões definitivas)
> - **[`../ROADMAP.md`](../ROADMAP.md)** — as 9 fases canônicas
>
> **Proibido para sempre (não é "para depois"):** face/reconhecimento facial, biometria, demografia, controle de acesso (catracas), **MTMCT/Re-ID/associação entre câmeras (inclusive por silhueta)**, `sessoes`/`session_traces`, track_id persistido, embeddings, rota/jornada, heatmap por indivíduo, gravação de vídeo de clientes.
> **Permitido:** detecção de corpo (CrowdHuman), ByteTrack **intra-câmera em RAM (segundos, nunca persistido)**, saída 100% agregada (contagem, ocupação, dwell agregado, heatmap de densidade).
> Base legal: LGPD art. 11 (sensível), art. 12 §2º (perfil comportamental), art. 6º III (minimização); verificação completa em [`../research/COMPLIANCE-LGPD-MARCO-CIVIL.md`](../research/COMPLIANCE-LGPD-MARCO-CIVIL.md).

> **Instrução para Agentes de IA:**
> Use os arquivos desta pasta para entender a arquitetura e as restrições legais, **mas o escopo vigente é o do aviso acima e o do `../ROADMAP.md` + `../REQUIREMENTS.md`** — em caso de conflito, o planejamento canônico prevalece sobre qualquer documento antigo.

---

## 🗺️ Mapa do Contexto

| Arquivo | Conteúdo e Finalidade | Status |
| :--- | :--- | :--- |
| **[`NEGOCIO_E_OBJETIVOS.md`](NEGOCIO_E_OBJETIVOS.md)** | Visão de produto, dor do cliente, objetivos de negócio e requisitos funcionais. | ✅ **Vigente** |
| **[`ARQUITETURA_TECNICA_E_ENGENHARIA.md`](ARQUITETURA_TECNICA_E_ENGENHARIA.md)** | Arquitetura em camadas, pipelines de vídeo RTSP, filas assíncronas e hardware. | ✅ **Vigente** (revisado em 2026-10-21 — arquitetura-alvo + implementação real) |
| **[`CAMERAS_E_PLANTAS.md`](CAMERAS_E_PLANTAS.md)** | Planta física do hotel, divisão por andares (Recepção, Lazer, Corredores) e ROIs. | ✅ **Vigente** (revisado em 2026-10-21 — tripwire desativado; ver `config/zonas.yaml`) |
| **[`MODELAGEM_BANCO_DE_DADOS.md`](MODELAGEM_BANCO_DE_DADOS.md)** | DDL PostgreSQL, MER, tabelas de zonas, câmeras e métricas agregadas. | ✅ **Vigente** (revisado em 2026-10-21 — schema conforme na §2.2; `sessoes`/`session_traces` marcados como vetados) |
| **[`PARECER_LGPD_E_MARCO_CIVIL.md`](PARECER_LGPD_E_MARCO_CIVIL.md)** | Parecer regulatório completo: artigo por artigo, multas, TTLs e pendências da Fase 9. | ✅ **Vigente** (revisado em 2026-10-21 — ver também [`../research/COMPLIANCE-LGPD-MARCO-CIVIL.md`](../research/COMPLIANCE-LGPD-MARCO-CIVIL.md)) |
| **[`DIRETRIZES_PARA_AGENTE_IA.md`](DIRETRIZES_PARA_AGENTE_IA.md)** | Instruções e restrições de escopo para agentes de IA. | ✅ **Vigente** (revisado em 2026-10-21 — comandos obsoletos removidos) |

---

## ⚡ Resumo Executivo em 1 Minuto

1. **O que é o projeto:** sistema de IA com visão computacional para monitorar **fluxo de pessoas, tempo de permanência, mapa de calor de densidade e ocupação** em um hotel — **sem identificar ninguém**.
2. **Capacidade técnica:** YOLO CrowdHuman (~320 FPS em GPU, ~84% de precisão) detectando **corpos** em tempo real via streams RTSP ou webcam; ByteTrack efêmero (RAM) para não contar a mesma pessoa duas vezes.
3. **Decisão de privacidade (LGPD) — confirmada por auditoria:**
   - **Detecção apenas de corpo** (sem biometria facial — face está fora para sempre, LGPD art. 11);
   - **Sem rastreamento entre câmeras** (nem por silhueta/aparência — LGPD art. 12 §2º); ByteTrack é intra-câmera, vive segundos em RAM e nada é persistido;
   - **Saída 100% agregada** (contagens, ocupação, histogramas, heatmap de densidade) — anônima irreversível (art. 12 caput);
   - **Sem controle de acesso/catracas** — analytics apenas;
   - **Sem gravação de vídeo/frames** — imagens nunca tocam disco;
   - **Gate de produção:** auditoria de código + RIPD/LIA/ROPA + aviso de monitoramento + encarregado + plano de incidente (Fase 9) antes de qualquer câmera real com hóspedes.

---

## Mapa de origem (consolidação de 2026-10-21)

Este material veio de `docs/DOCUMENTACAO_PROJETO_E_LGPD/`, dissolvido em favor de **um único planejamento**
(`ROADMAP.md` + `REQUIREMENTS.md` + `STATE.md`). Nenhum conteúdo foi perdido — o que era duplicado foi
removido, o que era único foi movido para cá.

| Origem | Destino |
| :--- | :--- |
| `01_VISAO_GERAL_E_NEGOCIO_HOTEL.md` | [`NEGOCIO_E_OBJETIVOS.md`](NEGOCIO_E_OBJETIVOS.md) |
| `02_ARQUITETURA_TECNICA_E_ENGENHARIA.md` | [`ARQUITETURA_TECNICA_E_ENGENHARIA.md`](ARQUITETURA_TECNICA_E_ENGENHARIA.md) |
| `03_MAPEAMENTO_CAMERAS_E_PLANTAS.md` | [`CAMERAS_E_PLANTAS.md`](CAMERAS_E_PLANTAS.md) |
| `06_MODELAGEM_BANCO_DE_DADOS.md` | [`MODELAGEM_BANCO_DE_DADOS.md`](MODELAGEM_BANCO_DE_DADOS.md) |
| `07_PARECER_COMPLETO_LGPD_E_MARCO_CIVIL.md` | [`PARECER_LGPD_E_MARCO_CIVIL.md`](PARECER_LGPD_E_MARCO_CIVIL.md) |
| `08_PROMPT_E_DIRETRIZES_PARA_AGENTE_IA.md` | [`DIRETRIZES_PARA_AGENTE_IA.md`](DIRETRIZES_PARA_AGENTE_IA.md) |

---

## Onde ver o resultado

- **O que cada fase é e seu estado:** [`../ROADMAP.md`](../ROADMAP.md) · [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · [`../STATE.md`](../STATE.md)
- **Execução das fases (planos, resumos, validações):** [`../phases/`](../phases/)
- **Mapa do código real:** [`../codebase/`](../codebase/)
- **Código e testes:** `main.py`, `captura.py`, `rastreio.py`, `zona.py`, `overlay.py`, `tests/`
- **Relatório de conformidade para a gestão:** `docs/relatorios/`
