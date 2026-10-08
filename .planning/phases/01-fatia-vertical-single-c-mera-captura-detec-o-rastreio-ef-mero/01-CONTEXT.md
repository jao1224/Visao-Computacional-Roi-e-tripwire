# Phase 1: Fatia vertical single-câmera (captura, detecção, rastreio efêmero) - Context

**Gathered:** 2026-10-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Pipeline mínimo de visão em **1 câmera** (webcam ou vídeo-amostra): captura → YOLO CrowdHuman (corpo) → ByteTrack efêmero em RAM → overlay na tela. Base de privacidade estabelecida desde o início: **nada em disco** (nenhum frame/crop/imagem), IDs de rastreio morrem ao sair do quadro, nenhum módulo de face/biometria. Sem RTSP (Fase 6), sem banco (Fase 3), sem API/dashboard (Fases 4–5), sem contagem por zona (Fase 2).

Requisitos da fase: ING-01, ING-03, CNT-01, CNT-03.

</domain>

<decisions>
## Implementation Decisions

### Estrutura do Código
- **D-01:** Módulos **planos na raiz** do projeto — `captura.py`, `rastreio.py`, `overlay.py` — importados pelo `main.py`. **Sem pacote, sem `__init__.py`**, seguindo a convenção atual de scripts autônomos (`STRUCTURE.md`).
- **D-02:** Nomes dos módulos novos **em português** (combina com a raiz — `treinar_crowdhuman.py` — e com mensagens/comentários em pt-BR).
- **D-03:** `main.py` permanece o **único ponto de entrada** (`python main.py`, `q` para sair) — mantém seus padrões atuais: resolução de pesos por fallback de candidatos (`main.py:11-19`), guard `main()`, mensagens em pt-BR.
- **D-04:** Conexão entre módulos por **funções simples** chamadas pelo laço `while` do `main.py` (ex.: `capturar()`, `rastrear()`, `desenhar()`) — **sem classes nem Pipeline orquestrador**; cada função faz uma coisa.
- **D-05:** Criar **`requirements.txt`** mínimo na raiz (ultralytics, opencv-python, numpy e o que mais os imports exigirem) — hoje o repo não tem nenhum lock de dependências.
- **D-06:** Logs de execução **somente no console** (print com tags `[OK]`/`[Aviso]`/`-->` em pt-BR) — nenhum arquivo de log em disco (elimina risco de log por-pessoa violar ING-03).

### the agent's Discretion
- Assinatura exata e parâmetros das funções de cada módulo
- Como o ByteTrack é integrado (provavelmente `model.track()` do Ultralytics com `persist=True` — decisão técnica do researcher/planner)
- Formato dos dados passados entre módulos (dict, tupla, dataclass simples)
- Valores de `conf`, `iou`, FPS alvo (hoje 5 FPS em `main.py:35`)
- Estratégia de teste manual com `test/gemini_generated_video_8d21d35f.mp4`
- Conteúdo detalhado do `requirements.txt` (versões)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §Phase 1 — goal, success criteria (4 itens) e requisitos da fase
- `.planning/REQUIREMENTS.md` — ING-01 (webcam + vídeo-amostra), ING-03 (frames voláteis), CNT-01 (só corpo), CNT-03 (associação intra-câmera efêmera)
- `DOCUMENTACAO_PROJETO_E_LGPD/09_PLANO_DE_FASES_V1.md` §Fase 1 — detalhamento, critérios e base legal

### Conformidade (obrigatório em toda decisão de código)
- `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` — 11 condições vinculantes (verificar invariantes: nada em disco, sem face, IDs efêmeros)
- `.planning/PROJECT.md` — Out of Scope permanente e Core Value

### Convenções e código existente
- `AGENTS.md` — regras do projeto (pt-BR, convenções, workflow)
- `main.py` — referência atual: resolução de pesos, loop de webcam, HUD (`main.py:73`)
- `.planning/codebase/STRUCTURE.md` — papéis dos arquivos (main.py = principal; novos módulos na raiz)
- `.planning/codebase/CONVENTIONS.md` — nomenclatura, imports, estilo

### Pesquisa técnica (alimenta o researcher)
- `.planning/research/SUMMARY.md` §Phase 1 — síntese do que a fase precisa ter
- `.planning/research/PITFALLS.md` — armadilhas marcadas "Phase 1" (contrato de timestamp, fila latest-frame-wins, baseline de privacidade)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `main.py:11-19`: resolução de pesos por lista de candidatos com fallback — manter
- `main.py:48`: inferência YOLO (`conf=0.25, iou=0.60`) — ponto de integração do rastreio
- `main.py:57-65`: desenho de caixas/labels — extrair para `overlay.py`
- `main.py:67-76`: HUD de FPS + contagem — extrair para `overlay.py`
- `main.py:78-81`: loop com teto de FPS e `q` para sair — manter como orquestração
- `test/gemini_generated_video_8d21d35f.mp4` (~6 MB): vídeo-amostra para ING-01
- `resultados/best.pt`: pesos treinados (primeiro candidato do fallback)

### Established Patterns
- `main()` + guard `if __name__ == "__main__"`; 4 espaços; aspas simples
- Imports stdlib primeiro, depois terceiros, bloco único
- Mensagens pt-BR com tags `[OK]`/`[Aviso]`/`-->`
- Resolução de caminhos: `base_dir = os.path.dirname(os.path.abspath(__file__))`
- Sem framework de testes, sem linter, sem requirements.txt (será criado — D-05)

### Integration Points
- `main.py` chama os novos módulos (`captura`, `rastreio`, `overlay`) — eles NÃO chamam main
- RTSP entrará depois (Fase 6): `captura.py` deve ser a fronteira da fonte de vídeo (webcam/arquivo hoje, RTSP depois) — desenho da interface fica a critério do planner

</code_context>

<specifics>
## Specific Ideas

- "Todo o desenvolvimento deve convergir para o `main.py`" (STRUCTURE.md:41 — decisão do usuário sobre o papel do arquivo principal)
- Logs: "Só console" — zero arquivo de log em disco (decisão do usuário nesta discussão)

</specifics>

<deferred>
## Deferred Ideas

- Nenhuma — a discussão permaneceu dentro do escopo da fase.

</deferred>

---

*Phase: 01-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero*
*Context gathered: 2026-10-08*
