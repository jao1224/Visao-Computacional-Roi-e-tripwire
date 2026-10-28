# Relatório – Fase 3: Persistência PostgreSQL (Fila + Escrita em Lote)

**Data:** 27/10/2026  
**Projeto:** Visão Computacional para Hotelaria (Analytics de Fluxo)  
**Branch:** docs/refatoracao-organizacao-documentacao  
**Status:** Base implementada e validada em PostgreSQL 16 (schema aplicado, gravação idempotente confirmada)

---

## 1. Objetivo da Fase 3

Implementar a persistência **apenas de dados agregados** no PostgreSQL, garantindo que **nenhum dado individual** seja gravado. Toda a escrita no banco será feita **fora do loop de processamento de vídeo**, utilizando uma fila em memória e um *Batch Writer* dedicado.

O objetivo é ter um histórico confiável de ocupação, pronto para alimentar a API e o Dashboard, sem comprometer o desempenho ou a conformidade com a LGPD.

---

## 2. Princípio: "Só números, nunca trilhas"

A regra fundamental adotada é simples:

> *"Se for possível reconstituir o trajeto ou o tempo individual de uma pessoa consultando o banco, está errado. Se só for possível obter médias, contagens, histogramas e dados agregados por zona/tempo, está correto."*

Para garantir isso, seguimos rigorosamente os seguintes pontos:

- **Sem rastreamento persistente:** Não serão gravados `track_id`, `session_id`, rotas, jornadas ou qualquer identificador individual.
- **Agregação por janela:** Ao invés de gravar 30 frames por segundo, gravamos **1 linha agregada por zona por janela de tempo** (sugerido: 1 minuto).
- **Descartar individualmente:** Todos os dados efêmeros existentes em memória durante o processamento são agregados e descartados imediatamente após o fechamento da janela.
- **Zero associação entre câmeras:** Mantido o isolamento intra-câmera já existente nas fases anteriores.

---

## 3. Modelagem do Banco de Dados

Foi criada a estrutura em `db/schema.sql`, estritamente restrita a **configuração e métricas agregadas**.

### Tabelas criadas

| Tabela | Finalidade | Observação |
|---|---|---|
| **`cameras`** | Cadastro de câmeras | Configuração do sistema. |
| **`zonas`** | Cadastro de Regiões de Interesse (ROI) | Armazena polígonos em formato JSONB. |
| **`metricas_fluxo_zona`** | Ocupação agregada por zona x janela | Guarda `ocupacao_media` e `pct_area_media`. **Apenas números.** |
| **`heatmap_densidade_camada`** | Mapa de calor agregado por quadrante/célula x janela | **Implementada nesta fase.** Uma linha por `(camera_id, janela_inicio, janela_fim, grade_x, grade_y)` com `contador`. Permite gerar o heatmap de densidade sem gravar trilha individual ou posições por pessoa. |
| **`dwell_agregado_zona`** | Tempo de permanência agregado por zona x janela | Guarda `n_permanencias`, `soma_segundos`, `min_segundos`, `max_segundos` e `histograma` por faixas (0-2, 2-5, 5-15, 15+ min). |

### Tabelas vetadas (proibidas)

As seguintes tabelas **não serão criadas**, em conformidade com a LGPD e com a decisão do projeto:

- `sessoes`
- `session_traces`

Também estão **proibidas** as colunas: `track_id`, `session_id`, `id_rastreio_local`, `embedding`, `rota`, `jornada`.

### Medidas de segurança na modelagem

- **Chave única por agregação:** `UNIQUE` por `(zona_id, janela_inicio, janela_fim)` ou `(camera_id, janela_inicio, janela_fim, grade_x, grade_y)` nas tabelas agregadas. Garante idempotência e evita duplicados.
- **Chaves estrangeiras:** Relacionamento correto entre `cameras/zonas` sem expor dados pessoais.
- **Índices otimizados:** Para consultas rápidas por zona/câmera e por intervalo de tempo.
- **Heatmap por quadrantes:** Ao invés de gravar um array por linha, optou-se por **uma linha por célula da grade** (`grade_x`, `grade_y`). Essa abordagem é mais performática, normalizada e permite filtrar/gerar o heatmap sem qualquer dado individual.
- **Auditoria automatizada:** Criado o teste `tests/test_db_schema_privacidade.py`, que **falha automaticamente** caso alguma tabela ou coluna vetada seja adicionada por engano.

---

## 4. Arquitetura: Fila + Batch Writer (fora do loop de vídeo)

A grande preocupação da Fase 3 é **não degradar o desempenho** do processamento de vídeo. Por isso, adotamos o isolamento total entre o *hot-loop* e o banco de dados.

### Fluxo implementado

| Etapa | Descrição |
|---|---|
| **1. Processamento em tempo real** | O pipeline (`main.py`) continua calculando ocupação e interseção de área por zona, exatamente como nas fases 1 e 2. |
| **2. Acumulação em RAM** | Durante a janela de tempo (1 minuto), os valores são acumulados em memória pelo módulo `persistencia/agregador.py`. |
| **3. Fechamento da janela** | Ao final do intervalo, são calculadas apenas as **médias agregadas**. Nenhum dado individual é mantido. |
| **4. Enfileiramento** | O evento **100% agregado** é enviado para uma fila em memória (`persistencia/fila.py`). |
| **5. Batch Writer (thread separada)** | Em segundo plano, `persistencia/batch_writer.py` consome essa fila em lote e grava no PostgreSQL. |
| **6. Gravação em lote** | Utiliza transação única por lote, com `INSERT ... ON CONFLICT DO NOTHING` para garantir idempotência. |

### Requisitos atendidos

- **Desempenho:** Nenhuma chamada SQL ocorre dentro do `while True` do processamento de vídeo — o loop só acumula números em RAM e enfileira. Medição do trecho adicionado ao loop: **~0,002 ms/frame** com 5 zonas, muito abaixo da meta de 5 ms/frame. Toda a latência de banco fica na thread escritora.
- **Idempotência:** Cada lote recebe um `batch_id` único (UUID) e as tabelas agregadas têm `UNIQUE`; reentregar o mesmo lote não duplica linhas (validado: 2 linhas após gravar o mesmo lote duas vezes).
- **Robustez:** O *Batch Writer* roda em thread *daemon*, abre conexão por lote e erros de banco não derrubam o processamento de vídeo.
- **Privacidade por construção:** A fila valida e **rejeita** qualquer evento que contenha chaves vetadas (`track_id`, `session_id`, etc.).

---

## 5. Conformidade com LGPD e Marco Civil

| Dispositivo | Aplicação |
|---|---|
| **LGPD art. 6º III (Minimização)** | Coletamos apenas o estritamente necessário: médias por zona e por janela. |
| **LGPD art. 11 (Dados sensíveis)** | **Proibido** expressamente. Não há face, biometria, demografia ou emoção. |
| **LGPD art. 12 (Anonimização)** | Dados persistidos são **anônimos irreversíveis**. Não existem meios razoáveis de reidentificação a partir das tabelas criadas. |
| **LGPD art. 37 (ROPA)** | Mapeamento das operações já documentado. |
| **LGPD art. 46 (Segurança)** | Acesso restrito ao banco, credenciais via variáveis de ambiente, isolamento do *hot-loop* e auditoria automatizada. |
| **Marco Civil da Internet art. 15** | Base para os logs de acesso da API, que serão implementados na Fase 4 (retenção por 6 meses). |
| **LGPD art. 52** | Risco mitigado pelo desenho de privacidade por construção. |

---

## 6. Status Atual e Próximos Passos

### Concluído nesta etapa

- [x] Modelagem validada e atualizada em `db/schema.sql`
- [x] Inclusão das tabelas `heatmap_densidade_camada` e `dwell_agregado_zona` para evitar migrações futuras
- [x] Implementação da fila, agregador e *batch writer* fora do *hot-loop*
- [x] Integração no pipeline (`main.py`): acumula por janela de 1 minuto e enfileira; nenhuma consulta SQL no loop
- [x] Testes negativos de privacidade e de isolamento aprovados (49 testes verdes na suíte)
- [x] Documentação atualizada no plano mestre do projeto
- [x] Schema aplicado em PostgreSQL 16 e gravação real validada (inclusive reentrega do mesmo lote sem duplicar)
- [x] Latência do trecho de persistência no loop medida em ~0,002 ms/frame com 5 zonas

### Próximos passos (Fase 4)

- **API FastAPI somente-leitura:** Criar endpoints para consulta das métricas agregadas
- **Logs de acesso:** Implementar registro com retenção por 6 meses (conforme Marco Civil)
- **Política de TTL:** Definir e aplicar expurgo automático conforme necessidade de minimização
- **Integração com Dashboard:** Preparar base para visualização em tempo real

---

## 7. Conclusão

A Fase 3 estabelece a base sólida para o histórico do sistema, **sem abrir mão da privacidade**. Com a separação entre processamento em tempo real e escrita assíncrona, garantimos desempenho, escalabilidade e conformidade com a LGPD.

O grande diferencial deste projeto continua sendo claro: **transformamos câmeras em sensores de negócio, sem transformar hóspedes em perfis identificáveis.**

**Fase 3 concluída no escopo técnico. Próximo passo: Fase 4 (API FastAPI somente-leitura + retenção e logs de acesso).**
