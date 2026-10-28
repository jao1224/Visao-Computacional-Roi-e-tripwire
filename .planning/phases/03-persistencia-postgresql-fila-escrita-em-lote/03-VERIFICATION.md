# Phase 3 — Verificação (goal-backward)

**Data:** 2026-10-28
**Ambiente:** Ubuntu, Python 3.14 (`.venv`), PostgreSQL 16 em container descartável
**Método:** cada critério de sucesso do ROADMAP foi confrontado com evidência executável
(teste automatizado, comando reproduzível ou medição), não com inspeção visual.

## Critérios de sucesso

| # | Critério (ROADMAP) | Evidência | Veredito |
|---|---|---|---|
| 1 | Eventos chegam ao PostgreSQL via fila em lote (size-or-time) e nenhuma operação de banco acontece no loop de vídeo | `tests/test_fila_batch_privacidade.py::test_hot_path_sem_sql` (grepa `psycopg2`, `cursor`, `.execute(`, `commit(`, `execute_values` em `main.py`/`zona.py`); `_coletar()` fecha por `batch_size` **ou** `flush_interval`; UAT passo [1] | PASS |
| 2 | Banco contém apenas configuração e métricas agregadas; sem tabela/coluna por-pessoa | `tests/test_db_schema_privacidade.py` (falha se `sessoes`/`session_traces` ou colunas vetadas aparecerem); `\dt` no PostgreSQL real mostra só `cameras`, `zonas`, `metricas_fluxo_zona`, `heatmap_densidade_camada`, `dwell_agregado_zona` | PASS |
| 3 | Latência do loop ≤ 5 ms/frame com o escritor ativo | Medição do trecho adicionado ao loop: **0,0018 ms/frame** com 5 zonas (20.000 frames); SQL roda em outra thread. Medição do pipeline completo em GPU continua na Fase 8 | PASS (I/O fora do loop) |
| 4 | Reentregar um lote não duplica contagens | UAT: mesmo lote gravado 2× → `SELECT count(*)` = 1; `UNIQUE (zona_id, janela_inicio, janela_fim)` + `ON CONFLICT DO NOTHING`; teste de integração `DB_TESTE=1` | PASS |

## Decisões confirmadas com o usuário

| Decisão | Verificação | Veredito |
|---|---|---|
| Retry com fila limitada quando o banco cai | UAT passos [2]–[4]: banco parado → 1 evento retido e nada gravado; banco volta → evento gravado e fila drenada | PASS |
| Seed explícito (writer não cria zona) | `db/seed.py` + teste `test_seed_le_zonas_do_yaml`; `test_writer_ignora_zona_nao_cadastrada`; teste de integração roda o seed antes de gravar | PASS |
| Janela configurável por env | `DB_JANELA_SEGUNDOS` (padrão 60) em `main.py` | PASS (código) |
| Escopo só de persistência (sem compose/TTL) | TTL segue em API-03 (Fase 4) e compose na Fase 5 | PASS |

## Testes negativos (devem falhar ao violar)

- `test_fila_rejeita_chave_por_pessoa` — 6 chaves vetadas, todas rejeitadas na entrada da fila.
- `test_writer_recusa_lote_com_dado_por_pessoa` — lote com `track_id` levanta `ValueError` antes de tocar o banco.
- `test_schema_nao_contem_tabelas_ou_colunas_vetadas` — falha se alguém recriar `sessoes`/`session_traces`.

## Suíte

```
49 passed, 1 skipped            # sem banco (integração pulada)
19 passed                       # com DB_TESTE=1 e PostgreSQL 16 no ar
```

## Como reproduzir a validação

```bash
docker run -d --name pg-fase3-val -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=hotel_analytics -p 55432:5432 postgres:16-alpine

DB_TESTE=1 DB_PORT=55432 .venv/bin/python -m pytest tests/test_fila_batch_privacidade.py -q

DB_PORT=55432 .venv/bin/python -m db.seed          # cadastro de câmeras/zonas
DB_PORT=55432 .venv/bin/python main.py 0           # pipeline + escrita em lote

docker rm -f pg-fase3-val
```

## Lacunas conhecidas (não bloqueiam a fase)

- Latência **do pipeline completo em GPU** não medida aqui — é critério da Fase 8 (QUA-01).
- `dwell_agregado_zona` e `heatmap_densidade_camada` existem e estão vazias de propósito; são
  preenchidas na Fase 7.
- Sem `docker-compose` versionado e sem política de TTL nesta fase (Fases 5 e 4, respectivamente).
