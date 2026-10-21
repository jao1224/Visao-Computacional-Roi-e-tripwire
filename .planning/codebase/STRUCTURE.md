# Estrutura do Repositório

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas)
Branch de trabalho: `feat/intersecao-area-roi`

---

## 1. Árvore (arquivos versionados)

```text
Visao-Computacional-Roi-e-tripwire/
├── main.py                          # Pipeline de produção — orquestrador (124 linhas)
├── captura.py                       # Fonte de vídeo + capture_ts (19)
├── rastreio.py                      # YOLO corpo + ByteTrack efêmero (23)
├── zona.py                          # ROIs, ocupação e interseção de área (313)
├── overlay.py                       # HUD, ROIs e caixas filtradas por ROI (129)
├── entender_zonas.py                # Utilitário: gera zonas_visualizacao.png (76)
│
├── config/
│   ├── data.yaml                    # Config do dataset CrowdHuman (treino) — caminho relativo
│   └── zonas.yaml                   # ROIs por câmera (configuração ativa do produto)
│
├── tests/                           # 33 testes automatizados
│   ├── conftest.py                  # Fixtures compartilhadas (32 linhas)
│   ├── test_captura.py              # 3 testes
│   ├── test_integracao.py           # 4 testes
│   ├── test_main.py                 # 6 testes
│   ├── test_overlay.py              # 4 testes
│   ├── test_privacidade.py          # 3 testes — auditoria LGPD automatizada
│   ├── test_rastreio.py             # 3 testes
│   └── test_zona.py                 # 10 testes
│
├── scripts/                         # Ferramentas de DESENVOLVIMENTO (fora do pipeline)
│   ├── demarcar_zona.py             # Demarcador interativo de ROI (263 linhas)
│   ├── download_and_convert_crowdhuman.py
│   ├── gerar_relatorio_lgpd.py      # Gerador do relatório PDF de conformidade
│   ├── run_pipeline.py
│   ├── setup_colab_ssh.py
│   ├── train_body.py
│   ├── treinar_crowdhuman.py
│   ├── treinar_crowdhuman_colab.ipynb
│   └── validate_body.py
│
├── docs/
│   └── relatorios/                  # Entregáveis para a gestão (PDF)
│       ├── README.md                # Índice dos relatórios publicados
│       ├── RELATORIO-CONFORMIDADE-LGPD-v1.0-2026-10-21.pdf
│       └── RELATORIO-CONFORMIDADE-LGPD-v1.1-2026-10-21.pdf
│
├── .planning/                       # Planejamento canônico (GSD) — fonte única da verdade
│   ├── PROJECT.md  REQUIREMENTS.md  ROADMAP.md  STATE.md
│   ├── config.json  milestone.lock  state.json
│   ├── codebase/                    # 7 documentos: ARCHITECTURE, CONCERNS,
│   │                               # CONVENTIONS, INTEGRATIONS, STACK, STRUCTURE, TESTING
│   ├── context/                     # Contexto: negócio, arquitetura, plantas/câmeras,
│   │                               # banco, parecer LGPD, diretrizes, design por fase
│   ├── historico/                   # Docs superados (face-vs-body, MTMCT) — não implementar
│   ├── phases/                      # Snapshots históricos de fase (PLAN/SUMMARY/RESEARCH)
│   ├── research/                    # Pesquisas (compliance legal, stack, stack-alvo…)
│   ├── debug/                       # Diagnósticos de debug (filtro visual por ROI)
│   └── seeds/                       # Ideias capturadas
│
├── models/                          # Pesos versionados
│   ├── yolo26n.pt                   # Modelo nano (fallback)
│   └── base_face_weights.pt         # ⚠️ pesos de FACE — dívida PRV-03 (fora do pipeline)
│
├── resultados/                      # Saída do treino do detector de corpo
│   ├── best.pt                      # ✅ detector de corpo (usado por main.py)
│   └── best (1).pt                  # cópia idêntica (mesmo md5) — duplicata
│
├── runs/detect/train_crowdhuman_body/   # Artefatos do treino (args.yaml, labels.jpg, batches)
├── test/                            # Vídeo-amostra para os testes
│   └── gemini_generated_video_8d21d35f.mp4
│
├── requirements.txt                 # Pins do produto (5 dependências)
├── requirements-dev.txt             # Pins do produto + pytest
├── README.md                        # Ponto de entrada
├── .gitignore
└── zonas_visualizacao.png           # Saída do utilitário entender_zonas.py
```

---

## 2. O que é produto e o que é resíduo

| Categoria | Caminhos | Regra |
|---|---|---|
| **Pipeline de produção** | `main.py`, `captura.py`, `rastreio.py`, `zona.py`, `overlay.py`, `config/zonas.yaml` | Não podem escrever nada em disco além de código |
| **Utilitário** | `entender_zonas.py` | Só gera `zonas_visualizacao.png` (polígonos, sem pessoas) |
| **Desenvolvimento** | `scripts/` | Fora do pipeline; `scripts/gerar_relatorio_lgpd.py` só produz documentação |
| **Testes** | `tests/` | O único lugar que cria arquivos temporários (e os remove) |
| **Resíduo de treino** | `models/base_face_weights.pt`, `runs/`, `resultados/` | Fora do escopo do produto; `base_face_weights.pt` é **dívida PRV-03** (Fase 9) |

---

## 3. Convenções de caminho

- **Configuração do produto:** sempre dentro de `config/`, lida por caminho relativo ao arquivo do módulo (`base_dir = os.path.dirname(os.path.abspath(__file__))`).
- **Nenhum caminho absoluto** de máquina em arquivos versionados. `runs/detect/train_crowdhuman_body/args.yaml` é a única exceção — é um **registro automático do run de treino original** (máquina Windows) e não deve ser reescrito.
- **Saídas geradas:** `zonas_visualizacao.png` (raiz), `resultados/` (treino), `runs/` (treino).

---

## 4. Referências

- Fluxo entre módulos: `.planning/codebase/ARCHITECTURE.md`
- Riscos e dívidas: `.planning/codebase/CONCERNS.md`
- Cobertura de testes: `.planning/codebase/TESTING.md`
