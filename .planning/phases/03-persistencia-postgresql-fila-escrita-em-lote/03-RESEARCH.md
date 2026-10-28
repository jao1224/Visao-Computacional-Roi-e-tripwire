# Phase 3: Persistência PostgreSQL (fila + escrita em lote) — Pesquisa

Pesquisa feita em 2026-10-28 consultando a documentação oficial (psycopg2 e PostgreSQL) e o
estado do próprio repositório. Cada achado abaixo tem consequência direta no código.

## 1. Concorrência no psycopg2 (fonte: psycopg2 `usage.rst`)

> "The Psycopg module and the `connection` objects are thread-safe: many threads can access the
> same database either using separate sessions and creating a `connection` per thread or using the
> same connection and creating separate `cursor`s."

- psycopg2 é **level 2 thread-safe**, mas a recomendação é **uma conexão por thread**.
- Consequência: o `BatchWriter` mantém **uma conexão própria e persistente** em vez de abrir uma
  conexão nova a cada lote (evita handshake a cada janela e torna o retry barato).
- Consequência 2: a conexão **não é compartilhada** com o `main` nem com o seed.

## 2. Transação abortada inutiliza a conexão (fonte: psycopg2 `connection.rst`)

Depois de um erro dentro de uma transação, a conexão entra em estado "aborted" e todo comando
seguinte falha até um `rollback`. Se o erro foi de rede/`OperationalError`, a conexão está morta.

- Consequência: no `except`, o writer faz `rollback` implícito via **descarte da conexão**
  (`close` + `None`), forçando reconexão na próxima tentativa. Sem isso, o retry repetiria o mesmo
  erro indefinidamente — foi o motivo de não usar `With connection` block no retry.

## 3. `ON CONFLICT` exige árbitro único (fonte: PostgreSQL `sql-insert.html`)

> "The optional `ON CONFLICT` clause specifies an alternative action to raising a unique violation
> or exclusion constraint violation error. [...] `ON CONFLICT DO NOTHING` simply avoids inserting a row."

- Com `conflict_target` explícito, só aquele índice é usado como árbitro — conflitos em **outros**
  `UNIQUE` continuam levantando erro. Por isso o `conflict_target` é
  `(zona_id, janela_inicio, janela_fim)`, exatamente o `uq_metricas_zona_janela`.
- `DO NOTHING` é o correto aqui: a janela já gravada é idêntica (mesmos agregados), então
  reentrega de lote é no-op — idempotência sem `DO UPDATE`.

## 4. Inserção em lote

- `execute_values` (psycopg2) monta um único `INSERT ... VALUES (...), (...)` — 1 round-trip por lote.
- Alternativa `COPY` é mais rápida, mas não suporta `ON CONFLICT`, então não serve para idempotência.

## 5. Retry e contenção de memória

- Backoff exponencial evita martelar um banco que está subindo (0,5 s → 1 → 2 → 4 ... teto 30 s).
- Fila de retry **limitada** (1000 eventos) protege a RAM: uma queda longa do banco não pode
  crescer indefinidamente dentro do processo de vídeo. Ao encher, descarta os mais antigos e avisa.

## 6. `unnest` para resolver códigos de zona

- `SELECT codigo_zona, id FROM zonas WHERE codigo_zona = ANY(%s)` resolve os códigos do YAML para
  a FK numérica em **uma** query por lote (sem N+1).
- O cadastro é responsabilidade do seed (`db/seed.py`), não do writer — decisão de 2026-10-28.

## 7. Estado do repositório

- Fases 1–2: privacidade-first, sem gravação de mídia, código em pt-BR, testes pytest com vídeo-amostra.
- `.planning/context/MODELAGEM_BANCO_DE_DADOS.md` §2.1/§2.2 define as tabelas permitidas.
- Não havia base de dados nem seed: a FK `zona_id INT` não teria como ser satisfeita com IDs de texto.

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Bloquear o loop de vídeo | Nenhum SQL no `while`; só `list.append` e `queue.put` |
| Duplicar linhas em reinício | `UNIQUE` + `ON CONFLICT DO NOTHING` |
| Repetir erro para sempre após falha | Descartar conexão no erro (item 2) |
| Crescer RAM sem limite com banco fora | Fila de retry limitada com descarte dos mais antigos |
| Gravar zona inexistente / criar cadastro fantasma | Seed explícito + writer ignora zona desconhecida com aviso |
| Violação de LGPD | Grep automatizado + testes negativos de schema e de fila |

## Referências

- psycopg2 docs — Thread and process safety: https://www.psycopg.org/docs/usage.html
- psycopg2 docs — Connection classes / pool: https://www.psycopg.org/docs/connection.html
- PostgreSQL docs — INSERT / ON CONFLICT: https://www.postgresql.org/docs/current/sql-insert.html
- PostgreSQL docs — INSERT ... ON CONFLICT (índice de árbitro): https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT
- `.planning/context/MODELAGEM_BANCO_DE_DADOS.md`
- `.planning/ROADMAP.md` (Fase 3) / `.planning/REQUIREMENTS.md` (API-01, QUA-01)
- `.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md`
