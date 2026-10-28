# Documento Detalhado por Fases — Visão Computacional para Hotelaria (Analytics de Fluxo)

**Versão:** 1.1  
**Data:** 2026-10-26  
**Público-alvo:** Equipe Técnica, Gestão, Jurídico/Conformidade LGPD e Operação do Hotel  
**Branch:** `docs/refatoracao-organizacao-documentacao`  
**Fonte única da verdade:** `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/PROJECT.md`, `.planning/STATE.md`, `.planning/context/PLANO_V1_COMPLETO.md`

---

## Sumário

- [1. Objetivo Geral](#1-objetivo-geral)
- [2. Escopo, Fora de Escopo e Valores](#2-escopo-fora-de-escopo-e-valores)
- [3. Glossário Completo](#3-glossário-completo)
- [4. Situação Atual](#4-situação-atual)
- [5. Regras de Ouro (Privacidade por Design)](#5-regras-de-ouro-privacidade-por-design)
- [6. Arquitetura Atual x Arquitetura Alvo](#6-arquitetura-atual-x-arquitetura-alvo)
- [7. Modelo de Dados: Permitido x Vetado](#7-modelo-de-dados-permitido-x-vetado)
- [8. Mini-Planejamento Detalhado por Fase (1 a 9)](#8-mini-planejamento-detalhado-por-fase-1-a-9)
- [9. Cronograma Sugerido por Ordem](#9-cronograma-sugerido-por-ordem)
- [10. Testes, Verificações e Controle](#10-testes-verificações-e-controle)
- [11. Dicas Práticas para Execução](#11-dicas-práticas-para-execução)
- [12. Referências](#12-referências)
- [13. Anexos](#13-anexos)

---

## 1. Objetivo Geral

O projeto tem como objetivo transformar as câmeras de segurança do hotel em **sensores de negócio anonimizados**. 

A ideia é simples: **saber quantas pessoas estão em cada área, por quanto tempo ficam e como o fluxo se comporta, sem nunca identificar ninguém.**

Tudo deve ser feito com foco em clareza para gestão, sem abrir mão da conformidade com a LGPD e do Marco Civil da Internet.

---

## 2. Escopo, Fora de Escopo e Valores

### 2.1 Escopo
- Contagem e ocupação por zona delimitada (ROI)
- Cálculo por interseção de área `Área(Objeto) ∩ Área(ROI)`
- Tempo de permanência (Dwell) **somente agregado**
- Mapa de calor de densidade **somente agregado**
- Funcionar com webcam, vídeos-amostra e futuramente com câmeras RTSP
- Tudo voltado a **métricas agregadas e anônimas**

### 2.2 Fora de Escopo
- Reconhecimento facial, biometria, idade, gênero, emoção
- Rastreamento entre câmeras (MTMCT/Re-ID)
- Criação de perfis, trilhas ou jornadas de pessoas
- Armazenamento de imagens, vídeos ou recortes
- Controle de acesso por catraca
- Qualquer dado que permita identificar ou reidentificar alguém

### 2.3 Valores
- **Privacidade primeiro:** Se houver dúvida, não grave. Agregue.
- **Simplicidade:** Melhor solução funcional e auditável, do que complexa e arriscada.
- **Transparência:** Tudo documentado para equipe, gestão e conformidade.
- **Pragmático:** Evoluir por fatias testáveis, sem tentar fazer tudo de uma vez.

---

## 3. Glossário Completo

| Sigla/Termo | Significado | Explicação prática |
|---|---|---|
| **ROI** | Region of Interest (Região de Interesse) | Área demarcada no vídeo (polígono) onde queremos contar/medir ocupação. |
| **ByteTrack** | Rastreador de objetos | Ajuda a não contar a mesma pessoa duas vezes enquanto ela passa. Vive **apenas em memória**. |
| **Dwell** | Tempo de permanência | Quanto tempo, em média, as pessoas ficam em determinada zona. Só guardamos somas e faixas. |
| **Heatmap Agregado** | Mapa de calor agrupado | Mostra "onde há mais movimentação/concentração", nunca "por onde fulano passou". |
| **Fila/Batch Writer** | Fila + escrita em lote | Em vez de gravar no banco a cada frame, junta vários dados e grava de uma vez, fora do processamento do vídeo. |
| **Watchdog** | Vigia de conexão | Detecta se um stream "travou" e tenta reconectar sozinho. |
| **Backoff Exponencial** | Tentativas com intervalo crescente | Tenta reconectar a cada X segundos, aumentando o intervalo para não sobrecarregar a rede. |
| **RIPD** | Relatório de Impacto à Proteção de Dados | Documento que avalia riscos e medidas para tratamento de dados. |
| **LIA** | Avaliação de Interesse Legítimo | Justifica o uso legítimo quando não há consentimento. |
| **ROPA** | Registro das Operações de Tratamento | Listagem de tudo que é feito com os dados. |
| **DPO/Encarregado** | Responsável pela Proteção de Dados | Pessoa de contato para dúvidas sobre LGPD. |
| **TTL** | Tempo de Retenção | Por quanto tempo guardamos determinado tipo de informação. |
| **GSD** | Get Shit Done | Metodologia usada para planejar e validar cada fase. |
| **VERIFICATION.md** | Relatório de verificação | Prova de que a fase realmente atingiu o objetivo proposto. |

---

## 4. Situação Atual

| Item | Situação | Detalhes |
|---|---|---|
| **Fases concluídas** | 2 de 9 | Fase 1 e Fase 2 finalizadas e aprovadas pelo verificador GSD. |
| **Requisitos atendidos** | 6 de 27 | ING-01, ING-03, CNT-01, CNT-02, CNT-03, CNT-04 |
| **Testes** | 33/33 verdes | Todos passando com `./.venv/bin/python -m pytest` |
| **Escopo vigente** | ROI-only | Tripwire (contagem por linha) está **desativado e comentado**. Foco total em ocupação por zona e interseção de área. |
| **Próxima etapa** | Fase 3 | Persistência PostgreSQL com fila + escrita em lote |

---

## 5. Regras de Ouro (Privacidade por Design)

Estas regras **devem ser seguidas em TODAS as fases**, sem exceção:

- [ ] **Só agregado:** Nunca guardar "quem". Só "quantos", "por quanto tempo" em forma de soma/histograma.
- [ ] **Nada em disco:** Frames, imagens, recortes ou capturas **nunca** devem ser gravados.
- [ ] **Só em memória:** Rastreamento com ByteTrack apenas enquanto a pessoa estiver visível.
- [ ] **Uma câmera por vez na lógica:** Nunca comparar câmeras entre si.
- [ ] **Sem biometria:** Proibido qualquer coisa relacionada a rosto, digital, íris ou características únicas.
- [ ] **Sem trilhas:** Ao sair da zona/quadro, todo rastro individual deve sumir.
- [ ] **Apenas o necessário:** Se não for estritamente preciso para **contar, medir ocupação ou medir permanência agregada**, não deve ser feito.
- [ ] **Auditoria constante:** Se aparecer `track_id`, `session_id`, `sessoes`, `session_traces` em qualquer lugar, **corrigir imediatamente**.

---

## 6. Arquitetura Atual x Arquitetura Alvo

### 6.1 Como está hoje (Fases 1-2)
Simples, direto e voltado a prova de conceito validada:

1. **Captura** – Pega imagem da webcam ou arquivo de vídeo
2. **Detecção** – Identifica corpos com YOLO
3. **Rastreamento** – Acompanha em memória apenas para não contar duas vezes
4. **Zonas** – Verifica se está dentro da região demarcada
5. **Visualização** – Mostra no monitor (overlay) ocupação por zona

**Tudo roda em um único processo. Nada vai para banco.**

### 6.2 Como será no futuro (Fases 3-7)
Evolui sem perder as regras de privacidade:

1. **Múltiplos streams** – Várias câmeras ao mesmo tempo
2. **Fila em memória** – Guarda apenas números agregados
3. **Gravação em lote** – Salva no PostgreSQL fora do processamento do vídeo
4. **API** – Disponibiliza esses números para consulta
5. **Dashboard** – Apresenta de forma visual para gestão
6. **Analytics agregados** – Dwell e heatmap, sempre sem dados individuais

---

## 7. Modelo de Dados: Permitido x Vetado

### 7.1 Permitido
| Tabela | Para que serve | Observação |
|---|---|---|
| `cameras` | Cadastro das câmeras | Dados apenas de configuração |
| `zonas` | Cadastro dos polígonos ROI | Dados apenas de configuração |
| `metricas_fluxo_zona` | Ocupação por zona e janela de tempo | Somente contagens, médias e % de área |
| `dwell_agregado_zona` | Permanência agregada | Somente soma, quantidade, mín/máx e faixas. **Sem por pessoa** |
| `heatmap_densidade_camada` | Densidade por região e tempo | Contadores por quadrícula. **Sem rastro individual** |

### 7.2 Vetado
| Item | Motivo |
|---|---|
| `sessoes`, `session_traces` | Criam "trajeto" da pessoa – proibido pela LGPD |
| `track_id`, `session_id`, `id_rastreio_local` | Identificadores que ligam eventos à mesma pessoa |
| `rota`, `jornada`, `embedding` | Perfil comportamental – proibido |
| Qualquer coluna com dados individuais | Não existe justificativa para isso neste projeto |

---

## 8. Mini-Planejamento Detalhado por Fase (1 a 9)

### FASE 1: Fatia vertical single-câmera (captura, detecção, rastreio efêmero)
**Status:** ✅ CONCLUÍDA | **Duração real:** ~1 dia | **Foco:** Provar que funciona com privacidade desde o início

#### Objetivo
Ter o pipeline rodando em 1 câmera, detectando apenas corpos, com rastreamento efêmero e **zero gravação em disco**.

#### Pré-requisitos
- Ambiente Python configurado (`.venv`)
- Pesos do modelo disponíveis
- Vídeo-amostra para testes

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **1.1** | **Organizar base**: Criar módulos `captura.py` e `overlay.py` com funções simples e diretas. | Técnico | Módulos criados e importam sem erro |
| **1.2** | **Captura**: Garantir que frames venham apenas da webcam/arquivo e tenham timestamp na hora certa. | Técnico | Teste lê pelo menos 1 frame |
| **1.3** | **Detecção**: Configurar YOLO para **somente corpo** (`classes=[0]`). Impedir qualquer menção a face/biometria. | Técnico | Varredura no código não encontra termos proibidos |
| **1.4** | **Rastreamento efêmero**: Usar ByteTrack, mas garantir que IDs sumam ao sair do quadro. | Técnico | Ao sair da imagem, ID não persiste |
| **1.5** | **Overlay**: Desenhar caixas e informações na tela, **sem salvar arquivo algum**. | Técnico | Pasta sem novos arquivos após rodar |
| **1.6** | **Testes de privacidade**: Criar/validar testes que proíbam gravação e uso de face. | Técnico + Qualidade | `test_privacidade.py` passando |
| **1.7** | **Validação visual**: Testar com webcam e com vídeo-amostra olhando na tela. | Equipe | Caixas corretas, sem rostos destacados, sem arquivos gerados |

#### Entregáveis
- `captura.py`, `rastreio.py`, `overlay.py`, `main.py` funcionais
- Testes automatizados da fase
- `01-VERIFICATION.md` aprovado

#### Critérios de Aceite
- [x] Roda com webcam e arquivo
- [x] Só corpos detectados
- [x] Nada em disco
- [x] IDs efêmeros
- [x] Sem face/biometria

---

### FASE 2: Contagem por zona e ocupação em tempo real (ROI-only)
**Status:** ✅ CONCLUÍDA | **Duração real:** ~2 dias | **Foco:** Saber se a ocupação por área está correta

#### Objetivo
Calcular ocupação por zona demarcada, usando **presença + interseção de área**. Tripwire desativado por decisão.

#### Pré-requisitos
- Fase 1 concluída
- Saber demarcar um polígono (pode usar `scripts/demarcar_zona.py`)

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **2.1** | **Planejar zonas**: Definir quais áreas do hotel interessam medir (ex.: recepção, hall). Pensar em "quem conta" nessa área. | Gestão + Operação | Lista de zonas aprovada |
| **2.2** | **Demarcar ROI**: Desenhar polígono por cima da imagem para marcar exatamente a região. Salvar em `config/zonas.yaml`. | Técnico | Polígono fecha corretamente, dentro da imagem |
| **2.3** | **Criar lógica de zonas**: Desenvolver `zona.py` com carregamento, validação e cálculo. | Técnico | Arquivo carrega o YAML sem erro |
| **2.4** | **Cálculo por presença**: Verificar se o "pé" da pessoa está dentro do polígono (mais fiel à perspectiva). | Técnico | Testes com deslocamento batem |
| **2.5** | **Cálculo por interseção de área**: Calcular quanto da área do ROI está coberta pelo "pé/base" da pessoa. | Técnico | Valores coerentes com o que se vê |
| **2.6** | **Estabilizar**: Aplicar regras para evitar piscar (clamp por capacidade, reconciliação ao reiniciar vídeo). | Técnico | Contagem não "pula" sem motivo |
| **2.7** | **Visualizar**: Mostrar ROI, ocupação e % de área no overlay. | Técnico | Fácil de entender na tela |
| **2.8** | **Testes e validação**: Rodar bateria de testes e conferir visualmente com vídeo-amostra. | Técnico + Qualidade | `test_zona.py` 10/10 e `02-VERIFICATION.md` aprovado |

#### Entregáveis
- `config/zonas.yaml` com ROIs válidos
- `zona.py` + integrações com `main.py` e `overlay.py`
- Testes determinísticos
- `02-VERIFICATION.md` aprovado

#### Critérios de Aceite
- [x] Ocupação correta por zona
- [x] Interseção de área funcionando
- [x] Estável
- [x] Tripwire permanece comentado
- [x] Sem violação de privacidade

---

### FASE 3: Persistência PostgreSQL (fila + escrita em lote)
**Status:** ⏳ PENDENTE | **Foco:** Guardar **apenas números agregados** sem travar o vídeo

#### Objetivo
Criar histórico confiável de ocupação/fluxo, mas **nunca** guardar dados individuais. Tudo deve sair do loop de processamento do vídeo.

#### Pré-requisitos
- Fases 1-2 estáveis
- PostgreSQL disponível (pode ser local em `docker` ou ambiente de desenvolvimento)
- Clareza sobre quais métricas vão para o banco

#### 8.3.1 Como será salvo no banco (detalhado)

O grande princípio aqui é: **guardamos estatísticas, não trilhas**. 

##### Fluxo passo a passo

1. **Em memória (volátil)** – Durante o processamento do vídeo, o sistema mantém apenas o `estado` atual por zona (`ocupacao`, `pct_area`, entre outros). **Nenhum histórico por pessoa é acumulado**.
2. **Fechamento por janela** – A cada intervalo definido (sugerido **1 minuto**: `janela_inicio` / `janela_fim`) o sistema calcula os valores agregados daquela janela para cada zona.
3. **Montagem do evento agregado** – Ao invés de salvar 30 frames por segundo, é montado **UM ÚNICO REGISTRO AGREGADO** por `(zona_id, janela_inicio, janela_fim)`. Esse registro contém apenas médias, contagens e percentuais.
4. **Fila em memória** – Esse registro vai para uma **fila em memória** (`Queue`). A fila nunca recebe `track_id`, `session_id`, caixas, coordenadas ou qualquer identificador individual.
5. **Batch Writer (fora do loop)** – Em uma thread/processo separado, o *Batch Writer* lê essa fila em lote (`size-or-time`: ex. 10 registros OU a cada 5 segundos). Somente ele faz chamadas ao PostgreSQL.
6. **Gravação em lote** – Os registros são gravados com `INSERT` em lote. Nunca há `INSERT` dentro do `while True` da captura/detecção/rastreamento.

##### O que será salvo na primeira etapa

Para a Fase 3, o foco inicial é **apenas** a tabela `metricas_fluxo_zona`. Ela deve guardar **somente** informações agregadas.

| Campo | Tipo | Explicação |
|---|---|---|
| `id` | `BIGSERIAL` | Chave primária técnica (não é ID de pessoa) |
| `zona_id` | `INT` (FK para `zonas.id`) | Qual zona gerou essa métrica |
| `janela_inicio` | `TIMESTAMP WITH TIME ZONE` | Início da janela agregada (ex.: 14:00:00) |
| `janela_fim` | `TIMESTAMP WITH TIME ZONE` | Fim da janela agregada (ex.: 14:01:00) |
| `ocupacao_media` | `REAL` | Média da ocupação naquele intervalo (baseado nos frames da janela) |
| `pct_area_media` | `REAL` | Média do percentual de área ocupada (`Área(Objeto) ∩ Área(ROI)`) naquele intervalo |
| `criado_em` | `TIMESTAMP WITH TIME ZONE` | Momento em que esse agregado foi gravado |

**NUNCA** devem existir: `track_id`, `session_id`, `id_rastreio_local`, `camera_track_id`, `rota`, `jornada`, `embedding` ou qualquer coluna que relacione a um indivíduo.

##### Exemplo prático

Imaginando a zona "Recepção" entre 14:00 e 14:01:

| zona_id | janela_inicio | janela_fim | ocupacao_media | pct_area_media | criado_em |
|---|---|---|---|---|---|
| 1 | 2026-10-26 14:00:00-03 | 2026-10-26 14:01:00-03 | 4.2 | 18.7 | 2026-10-26 14:01:02-03 |

Com **apenas essa linha** já conseguimos responder: *"Qual foi a ocupação média da Recepção entre 14:00 e 15:00?"*. **Não conseguimos responder:** *"Quanto tempo ficou aquela pessoa entre 14:00 e 14:01?"*.

##### Regras obrigatórias para o salvamento

- **Por janela, não por frame:** 1 linha por `(zona_id, janela)`. Jamais gravar a cada detecção.
- **Fora do hot-loop:** `SELECT/INSERT/UPDATE/COMMIT` só podem ocorrer na thread do *Batch Writer*. Revisar código para garantir isso.
- **Somente agregados:** Se para montar o dado for necessário guardar um `track_id` para "lembrar", a abordagem está errada. Deve-se agregar e descartar.
- **Idempotente:** Cada lote deve ter um `batch_id` (UUID). Se o *Batch Writer* reiniciar, ele não pode inserir o mesmo lote novamente.
- **Schema enxuto:** Começar com o mínimo necessário. `dwell_agregado_zona` e `heatmap_densidade_camada` ficam para suas respectivas fases, seguindo o mesmo princípio.
- **Testes negativos obrigatórios:** Criar testes que **falhem propositalmente** caso seja tentado gravar `track_id`, criar `sessoes` ou `session_traces`.

##### Regra de ouro para validação

> *"Se for possível reconstituir o trajeto ou o tempo individual de alguém consultando o banco, está errado. Se só for possível obter médias, totais e histogramas por zona/tempo, está correto."*

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **3.1** | **Alinhar modelo**: Revisar `MODELAGEM_BANCO_DE_DADOS.md` e decidir **exatamente** quais colunas vão existir. **Rejeitar** qualquer sugestão de coluna por pessoa. | Técnico + Conformidade | Lista aprovada sem `track_id/session_id` |
| **3.2** | **Criar schema permitido**: Gerar tabelas apenas `cameras`, `zonas`, `metricas_fluxo_zona`. Adicionar `dwell_agregado_zona` e `heatmap_densidade_camada` apenas quando forem realmente usados. | Técnico | `\dt` mostra **somente** tabelas permitidas |
| **3.3** | **Desenhar fila**: Criar uma fila em memória (Python) para acumular **eventos agregados** por janela de tempo (ex.: a cada 1 minuto). | Técnico | Fila só recebe números agregados, nunca IDs |
| **3.4** | **Criar Batch Writer**: Desenvolver um processo/thread separado que lê a fila e grava no banco em lote, **totalmente fora** do `while True`. | Técnico | Escrita acontece fora do hot-loop |
| **3.5** | **Garantir isolamento**: Testar explicitamente que **nenhum `cursor.execute/commit`** acontece dentro do loop principal. | Técnico + Qualidade | Revisão de código aponta 0 chamadas no hot-loop |
| **3.6** | **Idempotência**: Adicionar identificador do lote (`batch_id` UUID) para evitar gravar o mesmo agregado duas vezes em caso de falha/reinício. | Técnico | Teste de reinício não duplica linhas |
| **3.7** | **Testes negativos**: Criar teste que **falhe** se tentar inserir `track_id`, `session_id` ou criar `sessoes`/`session_traces`. | Técnico + Conformidade | Teste falha propositalmente ao simular violação |
| **3.8** | **Validar desempenho**: Rodar pipeline com gravação ativa e conferir FPS/latência. | Técnico | FPS praticamente igual ao sem banco |

#### Entregáveis
- Schema SQL restrito
- Módulo de fila + batch writer
- Configuração de conexão
- Testes de integração e negativos
- Plano de verificação atualizado

#### Critérios de Aceite
- [ ] **Somente** tabelas/agregados permitidos
- [ ] Escrita **fora** do loop de vídeo
- [ ] Latência ≤ 5 ms/frame
- [ ] Sem identificadores por pessoa
- [ ] Idempotente
- [ ] Testes passando

#### Cuidados
- **Nunca** salvar linha por pessoa
- **Nunca** salvar histórico de rastreamento
- Se tiver dúvida se um campo "pode" ir pro banco, **não coloque**. Agregue ao invés.

---

### FASE 4: API FastAPI de métricas e conformidade Marco Civil
**Status:** ⏳ PENDENTE | **Foco:** Disponibilizar números agregados com governança

#### Objetivo
Criar uma API **apenas para consulta** dos dados já agregados, com logs e regras claras.

#### Pré-requisitos
- Fase 3 funcionando (dados agregados no banco)
- Definição de quais consultas a gestão realmente precisa

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **4.1** | **Mapear consultas reais**: Conversar com gestão e listar apenas o que será usado (ocupação por zona, por período, totais). | Gestão + Técnico | Lista enxuta e objetiva |
| **4.2** | **Desenhar rotas**: Criar apenas **GET**. Nada de criar/editar/deletar. | Técnico | Todas as rotas são leitura |
| **4.3** | **Retornar só agregado**: Garantir que JSON nunca traga IDs, nomes de pessoas ou trilhas. | Técnico | Revisão de resposta por rota |
| **4.4** | **Logs de acesso**: Registrar IP, data/hora, rota acessada. Pensar em rotação/expurgo para 6 meses. | Técnico | Log gerado a cada acesso |
| **4.5** | **TTL de métricas**: Documentar por quanto tempo cada tipo fica disponível. Aplicar regra quando definido. | Técnico + Conformidade | Documento de retenção criado |
| **4.6** | **Documentação**: Habilitar Swagger/OpenAPI para facilitar uso pela equipe. | Técnico | `/docs` acessível e claro |
| **4.7** | **Teste prático**: Consumir API com dados reais agregados e validar resposta. | Equipe | Respostas corretas e anonimizadas |

#### Entregáveis
- API FastAPI funcional
- Logs configurados
- Documentação de TTL
- Testes das rotas
- Orientações de uso

#### Critérios de Aceite
- [ ] **Somente leitura**
- [ ] Respostas 100% agregadas
- [ ] Logs de acesso funcionando
- [ ] Retenção 6 meses prevista
- [ ] Nenhum dado individual exposto

---

### FASE 5: Dashboard web de ocupação e séries
**Status:** ⏳ PENDENTE | **Foco:** Mostrar informações úteis para gestão, de forma simples

#### Objetivo
Colocar os números na tela, em tempo real, sem complicação.

#### Pré-requisitos
- API da Fase 4 disponível
- Lista de informações que gestão quer ver no dia a dia

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **5.1** | **Descoberta com gestão**: Perguntar "O que você precisa ver todos os dias ao chegar?". Focar em poucas coisas. | Gestão + Técnico | Lista minimalista aprovada |
| **5.2** | **Prototipar tela**: Desenhar no papel/rascunho: ocupação por zona, status (lotado/ok), horário. | Equipe | Protótipo simples aprovado |
| **5.3** | **Ocupação ao vivo**: Conectar via WebSocket para atualizar sem ficar recarregando página. | Técnico | Números atualizam sozinhos |
| **5.4** | **Séries históricas**: Permitir filtrar por data/período e ver evolução. | Técnico | Gráfico responde ao filtro |
| **5.5** | **Indicador de "atualizado"**: Mostrar "Atualizado há X segundos" para evitar confusão. | Técnico | Indicador visível |
| **5.6** | **Ambiente único**: Montar `docker-compose` para subir tudo junto (banco + API + dashboard). | Técnico | `docker compose up` sobe sem erros |
| **5.7** | **Teste com gestão**: Fazer um "teste prático" mostrando na tela e pedindo ajustes. | Gestão + Equipe | Gestão valida e aprova |

#### Entregáveis
- Dashboard funcional
- `docker-compose.yml`
- Manual rápido de uso
- Telas validadas com gestão

#### Critérios de Aceite
- [ ] Ocupação ao vivo por zona
- [ ] Filtro por período
- [ ] Indicador de frescor
- [ ] Sobe com `docker-compose`
- [ ] Simples de usar
- [ ] Só mostra dados agregados

---

### FASE 6: Multi-câmera RTSP com reconexão e watchdog
**Status:** ⏳ PENDENTE | **Foco:** Escalar sem perder estabilidade e sem cruzar câmeras

#### Objetivo
Processar várias câmeras ao mesmo tempo, com recuperação automática em caso de queda.

#### Pré-requisitos
- Fases 3-5 estáveis
- Acesso a stream RTSP de teste (pode ser `MediaMTX` local)
- Entendimento claro de "uma câmera = um tracker"

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **6.1** | **Mapear câmeras**: Listar quais câmeras farão parte e quais zonas cada uma cobre. **Nunca** compartilhar IDs entre elas. | Operação + Técnico | Mapa claro por câmera |
| **6.2** | **Trocar para ingestão robusta**: Migrar captura RTSP para abordagem mais estável (`PyAV`) ao invés de depender apenas do `cv2.VideoCapture`. | Técnico | Conecta em RTSP de teste |
| **6.3** | **Processar em paralelo**: Criar um "worker" por câmera. Cada um com seu próprio tracker. | Técnico | Rodar 2 câmeras simultâneas sem travar |
| **6.4** | **Reconexão**: Implementar reconexão com backoff exponencial ao perder stream. | Técnico | Derrubar stream e ver reconectar sozinho |
| **6.5** | **Watchdog**: Criar vigia que percebe se não chega frame novo há X segundos e aciona reconexão. | Técnico | Simular "stream congelado" → reconecta |
| **6.6** | **Isolar totalmente**: Garantir que contadores, trackers e zonas **não** se misturam entre câmeras. | Técnico + Conformidade | Teste com 2 câmeras mostra contagens independentes |
| **6.7** | **Teste prático**: Simular queda/reconexão várias vezes e conferir se ocupação fica coerente. | Equipe | Sem contagem corrompida |

#### Entregáveis
- Suporte multi-câmera
- Mecanismo de reconexão + watchdog
- Configuração por câmera
- Relatório de teste de queda/reconexão

#### Critérios de Aceite
- [ ] Várias câmeras rodando juntas
- [ ] Reconexão automática funciona
- [ ] Watchdog funciona
- [ ] **Sem cruzamento** entre câmeras
- [ ] Contagens permanecem coerentes
- [ ] Sem violação de privacidade

#### Alerta
**NUNCA** implemente "ligar" pessoa entre câmeras. Se surgir essa ideia, **descartar** imediatamente.

---

### FASE 7: Analytics de permanência e heatmap agregado
**Status:** ⏳ PENDENTE | **Foco:** Insights agregados sem traçar pessoas

#### Objetivo
Saber tempo médio por zona e onde há maior concentração, **somente em forma agrupada**.

#### Pré-requisitos
- Fases 3-6 estáveis
- Entendimento exato do que "agregado" significa (nunca por indivíduo)

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **7.1** | **Definir regras de "permanência"**: Decidir quando começa/termina a contagem (entra na zona / sai da zona / some do quadro). Também pensar em "saiu sem sair direito". | Gestão + Técnico | Regras claras e escritas |
| **7.2** | **Calcular em RAM**: Marcar entrada ao entrar na zona. Ao sair ou ao "sumir", calcular duração **naquele momento** e jogar no acumulador da janela. **Apagar** esse dado individual imediatamente. | Técnico | Dado individual some após agregado |
| **7.3** | **Agregar por janela**: Agrupar por zona + intervalo de tempo. Guardar apenas: quantidade, soma de segundos, mínimo, máximo e **faixas** (0-2, 2-5, 5-15, 15+ min). | Técnico | Banco tem **apenas** essas colunas |
| **7.4** | **Heatmap por grade**: Dividir a imagem em quadradinhos (grade). A cada vez que houver presença efêmera, somar +1 naquele quadradinho da janela. **Nunca guardar histórico por pessoa**. | Técnico | Heatmap mostra "áreas mais movimentadas", não "trajeto" |
| **7.5** | **Fechar sessões zumbis**: Se alguém "sumir" por muito tempo sem sair formalmente, fechar com critério definido para não inflar tempo. | Técnico | Evita tempos absurdos |
| **7.6** | **Exibir no dashboard**: Criar gráfico de faixas de permanência e visualizar heatmap agregado. | Técnico + Gestão | Fácil de interpretar |
| **7.7** | **Auditoria rigorosa**: Conferir schema linha a linha. Tentar imaginar "como descobrir tempo da pessoa X" → **deve ser impossível**. | Conformidade + Técnico | Impossível reconstituir indivíduo |

#### Entregáveis
- Lógica de dwell agregada
- Heatmap agregado
- Tabelas `dwell_agregado_zona` e `heatmap_densidade_camada`
- Telas no dashboard
- Teste prático comprovando anonimato

#### Critérios de Aceite
- [ ] Só agregados no banco
- [ ] Heatmap sem traço individual
- [ ] Faixas corretas
- [ ] Impossível identificar pessoa
- [ ] Visual claro para gestão
- [ ] Sem `track_id/session_id` persistidos

---

### FASE 8: Validação de qualidade, carga e acurácia
**Status:** ⏳ PENDENTE | **Foco:** Provar que está confiável antes da auditoria formal

#### Objetivo
Garantir que os números batem com a realidade e que o sistema aguenta o dia a dia.

#### Pré-requisitos
- Fases 1-7 integradas
- Vídeos com movimento real para testar
- Alguém disponível para fazer contagem manual

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **8.1** | **Definir "quem conta"**: Escrever por extenso. Ex.: "Conta clientes/pessoas em circulação. Funcionários em serviço? Definir claramente". Colocar em documento. | Gestão + Operação | Regra escrita e aprovada |
| **8.2** | **Testes automatizados**: Revisar toda a suíte. Garantir que cobre regras críticas (ROI, interseção, fila, reconexão). | Técnico + Qualidade | `pytest` 100% verde |
| **8.3** | **Contagem manual**: Escolher trecho de vídeo com movimento mais intenso (pico). Alguém conta "na mão" quantas pessoas entram/ficam. Comparar com sistema. | Operação + Técnico | Planilha com comparação lado a lado |
| **8.4** | **Calcular acurácia**: Ver diferença por zona. Anotar acertos, pequenas diferenças e motivos (oclusão, perspectiva). | Equipe | Relatório simples com números |
| **8.5** | **Testes de resiliência**: Simular queda de banco, fila cheia, câmera cair/reconectar, reiniciar API. | Técnico | Sistema se recupera sem travar |
| **8.6** | **Testes de carga leve**: Rodar com 2-3 câmeras ao mesmo tempo e observar estabilidade. | Técnico | Sem lentidão crítica |
| **8.7** | **Ajustes finos**: Corrigir apenas o necessário com base nos achados. Não inventar funcionalidade nova. | Técnico | Melhorias validadas |
| **8.8** | **Fechamento**: Gerar "Relatório de Validação e Acurácia" com dados reais. | Equipe | Relatório pronto para seguir à Fase 9 |

#### Entregáveis
- Definição escrita de "quem conta"
- Suíte de testes revisada
- Planilha de comparação manual x sistema
- Relatório de acurácia
- Relatório de resiliência/carga
- Correções aplicadas e validadas

#### Critérios de Aceite
- [ ] Testes automatizados passando
- [ ] Comparação manual feita e documentada
- [ ] Acurácia aceitável com justificativas
- [ ] Resiliência testada
- [ ] Tudo rastreável

---

### FASE 9: Conformidade LGPD e preparação para produção
**Status:** ⏳ PENDENTE | **Foco:** Gate obrigatório antes de ligar com hóspedes reais

#### Objetivo
Formalizar tudo que foi feito por design e ter documentos prontos para auditoria interna/gestão.

#### Pré-requisitos
- Fases 1-8 concluídas e validadas
- Relatórios da Fase 8 prontos
- Nome do Encarregado (DPO) definido

#### Passo a passo detalhado
| Passo | Ação | Responsável | Verificação |
|---|---|---|---|
| **9.1** | **Auditoria automatizada**: Rodar varredura por termos proibidos. Conferir schema do banco. Conferir se há arquivo em disco sendo criado. | Técnico + Conformidade | Zero ocorrências proibidas |
| **9.2** | **RIPD**: Preencher Relatório de Impacto à Proteção de Dados descrevendo finalidade, minimização, riscos e medidas. | Jurídico/Conformidade + Técnico | RIPD revisado e assinado |
| **9.3** | **LIA**: Fazer Avaliação de Interesse Legítimo (art. 10 §3º). Deixar claro por que não há consentimento e por que é necessário. | Jurídico/Conformidade | LIA completo |
| **9.4** | **ROPA**: Montar Registro das Operações. Listar: quem faz, para que, por quanto tempo, com que medidas. | Conformidade + Técnico | ROPA atualizado |
| **9.5** | **Aviso de monitoramento**: Definir texto e locais para placas nas áreas monitoradas. | Operação + Jurídico | Placas definidas/aprovadas |
| **9.6** | **Encarregado (DPO)**: Indicar nome, e-mail/telefone e publicar canal de contato. | Gestão | Canal divulgado |
| **9.7** | **Plano de resposta a incidente**: Criar passo a passo: como identificar, quem aciona, como comunicar à ANPD/titulares se aplicável. | TI + Conformidade + Gestão | Plano lido e aprovado por todos |
| **9.8** | **Checklist final**: Revisar **todos** os pontos com equipe. Fazer "teste cego": tentar encontrar dado por pessoa → impossível. | Todos | Checklist 100% marcado |
| **9.9** | **Gate de liberação**: Somente após **TODOS** aprovados, autorizar ligação de streams reais com hóspedes. | Gestão + Conformidade | Autorização formal registrada |

#### Entregáveis
- Relatório de auditoria (PRV-01)
- RIPD, LIA, ROPA
- Aviso de monitoramento
- Dados do Encarregado
- Plano de resposta a incidente
- Ata/registro do gate de liberação

#### Critérios de Aceite (OBRIGATÓRIOS)
- [ ] **Auditoria passa sem achados críticos**
- [ ] RIPD, LIA e ROPA revisados e aprovados
- [ ] Aviso afixado e Encarregado definido
- [ ] Plano de incidente pronto
- [ ] Teste "impossível identificar pessoa" confirmado
- [ ] **Parecer favorável para produção**
- [ ] **Autorização formal da gestão**

**IMPORTANTE:** **Nenhuma câmera real com hóspedes pode ser ligada antes deste gate ser concluído e aprovado.**

---

## 9. Cronograma Sugerido por Ordem

| Ordem | Fase | Situação | Observação |
|---|---|---|---|
| **1º** | Fase 1 | ✅ Concluída | Base e privacidade |
| **2º** | Fase 2 | ✅ Concluída | ROI + interseção de área |
| **3º** | Fase 3 | ⏳ Próxima | Banco + fila + escrita em lote |
| **4º** | Fase 4 | ⏳ A seguir | API + logs + Marco Civil |
| **5º** | Fase 5 | ⏳ A seguir | Dashboard para gestão |
| **6º** | Fase 6 | ⏳ A seguir | Multi-câmera + reconexão |
| **7º** | Fase 7 | ⏳ A seguir | Dwell + heatmap agregados |
| **8º** | Fase 8 | ⏳ A seguir | Validação, acurácia e resiliência |
| **9º** | Fase 9 | ⏳ Final | Auditoria LGPD + Gate de produção |

> **Regra prática:** Não pule fases. Cada uma valida o alicerce da próxima. Fases 1-2 já provaram que esse caminho funciona.

---

## 10. Testes, Verificações e Controle

| Ferramenta | Quando usar | Objetivo |
|---|---|---|
| **`pytest`** | Sempre após alteração no código | Garantir que nada quebrou. Hoje: **33/33 verdes** |
| **`gsd-verifier`** | Ao finalizar cada fase | Verificação objetiva "goal-backward". Gera `VERIFICATION.md` |
| **Testes de privacidade** | Em qualquer mudança | Barrar face, biometria ou gravação em disco |
| **Teste manual visual** | Ao mexer em zonas/overlay | Conferir com os próprios olhos se faz sentido |
| **Comparação manual x sistema** | Fase 8 | Validar acurácia com números reais |
| **Auditoria por grep** | Fase 9 | Procurar termos proibidos no repositório |

---

## 11. Dicas Práticas para Execução

- **"Agregue, não grave":** Sempre que pensar em salvar algo por pessoa, pense em somar num contador.
- **Mantenha simples:** Se explicar a fase para alguém não-técnico e não entender, simplifique.
- **Privacidade em primeiro lugar:** Melhor perder 1 hora questionando, que ter problema depois.
- **Teste pequeno:** Valide com 1 zona primeiro. Depois expande.
- **Documente decisões:** Anotar "por que foi feito assim" evita voltar atrás sem motivo.
- **Foque em gestão:** Dashboard não precisa ser bonito. Precisa ser **útil e claro**.
- **Respeite o gate:** Fase 9 **não é burocracia**. É proteção para empresa, equipe e pessoas.
- **Use o GSD:** `gsd-discuss-phase` e `gsd-plan-phase` ajudam muito a manter o planejamento organizado.

---

## 12. Referências

| Documento | Caminho | Finalidade |
|---|---|---|
| **Roadmap** | `.planning/ROADMAP.md` | Visão macro das fases |
| **Requisitos** | `.planning/REQUIREMENTS.md` | Lista completa com rastreabilidade |
| **Projeto** | `.planning/PROJECT.md` | Objetivo, decisões e escopo |
| **Estado** | `.planning/STATE.md` | Posição atual |
| **Plano Completo** | `.planning/context/PLANO_V1_COMPLETO.md` | Detalhamento unificado |
| **Parecer LGPD/Marco Civil** | `.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md` | Base jurídica |
| **Modelagem BD** | `.planning/context/MODELAGEM_BANCO_DE_DADOS.md` | Permitido x Vetado |
| **Diretrizes para Agente IA** | `.planning/context/DIRETRIZES_PARA_AGENTE_IA.md` | Regras obrigatórias |
| **Verificações GSD** | `.planning/phases/*/0*-VERIFICATION.md` | Provas de conclusão |
| **Relatórios LGPD** | `docs/relatorios/` | Documentos para gestão |

---

## 13. Anexos

### Anexo A: Comandos Úteis
```bash
# Rodar testes
./.venv/bin/python -m pytest

# Rodar pipeline com vídeo-amostra
./.venv/bin/python main.py test/gemini_generated_video_8d21d35f.mp4

# Ver zonas sem rodar vídeo
./.venv/bin/python entender_zonas.py

# Demarcar ROI interativo
./.venv/bin/python scripts/demarcar_zona.py 0 --camera camera_0 --zona nome_da_zona
```

### Anexo B: Checklist Rápido Antes de Seguir para Próxima Fase
- [ ] Todos os testes verdes
- [ ] Objetivo da fase alcançado (conferir com critérios)
- [ ] Sem arquivos em disco gerados indevidamente
- [ ] Sem dados por pessoa
- [ ] Sem tabelas/colunas vetadas
- [ ] Verificação GSD aprovada (`VERIFICATION.md`)
- [ ] Documentação atualizada
- [ ] Equipe alinhada

### Anexo C: Mensagem-chave
> **"O sucesso deste projeto não é 'rastrear todo mundo', é entregar números confiáveis sem saber quem são."**

**Documento pronto para revisão da equipe e gestão. Após validação, gero a versão em PDF.**
