# Desenho por Fase — rationale e mecanismo

> 📝 **STATUS: RASCUNHO DE DESIGN PRÉ-PLANEJAMENTO — NÃO É A VERSÃO OFICIAL DAS FASES.**
>
> Este documento guarda **o porquê** e **o como** de cada fase: a justificativa de ordenação, a
> lista de entregáveis e o mecanismo de funcionamento. Ele **não** define o que uma fase é.
>
> - **O que cada fase é (objetivo, requisitos, critérios de sucesso):** [`../ROADMAP.md`](../ROADMAP.md)
>   §Phase Details — **canônico, não alterado**.
> - **Requisitos e rastreabilidade:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) §Traceability — **canônico**.
> - **Estado de execução:** [`../ROADMAP.md`](../ROADMAP.md) §Progress e [`../STATE.md`](../STATE.md).
> - **A versão oficial de cada fase:** o `PLAN.md` que o GSD cria via `/gsd:plan-phase` no momento
>   em que a fase começa (já existem para as Fases 1 e 2 em [`../phases/`](../phases/)).
>
> Na dúvida, o `ROADMAP.md` prevalece. Este arquivo é insumo de apoio ao planejamento.

---

## Fase 1 — Fatia vertical single-câmera (captura, detecção, rastreio efêmero)

**Planejamento oficial:** [`../phases/01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero/`](../phases/01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero/)

**Por que primeiro.** É o "cimento" de tudo: se a captura e a detecção não funcionarem bem, nada depois disso importa. Também é aqui que os hábitos de privacidade (nada em disco) entram **desde o início** — mudar isso no final seria refazer metade do sistema.

**O que foi construído.**
1. **Captura de vídeo:** leitor de webcam e de arquivos de vídeo-amostra (RTSP não ainda — fase 6)
2. **Detecção de corpo:** o YOLO treinado com CrowdHuman que já existe em `main.py` (base do projeto), desenhando caixas ao redor de pessoas
3. **Rastreio efêmero (ByteTrack):** liga as caixas de frames seguintes para o sistema entender que "a caixa 7 de agora é a mesma da caixa 7 de 0,03 s atrás"
4. **Overlay na tela:** janela de vídeo com caixas + IDs temporários visíveis (só para debug — os IDs não são gravados em lugar nenhum)

**Como funciona.**
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

---

## Fase 2 — Contagem por zona e ocupação em tempo real

**Planejamento oficial:** [`../phases/02-*/`](../phases/) (`02-01` a `02-04`)

**Por que antes da infra.** Um bug de contagem/ocupação é 100× mais barato de descobrir aqui (tela, sem infra) do que depois reprocessando dados no PostgreSQL. É a lógica de maior risco do sistema.

**O que foi construído.**
1. **Zonas (ROIs):** polígonos nomeados desenhados sobre a imagem (Recepção, Restaurante, Spa…), configurados em `config/zonas.yaml` por câmera
2. **Ocupação instantânea por zona:** recontagem a cada frame — quantas pessoas estão dentro do polígono (pé, centro ou sobreposição de borda) — com clamp `[0, capacidade]`
3. **Interseção de área:** `Interseção = Área(Objeto) ∩ Área(ROI)` — percentual da área do ROI efetivamente coberta pelas pessoas, exibido no overlay
4. **Proteções de estabilidade:** reset diário (meia-noite local), reset por inatividade (> 10 min vazia), reconciliação total ao reabrir a fonte

**Como funciona.**
```
Zona HALL (polígono ROI):

   ┌───────────────────────────┐
   │        ▓▓▓                │   ▓ = interseção da área ocupada
   │       ▓▓▓▓▓      ▓▓       │       com o ROI (destacada no overlay)
   │───────────────────────────│
   │  ▓▓▓                     │   Ocupação(HALL) = nº de pessoas presentes
   └───────────────────────────┘   % Área(HALL) = área ocupada / área do ROI

   Toda pessoa é recontada a cada frame → nada é acumulado,
   nada é gravado, não há "trava" de entrada/saída.
```
- **Sem dupla contagem:** a ocupação é um *estado recalculado*, não um contador incremental — a mesma pessoa não gera 2 eventos por tremor de caixa
- **Sem explosão:** rajadas de detecção (flicker) não geram eventos, apenas atualizam o valor do frame
- **Sem fantasma:** reiniciar o vídeo → a ocupação é reconciliada (nunca fica "47 pessoas numa sala vazia")
- **Tripwire:** previsto na versão original desta fase, **desativado por decisão do usuário** (código comentado em `zona.py`, `overlay.py` e `main.py` — mantido para reativação futura)

---

## Fase 3 — Persistência PostgreSQL (fila + escrita em lote)

**Por que assim.** Escrever no banco dentro do loop de vídeo derruba os FPS (o doc 08 proíbe I/O no loop). A separação "loop quente / caminho frio" é o padrão de todos os sistemas de contagem em produção (confirmado na pesquisa).

**O que será construído.**
1. **Fila em memória:** o loop publica eventos agregados (ocupação por zona) e segue — nunca espera o banco
2. **Batch writer idempotente:** worker que acumula N eventos ou T segundos e grava em lote, com UUID por lote para que reentrega não duplique
3. **Schema mínimo:** tabelas de **configuração** (câmeras, zonas) + **métricas agregadas** (`metricas_fluxo_zona`, séries) — derivado de [`MODELAGEM_BANCO_DE_DADOS.md`](MODELAGEM_BANCO_DE_DADOS.md) **sem** `sessoes`/`session_traces`
4. **Métrica de latência:** FPS/latência monitorados para provar que o banco não afeta o loop

**Como funciona.**
```
Loop de vídeo ──(evento agregado)──▶ fila RAM ──▶ batch writer ──▶ PostgreSQL
     │                                                             │
     └── nunca faz I/O de banco ←── evidência: FPS estável         │ (só agregados)
```

---

## Fase 4 — API FastAPI de métricas e conformidade Marco Civil

**O que será construído.**
1. **Endpoints somente-leitura:** contagem atual, ocupação por zona, séries temporais, histogramas de dwell (estrutura pronta), heatmap agregado (estrutura pronta)
2. **TTL de retenção:** política documentada por tipo de métrica e aplicada por job de limpeza (LGPD art. 16)
3. **Logs de acesso:** cada requisição gera log mínimo (IP, data/hora, ação) retido **exatamente 6 meses**, sob sigilo (Marco Civil art. 15) — se a API for exposta à internet
4. **Guard de privacidade na API:** nenhuma rota/resposta pode expor dado por-pessoa (auditável)

**Como funciona.**
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

---

## Fase 5 — Dashboard web de ocupação e séries

**O que será construído.**
1. **Painel de ocupação ao vivo:** números por zona atualizando via **WebSocket** (sem dar F5)
2. **Gráficos de séries temporais:** contagem/ocupação com filtro de período
3. **Saúde/frescor do dado:** indicador visual de que a métrica está viva (o usuário nunca confere dado velho achando que é ao vivo)
4. **docker-compose:** PostgreSQL + API + dashboard sobem com um comando

**Como funciona.**
```
PostgreSQL ◀── FastAPI ◀── WebSocket ◀── Dashboard (navegador)
                              ▲
                    atualiza a cada evento agregado
```
Stack conforme pesquisa: React + Vite + ECharts (gráficos), WebSocket para tempo real.

---

## Fase 6 — Multi-câmera e ingestão RTSP

**Por que agora.** Só depois de a lógica de contagem estar correta (fases 1–2) e existir plataforma (3–5) faz sentido escalar para N câmeras.

**O que será construído.**
1. **Ingestão RTSP multi-stream:** PyAV (não OpenCV — ele corrompe frames RTSP após 15–35 s, consta na pesquisa) lendo várias câmeras ao mesmo tempo
2. **Fila por câmera com drop-oldest:** câmera lenta não trava o sistema
3. **Watchdog de staleness:** stream que trava é detectado e **reconectado com backoff exponencial**
4. **Tracker por câmera:** cada câmera tem seu próprio ByteTrack; reconexão **reseta** o tracker daquela câmera
5. **MediaMTX local:** servidor RTSP de teste para exercitar o caminho de produção sem ter os DVRs

**Como funciona.**
```
Câmera 1 ──RTSP──▶ worker 1 ─┐
Câmera 2 ──RTSP──▶ worker 2 ─┼─▶ (cada uma: detecção → track efêmero → zona → agregado)
Câmera 3 ──RTSP──▶ worker 3 ─┘
                 ▲ watchdog: staleness > limite → reconecta com backoff
```
**Regra de privacidade reforçada aqui:** os trackers são **estritamente por câmera**; não existe código que compare a câmera 1 com a câmera 2 (nem por ID, nem por silhueta, nem por aparência) — LGPD art. 12 §2º.

---

## Fase 7 — Analytics de permanência e heatmap agregado

**O que será construído.**
1. **Dwell time por zona:** tempo de permanência em ROIs poligonais, com timeout de saída e fechamento de sessões zumbis
2. **Agregação de dwell:** por zona × janela de tempo, persistem **apenas** `n_permanencias`, `soma_segundos`, `mín/máx` e **histograma de faixas** (0–2, 2–5, 5–15, 15+ min)
3. **Heatmap de densidade:** matriz célula × janela; posições efêmeras somam contadores por célula; **nunca** histórico por pessoa
4. **Telas no dashboard:** heatmap de densidade + histograma de permanências

**Como funciona.**
```
RAM (efêmero):                    Banco (agregado):
trilha entrou 14:02:11             zona | janela  | n | soma_seg | faixas
saiu   14:10:43                    -----+---------+---+----------+------------------
duração = 8min32s  ──┐             recep|14:02-03 | 9 |   4320   | 0-2min:4 2-5:3 ...
(dado morre aqui)    └──▶ somente isto persiste
```

**O que dá para perguntar (permitido):** média de permanência por zona/horário, % de visitas acima de 5 min, onde o fluxo se concentra.
**O que é impossível perguntar (proibido):** quanto tempo *Aqueleindivíduo* ficou ontem — a linha necessária para responder nunca é gravada.

---

## Fase 8 — Validação de qualidade e testes automatizados

**O que será construído.**
1. **Suíte de testes:** ocupação por área/interseção, dwell+timeout, fila e reconexão — rodando com um comando
2. **Protocolo de marcação manual:** alguém assiste o vídeo de pico e anota a contagem "ground truth"; o sistema compara
3. **Relatório de acurácia:** erro médio + faixa documentados
4. **Definição escrita de "quem conta"** (ex.: equipe do hotel conta ou não?) — aplicada consistentemente na validação

**Como funciona.**
```
vídeo de pico ──▶ pipeline do sistema ──▶ contagem automática
     │
     └──▶ marcação manual (ground truth) ──▶ comparação ──▶ relatório (erro médio, p95)
```

**Nota honesta.** A acurácia **em cenário de hotel real não pode ser julgada ainda** (sem DVRs) — a validação de campo real acontece quando os streams do hotel estiverem disponíveis; esta fase valida com webcam/vídeos-amostra e documenta a limitação.

---

## Fase 9 — Conformidade LGPD e preparação para produção

**Por que a última (e obrigatória).** Documentos como RIPD/LIA descrevem o sistema **como construído**; fazem sentido quando o sistema existe. Mas a *obrigação* deles é inegociável: sem essa fase, não se vai ao ar.

**O que será construído.**
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

---

_Extraído de `docs/DOCUMENTACAO_PROJETO_E_LGPD/09_PLANO_DE_FASES_V1.md` na consolidação de 2026-10-21:
foram preservados o *rationale*, os entregáveis e o mecanismo de cada fase; objetivo, requisitos e
critérios de sucesso deixaram de ser replicados aqui porque são canônicos em `../ROADMAP.md` e
`../REQUIREMENTS.md`._
