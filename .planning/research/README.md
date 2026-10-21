# Pesquisa de domínio (2026-10-08) — registro datado

> Esta pasta guarda a **pesquisa de domínio feita em 2026-10-08**, anterior ao planejamento
> canônico na forma atual. Os documentos são **referência técnica** — por que a stack foi escolhida,
> quais armadilhas o setor caiu, qual é a forma correta do pipeline — e **não são plano**.
>
> **Regra de leitura:** quando esta pesquisa e o planejamento divergirem, **o planejamento vence**.
> A pesquisa **não** autoriza reintroduzir nada vetado.

---

## Onde está o plano

| Pergunta | Fonte canônica |
| :--- | :--- |
| O que o sistema é e para quem | [`../PROJECT.md`](../PROJECT.md) |
| Quais são os 27 requisitos | [`../REQUIREMENTS.md`](../REQUIREMENTS.md) |
| Quais são as 9 fases | [`../ROADMAP.md`](../ROADMAP.md) |
| Onde a execução está | [`../STATE.md`](../STATE.md) · [`../phases/`](../phases/) |
| O que já foi construído (código real) | [`../codebase/`](../codebase/) |
| Contexto de negócio, arquitetura, plantas, banco, parecer, diretrizes | [`../context/`](../context/) |
| O que foi descartado e por quê | [`../historico/`](../historico/) |

---

## Mapa de validade da pesquisa

| Documento | Data | Estado | **Use para** | **Ignore** |
| :--- | :--- | :--- | :--- | :--- |
| **`SUMMARY.md`** | 2026-10-08 | ⚠️ Parcialmente superado | O *shape* do pipeline (hot loop / cold path), o raciocínio de ordenação, o mapa de riscos | O **roadmap de 6 fases** — o canônico tem **9** |
| **`ARCHITECTURE.md`** | 2026-10-08 | ⚠️ Parcialmente superado | A divisão hot loop/cold path, padrões de fila, contrato idempotente do batch writer | "Pattern 4: MTMCT", `sessoes/fusao.py`, `session_id`, a camada "SESSÃO / MTMCT" do diagrama |
| **`FEATURES.md`** | 2026-10-08 | ⚠️ Parcialmente superado | A lista de **anti-features** (o que nunca construir), a priorização de valor de negócio | MTMCT como "table stakes", o grafo de dependências com O-D flow, tripwire como KPI central |
| **`PITFALLS.md`** | 2026-10-08 | ✅ Válido | Armadilhas do domínio: RTSP/OpenCV, contagem, drift de ocupação, I/O no loop, relógio | Menções a `session_traces` como tabela a reter (tabela vetada) |
| **`STACK.md`** | 2026-10-08 | ⚠️ Versões desatualizadas | A **justificativa** de cada escolha (PyAV, asyncpg, FastAPI, ECharts…) | O pin de **Python 3.12** — o runtime real é **3.14.4**; e `sessoes`/`session_traces` no schema |
| **`COMPLIANCE-LGPD-MARCO-CIVIL.md`** | 2026-10-08 | ✅ **Normativo** | Verificação artigo por artigo + 11 condições vinculantes | — (documento de referência legal, não foi alterado) |

---

## Contradições conhecidas — e como resolvê-las

| # | Contradição na pesquisa | Resolução vigente |
| :-- | :--- | :--- |
| 1 | **Roadmap de 6 fases** (`SUMMARY.md` §Implications) × **9 fases** do plano | Vence [`../ROADMAP.md`](../ROADMAP.md). A ordem das fases também mudou: a contagem por zona (Fase 2) e a persistência (Fase 3) precedem API, dashboard, RTSP, analytics e auditoria. |
| 2 | **MTMCT / Re-ID / `session_id`** como table stakes, diferenciador ou "Fase 5" | **Veto permanente** (LGPD art. 12 §2º). Nunca implementado, nunca a implementar. Ver [`../historico/`](../historico/). |
| 3 | **`sessoes` / `session_traces`** no schema do banco | **Não implementar.** O schema que vai ao banco está em [`../context/MODELAGEM_BANCO_DE_DADOS.md`](../context/MODELAGEM_BANCO_DE_DADOS.md) §2.2 (config + agregados). |
| 4 | **Python 3.12** pinado pela pesquisa | O runtime real é **Python 3.14.4** (venv `.venv/`). A restrição era do `av` 19.x (`cp312-abi3`). Estado real: [`../codebase/STACK.md`](../codebase/STACK.md). |
| 5 | **Tripwire bidirecional** como KPI central | **Desativado** por decisão do usuário — o código está comentado, não removido, em `zona.py`, `overlay.py` e `main.py`. O escopo vigente é **ROI/ocupação por área** (`Interseção = Área(Objeto) ∩ Área(ROI)`). |
| 6 | **Fases 3–7** da pesquisa (persistência, API, dashboard, RTSP, analytics) como sequência | Mantido o **espírito**, reordenado em 9 fases pelo [`../ROADMAP.md`](../ROADMAP.md), que é a versão aprovada. |

---

## Equivalências da numeração antiga ("doc NN")

A pesquisa cita o antigo pacote `docs/DOCUMENTACAO_PROJETO_E_LGPD/` pela numeração original.
Esses documentos foram movidos na consolidação de 2026-10-21:

| Cita como | Onde está agora |
| :--- | :--- |
| doc 01 | [`../context/NEGOCIO_E_OBJETIVOS.md`](../context/NEGOCIO_E_OBJETIVOS.md) |
| doc 02 | [`../context/ARQUITETURA_TECNICA_E_ENGENHARIA.md`](../context/ARQUITETURA_TECNICA_E_ENGENHARIA.md) |
| doc 03 | [`../context/CAMERAS_E_PLANTAS.md`](../context/CAMERAS_E_PLANTAS.md) |
| doc 04, doc 05 | [`../historico/`](../historico/) — **superados, não implementar** |
| doc 06 | [`../context/MODELAGEM_BANCO_DE_DADOS.md`](../context/MODELAGEM_BANCO_DE_DADOS.md) |
| doc 07 | [`../context/PARECER_LGPD_E_MARCO_CIVIL.md`](../context/PARECER_LGPD_E_MARCO_CIVIL.md) |
| doc 08 | [`../context/DIRETRIZES_PARA_AGENTE_IA.md`](../context/DIRETRIZES_PARA_AGENTE_IA.md) |
| doc 09 | [`../context/DESENHO_POR_FASE.md`](../context/DESENHO_POR_FASE.md) |

---

_Índice criado na consolidação documental de 2026-10-21. Nenhum corpo de pesquisa foi reescrito:
a neutralização das contradições foi feita por banner no topo de cada arquivo, preservando o registro
datado da pesquisa._
