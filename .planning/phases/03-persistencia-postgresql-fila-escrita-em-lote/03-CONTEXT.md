# Phase 3: Persistência PostgreSQL (fila + escrita em lote) — Contexto

**Goal:** Eventos agregados ganham verdade durável no PostgreSQL sem nunca tocar o loop de vídeo — fila em memória + batch writer idempotente, schema apenas de configuração e métricas agregadas.

**Depends on:** Phase 2 (concluída)
**Requirements:** API-01, QUA-01

## Decisões-chave (vinculantes)
- **ROI-only / saída agregada:** Nunca persistir dados por-pessoa. Sem `track_id`, `session_id`, `session_traces`, `sessoes`, rotas/jornadas/embeddings.
- **Schema permitido:** `cameras`, `zonas`, `metricas_fluxo_zona`. Futuramente `dwell_agregado_zona`, `heatmap_densidade_camada` apenas quando usados.
- **Gravação por janela:** 1 linha por `(zona_id, janela_inicio, janela_fim)`. Não gravar por frame.
- **Fora do hot-loop:** Nenhuma operação SQL (`execute/commit`) dentro do `while True`. Usar fila em memória + *batch writer* em thread separada.
- **Idempotência:** Cada lote com `batch_id` (UUID). Evitar duplicados em reinício.
- **Latência:** Loop ≤ 5 ms/frame mesmo com escrita ativa.
- **Testes negativos:** Deve falhar se tentar inserir `track_id`/criar tabelas vetadas.

## Arquitetura-alvo
1. **Produtor (main/worker de vídeo):** Ao fechar janela, monta evento **agregado** (apenas números) e enfileira.
2. **Fila em memória:** `queue.Queue` com eventos agregados. Nunca recebe IDs individuais.
3. **Batch Writer:** Thread dedicada. Consome em lote (`size-or-time`), `executemany`/transação, commit fora do loop.
4. **PostgreSQL:** Schema conforme `MODELAGEM_BANCO_DE_DADOS.md` §2.1.

## Estrutura alvo (inicial)
`metricas_fluxo_zona(id, zona_id, janela_inicio, janela_fim, ocupacao_media, pct_area_media, criado_em)`

## Verificações obrigatórias
- `\dt` mostra apenas tabelas permitidas
- Grep no código: sem `cursor.execute`/`conn.commit` no caminho do loop de vídeo
- Testes negativos passam (falham ao violar)
- FPS/latência estáveis com escrita ativa
