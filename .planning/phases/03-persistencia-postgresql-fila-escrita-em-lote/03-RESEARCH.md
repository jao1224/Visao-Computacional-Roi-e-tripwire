# Phase 3: Persistência PostgreSQL (fila + escrita em lote) — Pesquisa

## Padrões relevantes no repo
- **Fases 1-2:** Privacidade-first (sem gravação em disco, sem IDs persistidos). Código em pt-BR.
- **Schema:** `.planning/context/MODELAGEM_BANCO_DE_DADOS.md` define apenas `cameras`, `zonas`, `metricas_fluxo_zona` + futuros agregados.
- **ROADMAP/REQUIREMENTS:** API-01, QUA-01.

## Decisões técnicas
- **Fila:** `queue.Queue` (thread-safe). Produtor não bloqueia o loop.
- **Batch writer:** `threading.Thread(daemon=True)` ou `asyncio` + executor. Thread mais simples e compatível com `psycopg2`.
- **Conexão:** Pool simples (`psycopg2.pool.ThreadedConnectionPool`) ou conexão por lote com `with conn:` e transação.
- **Janela temporal:** Agregar por `janela_inicio/janela_fim` (ex. 1 minuto). Fechar janela ao passar do limite.
- **Idempotência:** Gerar `batch_id = uuid.uuid4()` por lote. Opcionalmente tabela `batch_log` (apenas se necessário) — mas evitar tabelas vetadas. Alternativa: chave única `(zona_id, janela_inicio, janela_fim)` para prevenir duplicados.
- **Métricas iniciais:** `ocupacao_media`, `pct_area_media` (já calculados em `zona.py`).
- **Isolamento:** Módulo `persistencia/` ou `db/` com `fila.py`, `batch_writer.py`, `schema.sql`. Nunca importar/use SQL no `main.py` dentro do hot-path.

## Riscos e mitigações
- **Bloquear loop:** Nunca `commit` síncrono no loop → usar fila.
- **Duplicados:** Chave única + idempotência por lote.
- **Violação LGPD:** Grep automatizado + testes negativos.
- **Conexão caída:** Reconexão com backoff no batch writer.

## Referências
- `.planning/context/MODELAGEM_BANCO_DE_DADOS.md`
- `.planning/ROADMAP.md` (Fase 3)
- `.planning/REQUIREMENTS.md` (API-01, QUA-01)
- `.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md`
