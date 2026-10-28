# Phase 3: Persistência PostgreSQL (fila + escrita em lote) — Contexto

**Goal:** Eventos agregados ganham verdade durável no PostgreSQL sem nunca tocar o loop de vídeo — fila em memória + batch writer idempotente, schema apenas de configuração e métricas agregadas.

**Depends on:** Phase 2 (concluída)
**Requirements:** API-01, QUA-01

## Decisões-chave (vinculantes)

- **ROI-only / saída agregada:** Nunca persistir dados por-pessoa. Sem `track_id`, `session_id`, `session_traces`, `sessoes`, rotas/jornadas/embeddings.
- **Schema permitido:** `cameras`, `zonas`, `metricas_fluxo_zona`. `dwell_agregado_zona` e `heatmap_densidade_camada` já criadas (vazias) para evitar migração na Fase 7.
- **Gravação por janela:** 1 linha por `(zona_id, janela_inicio, janela_fim)`. Não gravar por frame.
- **Fora do hot-loop:** Nenhuma operação SQL dentro do `while True`. Fila em memória + batch writer em thread separada.
- **Idempotência:** `UNIQUE` por janela + `ON CONFLICT DO NOTHING`; lote identificado por `batch_id` (UUID) apenas em log.
- **Latência:** Loop ≤ 5 ms/frame mesmo com escrita ativa.
- **Testes negativos:** Deve falhar se tentar inserir `track_id`/criar tabelas vetadas.

## Decisões confirmadas com o usuário (2026-10-28)

Estas quatro foram discutidas e escolhidas explicitamente — não são suposições minhas:

| Tema | Decisão | Efeito no código |
|---|---|---|
| Banco indisponível | **Retry com fila limitada** (não descartar na primeira falha) | `BatchWriter` mantém pendentes com backoff exponencial (0,5 s → 30 s) e corta os mais antigos ao passar de 1000 eventos |
| Cadastro de zonas | **Seed explícito antes de rodar** | `db/seed.py` sincroniza `cameras`/`zonas` do `config/zonas.yaml`; o writer **não** cria zona alguma, apenas ignora e avisa |
| Janela de agregação | **Configurável por env** | `DB_JANELA_SEGUNDOS` (padrão 60) lido em `main.py` |
| Escopo da fase | **Só persistência** — sem docker-compose nem TTL | TTL é critério da Fase 4 (API-03) e `docker-compose` da Fase 5; a validação usa um PostgreSQL descartável documentado em `03-VERIFICATION.md` |

## Arquitetura-alvo
1. **Produtor (main):** ao fechar janela, monta evento **agregado** (só números) e enfileira.
2. **Fila em memória:** `queue.Queue` com eventos agregados; rejeita chaves por-pessoa.
3. **Batch Writer:** thread dedicada, conexão persistente da própria thread, lote `size-or-time`, retry com backoff.
4. **PostgreSQL:** schema conforme `MODELAGEM_BANCO_DE_DADOS.md` §2.1.

## Estrutura
`metricas_fluxo_zona(id, zona_id, janela_inicio, janela_fim, ocupacao_media, pct_area_media, criado_em)`

## Verificações obrigatórias
- `\dt` mostra apenas tabelas permitidas
- Grep no código: sem `cursor.execute`/`conn.commit` no caminho do loop de vídeo
- Testes negativos passam (falham ao violar)
- FPS/latência estáveis com escrita ativa
- Seed roda antes da gravação e zona desconhecida não é criada implicitamente
