# 07. PARECER JURÍDICO-TÉCNICO: LGPD & MARCO CIVIL DA INTERNET

> **Escopo vigente (2026-10-21).** Este parecer descreve o sistema **como construído**: analytics de fluxo por câmera, com **detecção de corpo apenas**, **sem identificação**. Toda menção a face, biometria, embeddings faciais, controle de acesso/catraca ou rastreamento entre câmeras está **fora do escopo — proibida para sempre** (LGPD art. 11 e art. 12 §2º).
>
> Documento normativo vivo. Última atualização: **2026-10-21**.
> Verificação normativa completa (artigo por artigo + 11 condições vinculantes): `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md`.
> Escopo e plano de referência: `../PLANO_V1_COMPLETO.md` e `09_PLANO_DE_FASES_V1.md`.

---

## 1. Síntese do Diagnóstico de Risco e Multas

| Operação Avaliada | Status Legal | Risco Regulatório | Multa Potencial Máxima |
| :--- | :---: | :---: | :--- |
| **Detecção de corpo em memória RAM** (`main.py`, YOLO CrowdHuman) | **CONFORME** | Quase nulo (< 5%) | Improvável |
| **Rastreio efêmero intra-câmera em RAM** (ByteTrack) | **CONFORME** | Baixo (< 10%) | R$ 0 — necessidade (art. 6º III) + base legal de interesse legítimo (art. 7º IX) |
| **Ocupação por zona ROI e interseção de área** (agregado) | **CONFORME** | Quase nulo (< 5%) | R$ 0 — saída anônima irreversível (art. 12 caput) |
| **Saída agregada (contagem, ocupação, dwell agregado, heatmap de densidade)** | **CONFORME** | Quase nulo (< 5%) | R$ 0 — não é dado pessoal |
| **Logs de acesso à API** (IP/data/hora/ação, 6 meses) | **CONFORME** | Baixo (< 15%) | R$ 0 — Marco Civil art. 15 (obrigação legal, sob sigilo) |
| ~~Detecção/identificação facial (biometria)~~ | **NÃO IMPLEMENTADO — VETADO** | — | — |
| ~~Controle de acesso / catraca~~ | **NÃO IMPLEMENTADO — VETADO** | — | — |
| ~~Associação entre câmeras (MTMCT/Re-ID)~~ | **NÃO IMPLEMENTADO — VETADO** | — | — |

**Se algum item vetado fosse implementado**, o enquadramento seria: **infração grave** — multa de até **2% do faturamento, teto de R$ 50 milhões por infração** (LGPD art. 52, §2º), além de bloqueio/eliminação dos dados e sanções da ANPD. Esse cenário não existe no código — e é verificado automaticamente por `tests/test_privacidade.py`.

---

## 2. Análise dos Artigos Críticos da LGPD (Lei nº 13.709/2018)

1. **Art. 5º, II e Art. 11 (Dados Biométricos Sensíveis):**
   - Vetores/embeddings faciais são dados sensíveis.
   - **Não existe base legal de legítimo interesse para biometria.** Para fins de analytics de fluxo em lojas/hotéis, o tratamento de rostos sem consentimento é expressamente **ilegal**.
   - **No sistema atual:** não há módulo de face, biometria, demografia ou emoção no código — a busca por esses termos no repositório vem vazia e é assegurada por teste automatizado.
2. **Art. 6º, III (Princípio da Minimização e Necessidade):**
   - Para contar quantas pessoas estão na recepção ou no restaurante, **não é necessário extrair a face nem identificar a pessoa**. A detecção de corpo (silhueta/entidade inteira) atende integralmente à finalidade sem violar a lei.
   - **Aplicação no projeto:** o Rastreio (ByteTrack) existe *apenas* para evitar dupla contagem. É o mínimo indispensável — ver a seção 4.
3. **Art. 12, §2º (Formação de Perfil Comportamental):**
   - Reconstruir a rota de um indivíduo desconhecido entre câmeras cria um perfil de hábitos, exigindo amparo legal estrito.
   - **No sistema atual:** cada câmera tem seu próprio tracker; não existe código que compare a câmera 1 com a câmera 2 (nem por ID, por silhueta ou por aparência). Nenhuma trilha individual, rota, jornada ou sessão é persistida.
4. **Art. 14 (Proteção de Crianças e Adolescentes):**
   - Câmeras em áreas de piscina e lazer capturam menores. Tratar biometria de crianças sem consentimento parental específico gera risco de autuação máxima pela ANPD.
   - **No sistema atual:** como não há biometria nem identificação, o tratamento é de contagem agregada — mas a **Fase 9 exige RIPD/LIA** que tratem explicitamente das áreas com público infantil (piscina, playground) e do aviso de monitoramento (art. 6º IV).
5. **Art. 16 (Retenção) e Art. 18 (Direitos do Titular):**
   - O sistema **não persiste dado pessoal**: não há tabela, arquivo, log ou backup com identificador de pessoa. Consequentemente, **não existe dado por-titular a ser excluído** — o direito de eliminação é atendido por construção (nada é coletado em nível individual).
   - O art. 16 aplica-se ao **TTL das métricas agregadas** (ver seção 3): retenção documentada e aplicada por tipo de métrica.
   - O art. 18 (confirmação, acesso, correção, informação, anonimização, bloqueio, eliminação, portabilidade) é atendido pelo canal do encarregado (art. 41) — os pedidos que dependam de dados agregados podem ser atendidos com os agregados.
   - ⚠️ A versão anterior deste parecer condicionava a eliminação a um `TTL de checkout` e a embeddings faciais de hóspedes. **Esse modelo foi superado**: não há checkout, não há hóspede identificado e não há dado a eliminar. Manter esse texto seria descrever um sistema inexistente.

---

## 3. Marco Civil da Internet (Lei nº 12.965/2014)

1. **Art. 15 (Guarda de Registros de Acesso a Aplicações):**
   - O backend web / FastAPI **deve guardar os logs de acesso telemático (IP, porta lógica, data e hora) por 6 (seis) meses sob sigilo** — mínimo funcional, sem conteúdo de vídeo.
2. **Distinção Essencial:**
   - O Marco Civil *obriga a retenção de logs de conexão*, mas **NÃO autoriza a retenção de imagens, vídeos ou dados biométricos** de pessoas.
   - Os logs de acesso são **telemétricos e técnicos** (IP, data/hora, ação) — não contêm imagem, voz nem identificador de hóspede.

---

## 4. Tabela de Temporalidade Técnica e Retenção de Dados (Data Retention)

| Tipo de Dado | Onde Fica Armazenado | Tempo Máximo de Guarda | Mecanismo de Expiração / Purge |
| :--- | :--- | :--- | :--- |
| **Frames brutos de câmera** | Memória RAM | **0 segundos** (volátil) | Descartado imediatamente após a inferência; nenhum `imwrite`/gravação no código. |
| **Buffer do tracker (ByteTrack)** | Memória RAM | **≤ 15 segundos** (podado após 60 frames sem sighting) | Liberado quando o objeto sai do enquadramento (`podar_track_states`). |
| **Estado de ocupação por zona** | Memória RAM | **0 segundos** (recalculado a cada frame) | Recontagem total por frame; nenhuma acumulação. |
| **Métricas de fluxo por zona** (`metricas_fluxo_zona`) | Tabela PostgreSQL | **Permanente / histórico** | Dado agregado e anônimo irreversível (art. 12 caput) — fora do alcance da LGPD. |
| **Agregados de permanência (dwell)** | Tabela PostgreSQL | **Permanente / histórico** | Somente `n`, `soma_segundos`, `mín/máx` e histograma de faixas por zona×janela — nenhuma linha por pessoa. |
| **Buckets de heatmap de densidade** | Tabela PostgreSQL | **Permanente / histórico** | Contadores de célula×janela a partir de posições efêmeras — nenhum histórico por pessoa. |
| **Logs de acesso à API/dashboard** | Servidor de logs | **Exatamente 6 meses** | Rotina mensal de arquivamento/expurgo (Marco Civil art. 15), sob sigilo. |
| ~~Snapshots de faces~~ | — | — | 🚫 **VETADO — não existe no sistema** (art. 11) |
| ~~Embeddings faciais de hóspedes~~ | — | — | 🚫 **VETADO — não existe no sistema** (art. 11 e art. 12 §2º) |

**Leitura da tabela:** a única categoria de dado com prazo de expiração próprio é a de **logs de acesso** (obrigação do Marco Civil). Todo o resto ou **não é persistido** (RAM) ou é **agregado e anonimizado de forma irreversível**. O sistema não possui — e jamais poderá possuir — armazenamento de imagem, vídeo, biometria ou identificador de pessoa.

---

## 5. Teste de conformidade em uma frase

> Se, ao a pessoa sair do quadro, **não sobra nada gravado dela** — nem imagem, nem ID, nem trilha, nem embedding — o sistema está na lei. Se sobra qualquer coisa rastreável, há infração do art. 12 §2º.

É exatamente esse teste que `tests/test_privacidade.py` executa automaticamente a cada build, e que a **Fase 9** transformará em auditoria formal (requisito PRV-01), somada ao RIPD (art. 5º XVII, art. 38), à LIA (art. 10 §3), ao ROPA (art. 37), ao aviso de monitoramento (art. 6º IV), à indicação do encarregado (art. 41) e ao plano de incidente (art. 48).

---

## 6. Pendências legais para a Fase 9 (gate de produção)

| Item | Base legal | Responsável | Status |
|---|---|---|---|
| RIPD (Relatório de Impacto à Proteção de Dados) | art. 5º XVII, art. 38 | Encarregado + TI | ⏳ Pendente (Fase 9) |
| LIA (Legitimate Interest Assessment) | art. 10 §3 | Encarregado + jurídico | ⏳ Pendente (Fase 9) |
| ROPA (registro de operações) | art. 37 | Encarregado | ⏳ Pendente (Fase 9) |
| Aviso de monitoramento afixado nas áreas | art. 6º IV | Operação do hotel | ⏳ Pendente (Fase 9) |
| Encarregado (DPO) com contato publicado | art. 41, Res. ANPD 18/2024 | Direção | ⏳ Pendente (Fase 9) |
| Plano de resposta a incidente | art. 48 | TI + Encarregado | ⏳ Pendente (Fase 9) |
| TTL documentado e aplicado por tipo de métrica | art. 16 | Backend (Fase 4) | ⏳ Pendente (Fase 4) |
| Logs de acesso retidos 6 meses sob sigilo | Marco Civil art. 15 | Backend (Fase 4) | ⏳ Pendente (Fase 4) |

**Nenhuma câmera real com hóspedes pode ser ligada antes do fechamento desta lista.**
