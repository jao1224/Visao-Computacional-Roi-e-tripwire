# Verificação Legal — LGPD e Marco Civil da Internet

**Data:** 2026-10-08 (pedido explícito do usuário: "verifique toda a lei do Marco Civil e LGPD antes de começar a fazer a aplicação")
**Fontes primárias:** Lei 13.709/2018 (LGPD, planalto), Lei 12.965/2014 (Marco Civil, planalto/CGI.br), parecer interno doc 07, orientações ANPD (guia de definições de agentes e encarregado, Res. CD/ANPD nº 18/2024).
**Status:** sistema VERIFICADO COM CONDIÇÕES — as condições abaixo são requisitos vinculantes do escopo.

---

## 1. Enquadramento do sistema

| Pergunta | Resposta |
|---|---|
| O hotel é **controlador** (art. 5º VI, art. 42)? | Sim — decide finalidade e meios do monitoramento |
| O sistema é **operador** ou controlador próprio? | Operador em nome do hotel (art. 5º VII) — se vendido como produto, a empresa cliente é controlador |
| A saída do sistema é dado pessoal? | **Não**, se (e somente se) as condições da §2 forem cumpridas: é dado **anonimizado irversível** (art. 5º XI, art. 12 caput) — contagens/ocupação/dwell/heatmap agregados, sem qualquer vetor de identificação |
| Risco de deixar de ser anônimo? | **Sim, art. 12 §2º**: dados usados para **perfil comportamental** de pessoa identificável são pessoais mesmo que "anônimos". Por isso o veto total a rastreio |
| Somos provedor de conexão? | Não |
| Somos provedor de aplicação (MCI art. 15)? | Sim, se a API/dashboard for acessível via internet — daí a regra de logs de 6 meses |

---

## 2. LGPD (Lei 13.709/2018) — artigo por artigo

### Art. 5º — Definições
- **I/II (dado pessoal):** qualquer dado vinculado a pessoa natural identificada/identificável. Imagem de pessoa em vídeo é dado pessoal; bounding box + posição histórica **também** é, se puder reconstruir a rotina.
- **VI (dado sensível):** biometria. → **Face = sensível, art. 11** → por isso face está eliminada do projeto (base legal inviável para analytics: não há consentimento específico nem proteção da vida numa contagem).
- **XI (anonimizado):** não se aplica LGPD **desde que** o processo de anonimização seja **irreversível** (requisito do art. 12 caput, com método consignado no registro).
- **XVII (RIPD):** documentação de riscos e salvaguardas — vira requisito PRV-04.

### Art. 6º — Princípios (todos vinculantes)
| Princípio | Exigência concreta no sistema |
|---|---|
| I Finalidade | Analytics de fluxo do hotel; vedado qualquer desvio para vigilância individual ou RH |
| II Adequação | Nenhum dado coletado que não sirva à métrica exibida |
| **III Necessidade/Minimização** | Associação de trilhas só em RAM, só o tempo de evitar dupla contagem; frames descartados após inferência; banco guarda só agregados |
| IV Transparência | Aviso físico nas áreas monitoradas (finalidade do tratamento) |
| V Segurança | Controle de acesso à API/banco, TLS, backups |
| VI Não discriminação | Nunca usar contagem/dwell para tratar pessoa (não temos identidade — garantido por arquitetura) |
| VII Prevenção | Este documento + auditoria de código por PRV-01 |
| VIII Responsabilização | Registro de operações + RIPD + encarregado |

### Art. 7º — Bases legais aplicáveis (para a fase em que pixels passam pela RAM)
- **VII — proteção da vida/incolumidade** (monitoramento de segurança do hotel) — aplicável a câmeras de segurança.
- **IX — interesse legítimo do controlador** (operação do hotel: ocupação, fluxo) — exige **LIA** (art. 10 §3º: a ANPD pode exigir o relatório de impacto quando a base é interesse legítimo).
- I (consentimento): impraticável em monitoramento contínuo (não é livre, pode ser viciado) — **não usar**.
- **Conclusão:** registrar LIA (Legitimate Interest Assessment) + RIPD (art. 38) como condição de produção.

### Art. 11 — Dados sensíveis
- Só consentimento específico/distinto ou as hipóteses do §1º/§2º. **Nenhum cenário de analytics se enquadra** → manter veto total a face, biometria, demografia por rosto, emoção.

### **Art. 12 — Anonimização (o artigo central deste projeto)**
- **Caput:** dados anônimos ficam fora da LGPD **se** a anonimização for irreversível.
- **§2º:** ainda assim são **dados pessoais** os usados para **formação de perfil comportamental** de pessoa identificável (mesmo sem nome/CPF, mesmo com vetor "de comportamento").
- **Consequência normativa (escopo):**
  - **PROIBIDO para sempre:** MTMCT, Re-ID, associação entre câmeras (nem por silhueta/aparência — ordem explícita do usuário), `session_traces`, `sessoes`, rotas, jornadas, IDs persistidos, embeddings, histórico de posição por indivíduo, heatmap por indivíduo.
  - **PERMITIDO:** trilhas **intra-câmera, em RAM, de segundos** (ByteTrack), necessárias à não-dupla-contagem (art. 6º III), destruídas com o frame; saída exclusivamente agregada.
  - **Heatmap:** somente **densidade agregada** (matriz de células × janela de tempo), alimentada por posições efêmeras, **sem** qualquer vetor de identidade ou histórico por-pessoa persistido.

### Art. 16 — Eliminação
- Fim do tratamento → eliminação dos dados; estabelecer TTL por tipo de métrica (API-03).

### Art. 18 — Direitos do titular
- Com saída 100% agregada não há dado pessoal a responder; ainda assim, prever canal de contato do encarregado e procedimento documentado (se algo pessoal for detectado em incidente → art. 18 aplicável).

### Art. 37 — Registro das operações (ROPA)
- **Obrigatório:** inventário das operações (frames voláteis em RAM, agregação em banco, exposição via API), finalidades, bases legais (7º VII/IX), retenções.

### Art. 38 + art. 10 §3º — Relatório de impacto (RIPD/LIA)
- ANPD **pode determinar** o RIPD; **obrigatório de fato** porque a base é interesse legítimo (art. 10 §3). Conteúdo mínimo (parágrafo único do art. 38): tipos de dados, metodologia de coleta/segurança, medidas de mitigação. → é o PRV-04.

### Art. 41 — Encarregado (DPO)
- Controlador **deve** indicar encarregado (Res. CD/ANPD nº 18/2024 + guia 19/12/2024). Identidade e contato divulgados publicamente; atende titulares e ANPD em português. → requisito de operação do hotel (cláusula de produto).

### Arts. 46–49 — Segurança e boas práticas
- Medidas técnicas: ACL na API, separação ambiente dev/prod, sem frame em disco, backups criptografados, plano de resposta a incidente.
- **Art. 48:** comunicar à ANPD e ao titular incidente com risco/dano relevante — termo no plano de resposta (OPS).

### Art. 52 — Sanções administrativas (vigência desde 01/08/2021)
| Sanção | Limite |
|---|---|
| I Advertência + prazo para correção | — |
| **II Multa simples** | **até 2% do faturamento no Brasil (excluídos tributos), teto R$ 50.000.000 por infração** |
| III Multa diária | mesmo teto total |
| IV–VII Publicização/registro da infração | dano reputacional |
| VIII–X Bloqueio, eliminação, suspensão/vedação parcial do tratamento | pode parar o sistema |
| Critérios §1º | gravidade, vantagem obtida, reincidência, cooperação, adoção de medidas, valor dos danos |

→ Confirma o doc 07: risco real de até **2% / R$ 50 mi por infração** — o risco se concentra em **rastrear pessoas** (art. 12 §2º) e em **guardar imagem de hóspede**.

---

## 3. Marco Civil da Internet (Lei 12.965/2014) — artigo por artigo

| Artigo | Regra | Aplicação ao sistema |
|---|---|---|
| Art. 2º II / art. 7º II | Privacidade como princípio/direito | Orienta tudo; veda desvio de finalidade das câmeras |
| Art. 10 | Guarda de registros deve preservar intimidade/vida privada; tratamento de dados pessoais conforme a LGPD | Logs mínimos, sem conteúdo |
| **Art. 13** | Registros de **conexão** guardados **1 ano**, sob sigilo, por provedor de conexão | **Não se aplica** — não somos provedor de conexão |
| Art. 14 | Vedado a provedor de conexão guardar registros de acesso a aplicações | **Não se aplica** |
| **Art. 15** | Provedor de **aplicação** guarda **registros de acesso à aplicação por 6 meses**, sob sigilo, em ambiente controlado e seguro | **Aplica-se** se API/dashboard forem acessíveis via internet: reter por 6 meses (e não mais) log de acesso = data/hora, IP, usuário, ação — **sem dados de pessoas**. Prazo maior só com requisição (polícia/MP) + autorização judicial nos 60 dias (art. 15 §2º) |
| Art. 15 §§ | Requisição cautelar por autoridade + autorização judicial | Procedimento documentado no runbook |
| Art. 22 | Disponibilização de registros por ordem judicial ou a parte com indícios de ilícito | Nunca disponibilizar dados agregados como se fossem "trilha de pessoa" — e não temos trilha para entregar |
| Art. 11, III | Vedações de coleta/armazenamento de dados de conexão fora do necessário | Log de acesso = mínimo; sem cookies de rastreamento de hóspede |

**Aderência ao doc 07:** o doc 07 já registra "logs de acesso 6 meses sob sigilo (Marco Civil Art. 15)" — **confirmado como correto** nesta verificação.

---

## 4. Condições vinculantes extraídas da verificação (viram requisitos)

1. **Veto absoluto** a qualquer forma de rastreio/identificação: entre câmeras, por silhueta/aparência, entre dias, por embedding, por ID persistido (LGPD art. 12 §2º + ordem do usuário).
2. **Associação intra-câmera efêmera** é permitida **somente** em RAM, por segundos, nunca persistida (art. 6º III).
3. **Saída exclusivamente agregada** (contagem, ocupação, dwell, heatmap de densidade) — irreversível por construção (art. 12 caput).
4. **Frames/imagens nunca em disco**, nem em logs, backups ou erros (art. 6º II/III; evita art. 11).
5. **RIPD + LIA** (interesse legítimo) produzidos antes de produção (arts. 10 §3, 38, 5º XVII).
6. **Registro de operações** (art. 37) e **encarregado indicado e publicado** (art. 41 + Res. 18/2024).
7. **Logs de acesso à API/dashboard: 6 meses, sigilo, mínimo** (MCI art. 15) — se expostos à internet.
8. **Aviso de monitoramento** nas áreas (transparência, art. 6º IV).
9. **TTL por métrica** documentado e aplicado (art. 16).
10. **Plano de resposta a incidente** com comunicação à ANPD (art. 48).
11. **Auditoria de código automatizada** garantindo 1–4 (PRV-01) — proibição de gravar track_id/session_id/trilha/rota/embedding.

## 5. Itens do escopo anterior que a verição REPROVOU

| Item | Motivo | Base |
|---|---|---|
| MTMCT / Re-ID / associação entre câmeras (mesmo anônima, mesmo por silhueta) | Perfil de comportamento identificável | Art. 12 §2º |
| `session_traces`, `sessoes`, rotas, jornadas | Persistência de trilha individual | Art. 12 §2º, art. 6º II |
| Embeddings de aparência / vetores de silhueta reutilizáveis | Reidentificação; vetor revoga anonimato | Art. 12 caput |
| Heatmap por indivíduo (traço de uma pessoa) | Mesmo que sem ID — é reconstrução de rotina | Art. 12 §2º |
| Face/biometria/demografia | Dado sensível sem base legal para analytics | Art. 11 |
| Gravação de vídeo/frames | PII massiva, desnecessário à finalidade | Art. 6º III; doc 07 |
