# 🧠 PACOTE DE CONTEXTO E DOCUMENTAÇÃO TÉCNICA + LGPD (PARA AGENTES DE IA)

> **⚠ AVISO DE ESCOPO — LEIA ANTES DE QUALQUER COISA (atualizado em 2026-10-08)**
> O escopo vigente deste projeto foi **redefinido pelo usuário** e **auditado contra a LGPD e o Marco Civil**. Fonte da verdade do escopo atual:
> - **[`../PLANO_V1_COMPLETO.md`](../PLANO_V1_COMPLETO.md)** — requisitos + roadmap + 9 fases (documento único para aprovação da equipe)
> - **[`09_PLANO_DE_FASES_V1.md`](09_PLANO_DE_FASES_V1.md)** — detalhamento das fases
>
> **Proibido para sempre (não é "para depois"):** face/reconhecimento facial, biometria, demografia, controle de acesso (catracas), **MTMCT/Re-ID/associação entre câmeras (inclusive por silhueta)**, `sessoes`/`session_traces`, track_id persistido, embeddings, rota/jornada, heatmap por indivíduo, gravação de vídeo de clientes.
> **Permitido:** detecção de corpo (CrowdHuman), ByteTrack **intra-câmera em RAM (segundos, nunca persistido)**, saída 100% agregada (contagem, ocupação, dwell agregado, heatmap de densidade).
> Base legal: LGPD art. 11 (sensível), art. 12 §2º (perfil comportamental), art. 6º III (minimização); verificação completa em `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md`.

> **Instrução para Agentes de IA:**
> Este diretório reúne a **documentação consolidada, a arquitetura de engenharia e o parecer regulatório (LGPD & Marco Civil)** do projeto de Visão Computacional aplicado a Hotelaria. Use os arquivos desta pasta para entender a arquitetura e as restrições legais, **mas o escopo vigente é o do aviso acima e do `PLANO_V1_COMPLETO.md`** — em caso de conflito, o escopo vigente prevalece sobre qualquer documento antigo.

---

## 🗺️ Mapa de Documentação Consolidada

| Arquivo | Conteúdo e Finalidade | Status |
| :--- | :--- | :--- |
| **[`01_VISAO_GERAL_E_NEGOCIO_HOTEL.md`](01_VISAO_GERAL_E_NEGOCIO_HOTEL.md)** | Visão de produto, dor do cliente, objetivos de negócio e requisitos funcionais. | ⚠ Partes de face/catraca superadas |
| **[`02_ARQUITETURA_TECNICA_E_ENGENHARIA.md`](02_ARQUITETURA_TECNICA_E_ENGENHARIA.md)** | Arquitetura em camadas, pipelines de vídeo RTSP, filas assíncronas e hardware. | ✅ **Vigente** (revisado em 2026-10-21 — arquitetura-alvo + implementação real) |
| **[`03_MAPEAMENTO_CAMERAS_E_PLANTAS.md`](03_MAPEAMENTO_CAMERAS_E_PLANTAS.md)** | Planta física do hotel, divisão por andares (Recepção, Lazer, Corredores) e ROIs. | ✅ **Vigente** (revisado em 2026-10-21 — tripwire desativado; ver `config/zonas.yaml`) |
| **[`04_MODELOS_IA_FACE_VS_BODY.md`](04_MODELOS_IA_FACE_VS_BODY.md)** | Comparativo dos modelos: YOLO Face vs. YOLO Body/CrowdHuman. | 🚫 **SUPERADO** — só body (histórico) |
| **[`05_RASTREAMENTO_MULTICAMERAS_MTMCT.md`](05_RASTREAMENTO_MULTICAMERAS_MTMCT.md)** | Arquitetura de rastreamento entre câmeras (Re-ID, fusão de trilhas). | 🚫 **SUPERADO — não implementar** |
| **[`06_MODELAGEM_BANCO_DE_DADOS.md`](06_MODELAGEM_BANCO_DE_DADOS.md)** | DDL PostgreSQL, MER, tabelas de zonas, câmeras, sessões e traces. | ✅ **Vigente** (revisado em 2026-10-21 — schema conforme na §2.2; `sessoes`/`session_traces` marcados como vetados) |
| **[`07_PARECER_COMPLETO_LGPD_E_MARCO_CIVIL.md`](07_PARECER_COMPLETO_LGPD_E_MARCO_CIVIL.md)** | Parecer regulatório completo: artigo por artigo, multas, TTLs e pendências da Fase 9. | ✅ **Vigente** (revisado em 2026-10-21 — ver também `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md`) |
| **[`08_PROMPT_E_DIRETRIZES_PARA_AGENTE_IA.md`](08_PROMPT_E_DIRETRIZES_PARA_AGENTE_IA.md)** | Instruções e restrições de escopo para agentes de IA. | ✅ **Vigente** (revisado em 2026-10-21 — comandos obsoletos removidos) |
| **[`09_PLANO_DE_FASES_V1.md`](09_PLANO_DE_FASES_V1.md)** | Detalhamento das 9 fases do v1 (requisitos, critérios, LGPD). | ✅ **Vigente** |

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
