# Plano Completo v1 (Atualizado) — Visão Computacional para Hotelaria (Analytics de Fluxo)

> **Documento mestre de referência e alinhamento** — une requisitos, roadmap e detalhamento técnico de cada uma das 9 fases do v1, adaptado ao cenário operacional vigente.
> **Data de atualização:** 2026-10-21 · **Status:** Fases 1 e 2 concluídas (33 testes verdes) · Pronto para a Fase 3.
> **Base legal verificada:** LGPD (Lei 13.709/2018) e Marco Civil (Lei 12.965/2014) — ver `.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md` e `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md`.

---

## 1. O que é o sistema

Câmeras de segurança do hotel viram sensores de negócio: **contagem de pessoas por zona, ocupação em tempo real, tempo de permanência (dwell) e mapa de calor de fluxo** — para o hotel saber *quantas pessoas estão em cada lugar, quando e por quanto tempo ficam*, sem nunca identificar ninguém.

**Base do projeto:** o detector já existente (`main.py`, YOLO CrowdHuman, ~320 FPS em GPU) — evoluindo de forma vertical e incremental pelas fases planejadas.

### Invariantes obrigatórios em todas as fases

| Invariante | Base legal / Operacional |
|---|---|
| Saída **exclusivamente agregada** — nenhum dado por-pessoa é gravado | LGPD art. 12 §2º |
| **Zero associação entre câmeras** — nem por ID, nem por silhueta, nem por aparência | LGPD art. 12 §2º + decisão do projeto |
| **Frames de vídeo nunca tocam disco** — imagem vive só na RAM durante a inferência | LGPD art. 6º III (minimização) |
| Face, biometria, demografia **nunca** existem no código | LGPD art. 11 (dado sensível) |
| IDs de rastreamento (ByteTrack) morrem ao sair do quadro, **intra-câmera** | LGPD art. 6º III |
| **Nenhum stream real com hóspedes antes do gate da Fase 9** — fases 1–8 usam só webcam, vídeos-amostra e MediaMTX local | LGPD art. 7º IX + art. 10 §3 (LIA formal ao fim da Fase 9) |

**Risco se violado:** multa de até **2% do faturamento, teto R$ 50 milhões por infração** (LGPD art. 52), além de bloqueio/eliminação de dados.

---

## 2. Resumo de Requisitos e Status Atual (v1)

* **Status atual:** 6/27 requisitos concluídos (ING-01, ING-03, CNT-01, CNT-02, CNT-03, CNT-04).
* **Escopo vigente:** Contagem **ROI-only** (ocupação por área via interseção $\text{Área}(\text{Objeto}) \cap \text{Área}(\text{ROI})$). O tripwire bidirecional foi desativado por decisão do projeto (código mantido comentado, não removido).

### Categorias de Requisitos:
1. **Ingestão (ING):** Webcam, vídeos-amostra (v1) e futuras câmeras RTSP; frames estritamente voláteis em RAM.
2. **Contagem & Ocupação (CNT):** YOLO CrowdHuman (corpo apenas), associação efêmera em RAM (ByteTrack), ocupação instantânea por zona poligonal ROI.
3. **Persistência & Armazenamento (BD):** PostgreSQL com schema agregado e filas assíncronas em lote (sem I/O no loop de vídeo).
4. **API & Governança (API / GOV):** Endpoints somente-leitura em FastAPI, logs de acesso de 6 meses (Marco Civil), TTL de retenção de métricas.
5. **Analytics & Escala (ANL / ESC):** Dwell time (permanência), mapas de calor de densidade agregada, suporte a múltiplas câmeras RTSP com reconexão exponencial.
6. **Qualidade & Auditoria (QUA / OPS / LGPD):** Cobertura de testes automatizados, RIPD formal, LIA, ROPA, encarregado (DPO) e gate de auditoria antes da produção.

---

## 3. Detalhamento Foco a Foco das 9 Fases

### Fase 1 — Fatia vertical single-câmera (captura, detecção, rastreio efêmero)
* **Status:** Concluída (2026-10-08).
* **Constrói:** Pipeline básico em `main.py` integrando captura de webcam/vídeo-amostra, detector YOLO CrowdHuman (corpo), rastreador intra-câmera em RAM (ByteTrack) com overlay visual de bounding boxes e IDs efêmeros.
* **Garantias:** Frames voláteis descartados na mesma hora; nenhum arquivo de imagem em disco; zero biometria.
* **Critérios atendidos:** Testes automatizados (`test_privacidade.py`, `test_rastreio.py`) verdes.

### Fase 2 — Contagem por zona e ocupação em tempo real (ROI-only)
* **Status:** Concluída (2026-10-12).
* **Constrói:** Módulo `zona.py` para definição de polígonos ROI, cálculo de ocupação instantânea por presença e interseção de área ($\text{Área}(\text{Objeto}) \cap \text{Área}(\text{ROI})$), renderização de polígonos no overlay, clamp/reset diário e reconciliação.
* **Garantias:** Contagem espacial precisa sem dupla contagem por ID duplicado nas bordas.
* **Critérios atendidos:** Bateria de testes de zona e overlay (`test_zona.py`, `test_overlay.py`) verdes.

### Fase 3 — Persistência PostgreSQL (fila + escrita em lote)
* **Constrói:** Schema relacional PostgreSQL estritamente restrito a tabelas de configuração (`cameras`, `zonas`) e métricas agregadas (`metricas_fluxo_zona`, `dwell_agregado_zona`, `heatmap_densidade_camada`). Implementação de fila assíncrona em memória (*batch writer*) para que qualquer I/O de banco ocorra completamente fora do loop principal de processamento de vídeo (garantindo latência < 5ms/frame).
* **Critérios de sucesso:**
  1. Banco criado apenas com tabelas de configuração e agregados (sem tabelas de rastreio individual ou sessões).
  2. Escrita em lote assíncrona testada sob carga sem impactar o FPS do vídeo.
  3. Testes automatizados de conexão e escrita agregada.

### Fase 4 — API FastAPI de métricas e conformidade Marco Civil
* **Constrói:** Aplicação FastAPI com endpoints somente-leitura para consulta das métricas agregadas por zona e período. Implementação de política de retenção (TTL) e logs de acesso auditáveis por 6 meses conforme exigido pelo Marco Civil da Internet (Lei 12.965/2014).
* **Critérios de sucesso:**
  1. Endpoints respondem exclusivamente com JSON agregado (médias, contagens, histogramas).
  2. Logs de acesso registram quem consultou o quê, retidos por 6 meses.
  3. Documentação interativa da API (Swagger/OpenAPI).

### Fase 5 — Dashboard operacional de ocupação em tempo real
* **Constrói:** Interface web leve conectada à API FastAPI para visualização em tempo real da ocupação por zona do hotel, indicadores de lotação e alertas operacionais visuais para equipes de recepção e segurança.
* **Critérios de sucesso:**
  1. Tela exibe o status de ocupação instantânea por zona com atualização em tempo real.
  2. Indicadores visuais claros de capacidade (verde, amarelo, vermelho).

### Fase 6 — Multi-câmera RTSP com reconexão e watchdog
* **Constrói:** Arquitetura para processamento paralelo de múltiplas fontes RTSP simultâneas, incorporando mecanismo de reconexão automática com backoff exponencial e watchdog de latência/staleness para evitar travamentos de stream.
* **Critérios de sucesso:**
  1. Sistema recupera automaticamente a conexão com câmeras após queda de rede simulada.
  2. Watchdog sinaliza quedas ou congelamentos de feed sem derrubar o processo principal.

### Fase 7 — Analytics de permanência e heatmap agregado
* **Constrói:** Módulo de tempo de permanência (*dwell time*) por zona com timeout de saída e fechamento de sessões zumbis; agregação por zona×janela (**só** `n`, `soma_segundos`, `mín/máx`, histograma de faixas 0–2/2–5/5–15/15+ min); heatmap de densidade (célula × janela) somando posições efêmeras; telas no dashboard.
* **Como funciona (Privacy by Design):**
  ```
  RAM (efêmero):                         Banco (agregado):
  trilha entrou 14:02:11                  zona | janela  | n | soma_seg | faixas
  saiu   14:10:43 → duração 8min32s  ──▶  recep|14:02-03 | 9 |  4320    | 0-2min:4 ...
  (dado morre aqui — nunca é gravado)
  ```
  * **Permitido:** "Média de permanência na recepção por horário".
  * **Impossível (por design):** "Quanto tempo *aquele indivíduo* ficou ontem" — a linha necessária jamais existe no banco.
* **Critérios de sucesso:**
  1. No banco só histograma/soma/n por zona×janela — nenhuma linha por pessoa.
  2. Heatmap gerado só de posições efêmeras, sem histórico por-pessoa.
  3. Usuário vê heatmap e histograma no dashboard.
  4. Auditoria do schema confirma zero identificadores individuais.

### Fase 8 — Suíte de testes de carga, resiliência e validação de campo
* **Constrói:** Bateria completa de testes automatizados cobrindo resiliência sob falhas de banco/rede, estouro de fila, estresse de multi-câmeras e validação de acurácia de contagem contra marcação manual em condições de pico.
* **Critérios de sucesso:**
  1. Cobertura de testes robusta para todas as regras críticas.
  2. Validação de acurácia documentada.

### Fase 9 — Auditoria formal LGPD (RIPD/LIA/ROPA) e liberação de produção
* **Constrói:** Condução da auditoria jurídica e técnica formal exigida antes de ligar qualquer stream real de hotel — produzindo o Relatório de Impacto à Proteção de Dados (RIPD), Legitimate Interest Assessment (LIA), Registro de Operações (ROPA), designação formal de Encarregado (DPO) e plano de resposta a incidentes.
* **Critérios de sucesso:**
  1. Parecer jurídico favorável assinado.
  2. Gate de liberação de produção aprovado para streams reais com hóspedes.

---

## 4. Organização do Repositório e Documentação

* **`.planning/`**: Diretório central do GSD (roadmap, requisitos, estado, pesquisas, histórico de fases).
* **`.planning/context/`**: Manuais de engenharia, arquitetura, design por fase e pareceres LGPD/Marco Civil.
* **`src/` ou raiz (`main.py`, `zona.py`, etc.)**: Código-fonte do motor de visão computacional.
* **`tests/`**: Suíte de testes automatizados (`pytest`).
