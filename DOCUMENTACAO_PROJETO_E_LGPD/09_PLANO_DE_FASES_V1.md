# 09 — Plano de Fases v1: Detalhamento Completo

**Data:** 2026-10-08
**Status:** aprovado pelo usuário junto com o roadmap (`.planning/ROADMAP.md`)
**Público-alvo:** leitor técnico/negócio que quer entender exatamente o que cada fase constrói, por quê, e como ela respeita a LGPD.

---

## Visão geral

O sistema transforma câmeras de segurança do hotel em sensores de negócio: conta pessoas, mostra ocupação, mede tempo de permanência e gera mapa de calor de fluxo — **sem nunca identificar ninguém**.

**Invariantes que valem em todas as 9 fases** (violá-las quebra o produto e a lei):

| Invariante | Base legal |
|---|---|
| Saída **exclusivamente agregada** — nenhum dado por-pessoa é gravado | LGPD art. 12 §2º |
| **Zero associação entre câmeras** — nem por ID, nem por silhueta, nem por aparência | LGPD art. 12 §2º + decisão do usuário |
| **Frames nunca tocam disco** — imagem vive só na RAM durante a inferência | LGPD art. 6º III |
| Face/biometria/demografia **nunca** existem no código | LGPD art. 11 |
| IDs de rastreamento (ByteTrack) morrem ao sair do quadro, **intra-câmera** | LGPD art. 6º III |
| **Nenhum stream real com hóspedes antes do gate da Fase 9** — fases 1–8 usam só webcam, vídeos-amostra e MediaMTX local (sem titulares reais de hotel em tratamento) | LGPD art. 7º IX + art. 10 §3 (LIA formal entregue na Fase 9) |

**Ordem de execução:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9. Cada fase só começa quando a anterior passou nos seus critérios de sucesso.

**Lógica da ordem:** primeiro provar que a *contagem está certa* (fases 1–2, o maior risco técnico), depois construir a *plataforma* (3–5: banco, API, dashboard), depois *escalar* (6: multi-câmera/RTSP), depois *profundizar* (7: dwell + heatmap), e só então *validar e formalizar* (8: qualidade; 9: conformidade legal como gate antes de produção).

---

## Fase 1 — Fatia vertical single-câmera (captura, detecção, rastreio efêmero)

### Objetivo
Ter o pipeline mínimo de visão funcionando numa única câmera (webcam ou arquivo de vídeo-amostra), com a base de privacidade estabelecida desde a primeira linha de código.

### Por que primeiro
É o "cimento" de tudo: se a captura e a detecção não funcionarem bem, nada depois disso importa. Também é aqui que os hábitos de privacidade (nada em disco) entram **desde o início** — mudar isso no final seria refazer metade do sistema.

### O que será construído
1. **Captura de vídeo:** leitor de webcam e de arquivos de vídeo-amostra (RTSP não ainda — fase 6)
2. **Detecção de corpo:** o YOLO treinado com CrowdHuman que já existe em `main.py` (base do projeto), desenhando caixas ao redor de pessoas
3. **Rastreio efêmero (ByteTrack):** liga as caixas de frames seguintes para o sistema entender que "a caixa 7 de agora é a mesma da caixa 7 de 0,03 s atrás"
4. **Overlay na tela:** janela de vídeo com caixas + IDs temporários visíveis (só para debug — os IDs não são gravados em lugar nenhum)

### Como funciona
```
Webcam/vídeo (30 fps)
   → frame na RAM
   → YOLO desenha caixas (pessoas)
   → ByteTrack associa caixas entre frames (IDs efêmeros, RAM)
   → descarta o frame (milissegundos depois — nada em disco)
   → repete
```
- O ID `#7` existe **apenas enquanto a pessoa está no quadro**; sai do quadro → o `#7` some para sempre
- Cada câmera tem seu próprio tracker (nunca compartilhado entre câmeras)

### Critérios de sucesso
1. Usuário processa webcam e vídeos-amostra e vê caixas de corpo em tempo real, **sem qualquer detecção de face**
2. Rodar o pipeline **não cria nenhum arquivo** de imagem/frame/crop em disco (verificado por inspeção de diretórios antes/depois)
3. IDs de rastreamento existem apenas enquanto a pessoa está no quadro — nada de ID/trilha/log por-pessoa é gravado
4. Busca por módulos/dependências de face/biometria no repositório vem **vazia**

### Requisitos
ING-01, ING-03, CNT-01, CNT-03

---

## Fase 2 — Contagem por zona e ocupação em tempo real

### Objetivo
Responder à pergunta central do projeto — *"a contagem está certa?"* — com tripwire bidirecional e ocupação instantânea, **visualmente validáveis na tela** antes de existir banco ou dashboard.

### Por que antes da infra
Um bug de tripwire é 100× mais barato de descobrir aqui (tela, sem infra) do que depois reprocessando dados no PostgreSQL. É a lógica de maior risco do sistema.

### O que será construído
1. **Zonas (ROIs):** polígonos nomeados desenhados sobre a imagem (Recepção, Restaurante, Spa…), configurados em arquivo/config no início
2. **Tripwire bidirecional:** linha virtual dentro de cada zona; o cruzamento incrementa (entrou) ou decrementa (saiu) conforme a direção
3. **Ocupação instantânea:** contador por zona = entradas − saídas, recalculado em tempo real e exibido no overlay
4. **Proteções de estabilidade:** régua de histerese (anti-flicker), reset/clamp diário, reconciliação ao reiniciar a fonte

### Como funciona
```
Zona RECEPÇÃO com tripwire vertical:

        │ tripwire (virtual)
   ─────┼────────────────────
        │   ↗ pessoa cruza para dentro → RECEPÇÃO +1
        │   ← sai para fora            → RECEPÇÃO −1

Ocupação(Recepção) = soma(entradas) − soma(saídas)  → exibida ao vivo
```
- **Sem dupla contagem:** só conta quem completou o cruzamento real; a trilha efêmera da Fase 1 garante que "a mesma pessoa" não gera 2 eventos por causa de tremor na caixa
- **Sem explosão:** rajadas de detecção (flicker) viram no máximo 1 evento
- **Sem fantasma:** reiniciar o vídeo → a ocupação é reconciliada (nunca fica "47 pessoas numa sala vazia")

### Critérios de sucesso
1. Contador incrementa/descrementa corretamente, sem contar a mesma pessoa duas vezes (mesmo sob jitter/occlusão leve)
2. Ocupação instantânea por zona é exibida no overlay durante a execução, em tempo real
3. Reiniciar a fonte de vídeo não corrompe a ocupação (reset/clamp/reconciliação aplicados)
4. Sob rajada de detecções não há explosão de eventos ENTROU/SAIU — contagem estável

### Requisitos
CNT-02, CNT-04

---

## Fase 3 — Persistência PostgreSQL (fila + escrita em lote)

### Objetivo
Dar verdade durável aos números **sem nunca tocar o loop de vídeo**: eventos fluem por uma fila em memória e um escritor em lote grava no PostgreSQL fora do caminho da inferência.

### Por que assim
Escrever no banco dentro do loop de vídeo derruba os FPS (o doc 08 proíbe I/O no loop). A separação "loop quente / caminho frio" é o padrão de todos os sistemas de contagem em produção (confirmado na pesquisa).

### O que será construído
1. **Fila em memória:** o loop publica eventos agregados (ENTROU/SAIU/ocupação) e segue — nunca espera o banco
2. **Batch writer idempotente:** worker que acumula N eventos ou T segundos e grava em lote, com UUID por lote para que reentrega não duplique
3. **Schema mínimo:** tabelas de **configuração** (câmeras, zonas) + **métricas agregadas** (`metricas_fluxo_zona`, séries) — derivado do doc 06 **sem** `sessoes`/`session_traces`
4. **Métrica de latência:** FPS/latência monitorados para provar que o banco não afeta o loop

### Como funciona
```
Loop de vídeo ──(evento agregado)──▶ fila RAM ──▶ batch writer ──▶ PostgreSQL
     │                                                             │
     └── nunca faz I/O de banco ←── evidência: FPS estável         │ (só agregados)
```

### Critérios de sucesso
1. Nenhuma operação de banco dentro do loop de vídeo (verificável por código/review e métrica de FPS)
2. O banco contém **apenas** tabelas de configuração e métricas agregadas — nenhuma tabela/coluna por-pessoa existe no schema; eventos ENTROU/SAIU gravados **sem qualquer chave de pessoa** (sem track_id — só zona, direção e timestamp de janela)
3. Latência do loop permanece ≤ 5 ms/frame em GPU mesmo com o escritor ativo
4. Reentregar um lote após interrupção não duplica contagens (idempotência via UUID)

### Requisitos
API-01, QUA-01

---

## Fase 4 — API FastAPI de métricas e conformidade Marco Civil

### Objetivo
Expor as métricas para consumo (dashboard e futuros integrantes) via API somente-leitura, com retenção documentada e logs de acesso conforme o Marco Civil.

### O que será construído
1. **Endpoints somente-leitura:** contagem atual, ocupação por zona, séries temporais, histogramas de dwell (estrutura pronta), heatmap agregado (estrutura pronta)
2. **TTL de retenção:** política documentada por tipo de métrica e aplicada por job de limpeza (LGPD art. 16)
3. **Logs de acesso:** cada requisição gera log mínimo (IP, data/hora, ação) retido **exatamente 6 meses**, sob sigilo (Marco Civil art. 15) — se a API for exposta à internet
4. **Guard de privacidade na API:** nenhuma rota/resposta pode expor dado por-pessoa (auditável)

### Como funciona
```
Dashboard ──HTTP──▶ FastAPI ──▶ PostgreSQL (agregados)
                         │
                         └──▶ log de acesso (mínimo, 6 meses, sigilo)
```
Exemplo de resposta:
```json
GET /api/v1/ocupacao
{ "zona": "recepcao", "pessoas": 12, "atualizado_em": "2026-10-08T14:03:11" }
```

### Critérios de sucesso
1. Cliente consulta endpoints de contagem, ocupação, séries, histogramas e heatmap agregado e recebe JSON válido
2. TTL documentado por tipo de métrica e aplicado de fato (registro antigo some após o prazo)
3. Cada acesso gera log IP/data/hora/ação; logs retidos 6 meses sob sigilo
4. Auditoria de rotas/respostas confirma: **nenhum** endpoint expõe dado por-pessoa

### Requisitos
API-02, API-03, API-04

---

## Fase 5 — Dashboard web de ocupação e séries

### Objetivo
A gestão do hotel ver ocupação ao vivo e tendências no navegador — e o sistema ganhar ambiente reproduzível de ponta a ponta.

### O que será construído
1. **Painel de ocupação ao vivo:** números por zona atualizando via **WebSocket** (sem dar F5)
2. **Gráficos de séries temporais:** contagem/ocupação com filtro de período
3. **Saúde/frescor do dado:** indicador visual de que a métrica está viva (o usuário nunca confere dado velho achando que é ao vivo)
4. **docker-compose:** PostgreSQL + API + dashboard sobem com um comando

### Como funciona
```
PostgreSQL ◀── FastAPI ◀── WebSocket ◀── Dashboard (navegador)
                              ▲
                    atualiza a cada evento agregado
```
Stack conforme pesquisa: React + Vite + ECharts (gráficos), WebSocket para tempo real.

### Critérios de sucesso
1. Usuário abre o dashboard e vê a ocupação por zona atualizando em tempo real sem refresh
2. Usuário filtra séries por período e o gráfico responde
3. Ambiente novo sobe com um comando e funciona de ponta a ponta
4. Dashboard indica frescor/health da métrica

### Requisitos
DSH-01, DSH-02, OPS-02

---

## Fase 6 — Multi-câmera e ingestão RTSP

### Objetivo
Processar múltiplos streams simultâneos com robustez de produção (reconexão, watchdog), exercitado com **MediaMTX e vídeos-amostra** antes de os DVRs reais do hotel chegarem.

### Por que agora
Só depois de a lógica de contagem estar correta (fases 1–2) e existir plataforma (3–5) faz sentido escalar para N câmeras.

### O que será construído
1. **Ingestão RTSP multi-stream:** PyAV (não OpenCV — ele corrompe frames RTSP após 15–35 s, consta na pesquisa) lendo várias câmeras ao mesmo tempo
2. **Fila por câmera com drop-oldest:** câmera lenta não trava o sistema
3. **Watchdog de staleness:** stream que trava é detectado e **reconectado com backoff exponencial**
4. **Tracker por câmera:** cada câmera tem seu próprio ByteTrack; reconexão **reseta** o tracker daquela câmera
5. **MediaMTX local:** servidor RTSP de teste para exercitar o caminho de produção sem ter os DVRs

### Como funciona
```
Câmera 1 ──RTSP──▶ worker 1 ─┐
Câmera 2 ──RTSP──▶ worker 2 ─┼─▶ (cada uma: detecção → track efêmero → zona → agregado)
Câmera 3 ──RTSP──▶ worker 3 ─┘
                 ▲ watchdog: staleness > limite → reconecta com backoff
```
**Regra de privacidade reforçada aqui:** os trackers são **estritamente por câmera**; não existe código que compare a câmera 1 com a câmera 2 (nem por ID, nem por silhueta/aparência) — LGPD art. 12 §2º.

### Critérios de sucesso
1. Múltiplas câmeras RTSP processadas simultaneamente (MediaMTX/amostras), tracker por câmera
2. Derrubar e reconectar um stream não corrompe contagens (sessões fechadas, ocupação reconciliada, tracker resetado)
3. Stream travado é detectado pelo watchdog e reconectado com backoff, sem intervenção manual
4. Com N câmeras, latência/frescor por câmera dentro do orçamento (benchmark documentado)

### Requisitos
ING-02, OPS-01

---

## Fase 7 — Analytics de permanência e heatmap agregado

### Objetivo
Mostrar **quanto tempo as pessoas permanecem** em cada zona e **onde o fluxo se concentra** — sempre como agregados, nunca como traço por pessoa.

### O que será construído
1. **Dwell time por zona:** tempo de permanência em ROIs poligonais, com timeout de saída e fechamento de sessões zumbis
2. **Agregação de dwell:** por zona × janela de tempo, persistem **apenas** `n_permanencias`, `soma_segundos`, `mín/máx` e **histograma de faixas** (0–2, 2–5, 5–15, 15+ min)
3. **Heatmap de densidade:** matriz célula × janela; posições efêmeras somam contadores por célula; **nunca** histórico por pessoa
4. **Telas no dashboard:** heatmap de densidade + histograma de permanências

### Como funciona
```
RAM (efêmero):                    Banco (agregado):
trilha entrou 14:02:11             zona | janela  | n | soma_seg | faixas
saio   14:10:43                    -----+---------+---+----------+------------------
duração = 8min32s  ──┐             recep|14:02-03 | 9 |   4320   | 0-2min:4 2-5:3 ...
(dado morre aqui)    └──▶ somente isto persiste
```

**O que dá para perguntar (permitido):** média de permanência por zona/horário, % de visitas acima de 5 min, onde o fluxo se concentra.
**O que é impossível perguntar (proibido):** quanto tempo *Aqueleindivíduo* ficou ontem — a linha necessária para responder nunca é gravada.

### Critérios de sucesso
1. Dwell calculado em RAM com timeout e sessões zumbis; no banco só histograma/soma/n por zona×janela — nenhuma linha por pessoa
2. Heatmap de densidade (célula × janela) gerado por câmera/zona a partir de posições efêmeras, sem histórico por-pessoa
3. Usuário vê heatmap e histograma no dashboard
4. Auditoria do schema confirma: dwell e heatmap não gravaram nenhum identificador individual

### Requisitos
DWL-01, DWL-02, DSH-03

---

## Fase 8 — Validação de qualidade e testes automatizados

### Objetivo
Cobrir as regras críticas com testes automatizados e **medir a acurácia real** da contagem contra marcação manual em condições de pico.

### O que será construído
1. **Suíte de testes:** tripwire, dwell+timeout, fila, ocupação e reconexão — rodando com um comando
2. **Protocolo de marcação manual:** alguém assiste o vídeo de pico e anota a contagem "ground truth"; o sistema compara
3. **Relatório de acurácia:** erro médio + faixa documentados
4. **Definição escrita de "quem conta"** (ex.: equipe do hotel conta ou não?) — aplicada consistentemente na validação

### Como funciona
```
vídeo de pico ──▶ pipeline do sistema ──▶ contagem automática
     │
     └──▶ marcação manual (ground truth) ──▶ comparação ──▶ relatório (erro médio, p95)
```

### Critérios de sucesso
1. Suíte cobre tripwire, dwell+timeout, fila, ocupação e reconexão; passa ponta a ponta com um comando
2. Contagem validada contra marcação manual em vídeo de pico, com relatório de acurácia documentado
3. Definição de "quem conta" escrita e aplicada no relatório

### Nota honesta
A acurácia **em cenário de hotel real não pode ser julgada ainda** (sem DVRs) — a validação de campo real acontece quando os streams do hotel estiverem disponíveis; esta fase valida com webcam/vídeos-amostra e documenta a limitação.

### Requisitos
QUA-02, QUA-03

---

## Fase 9 — Conformidade LGPD e preparação para produção

### Objetivo
Passar de uma auditoria formal de LGPD e ter a documentação de compliance pronta — **gate obrigatório antes de qualquer implantação real**.

### Por que a última (e obrigatória)
Documentos como RIPD/LIA descrevem o sistema **como construído**; fazem sentido quando o sistema existe. Mas a *obrigação* deles é inegociável: sem essa fase, não se vai ao ar.

### O que será construído
1. **Auditoria de código automatizada** (requisito PRV-01): script que varre o repositório e **falha** se encontrar:
   - gravação de `track_id`/`session_id` persistido, trilha, rota, jornada, embedding, vetor de silhueta/aparência
   - frame/imagem em disco (inclui logs, backups, dumps)
   - módulo de face/biometria/demografia
2. **RIPD** (Relatório de Impacto à Proteção de Dados — LGPD art. 5º XVII, art. 38): tipos de dados, metodologia de coleta/segurança, medidas de mitigação
3. **LIA** (Legitimate Interest Assessment — art. 10 §3): demonstração do interesse legítimo do hotel (operação/segurança) vs. privacidade dos titulares, com salvaguardas
4. **ROPA** (registro de operações — art. 37): inventário das operações, finalidades, bases legais, retenções
5. **Aviso de monitoramento** afixado nas áreas monitoradas (art. 6º IV — transparência)
6. **Encarregado (DPO)** indicado com contato publicado (art. 41 + Res. CD/ANPD nº 18/2024)
7. **Plano de resposta a incidente** (art. 48): detecção → contenção → comunicação à ANPD e titulares

### Critérios de sucesso
1. Auditoria de código roda e passa: nada por-pessoa gravado, nenhum frame em disco, nenhum módulo de face/biometria
2. RIPD + LIA + ROPA existem como documentos revisados, **anteriores a produção**
3. Aviso de monitoramento afixado e encarregado indicado com contato publicado
4. Plano de resposta a incidente documentado, com comunicação ANPD/titulares

### Requisitos
PRV-01, PRV-02, PRV-03, PRV-04, PRV-05, OPS-03

---

## Resumo de mapeamento (27 requisitos → 9 fases)

| Fase | Requisitos |
|------|-----------|
| 1 | ING-01, ING-03, CNT-01, CNT-03 |
| 2 | CNT-02, CNT-04 |
| 3 | API-01, QUA-01 |
| 4 | API-02, API-03, API-04 |
| 5 | DSH-01, DSH-02, OPS-02 |
| 6 | ING-02, OPS-01 |
| 7 | DWL-01, DWL-02, DSH-03 |
| 8 | QUA-02, QUA-03 |
| 9 | PRV-01, PRV-02, PRV-03, PRV-04, PRV-05, OPS-03 |

**Cobertura:** 27/27 — nenhum requisito órfão, nenhum duplicado.

## Fora do escopo para sempre (lembrete permanente)

Face, biometria, demografia, emoção, controle de acesso (catracas), **MTMCT/Re-ID/associação entre câmeras (inclusive por silhueta)**, `session_traces`/`sessoes`, IDs persistidos, embeddings, rota/jornada, heatmap por indivíduo, gravação de vídeo. Base: LGPD art. 11 (sensível) e art. 12 §2º (perfil comportamental) + decisão do usuário.
