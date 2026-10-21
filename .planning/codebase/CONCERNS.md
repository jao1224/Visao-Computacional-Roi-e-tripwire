# Preocupações e Riscos do Código-Fonte

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas)
Escopo: analytics de fluxo por ROI, LGPD *by design*.

---

## 1. Riscos técnicos do produto atual

### 1.1 Oclusão em cenas densas
O detector trabalha com **corpos inteiros**; em hall/restaurante cheios, pessoas se sobrepõem e o bounding box de uma pode conter outra. Efeitos: (a) sub-contagem de ocupação em multidão, (b) `pct_area` superestimado quando duas caixas se sobrepõem no ROI (a máscara `pessoas_mask` é a **união** dos retângulos).
**Mitigação prevista:** validação contra marcação manual em condição de pico (Fase 8, QUA-03) e definição escrita de "quem conta".

### 1.2 Viés de perspectiva na ocupação por área
`calcular_intersecao_area_roi` projeta o bounding box 2D sobre o plano da imagem. Uma câmera em altura vê o chão em perspectiva: a mesma pessoa ocupa **menos pixels** ao fundo que à frente, e o ROI é um polígono no plano de imagem, não no chão real. Logo, `pct_area` **não é uma área física** — é uma fração de pixels do ROI.
**Mitigação:** o valor é usado como **métrica relativa de ocupação**, não como área métrica. O heatmap agregado (Fase 7) herda a mesma limitação e deve ser documentado como tal.

### 1.3 Modo de caixa usado na interseção
Por padrão (`modo='base'`) só o **terço inferior** da bounding box entra na máscara de pessoas — a ideia é aproximar o "pé" do chão. Em cenas em que a caixa é muito alta (pessoa próxima à câmera), a base da caixa pode não alcançar o ROI mesmo com a pessoa presente.
**Mitigação:** a presença para a **contagem** usa um critério mais tolerante (pé, centro, vértices ou sobreposição de bounding box com o ROI) — ver `atualizar_ocupacao`.

### 1.4 Detector fallback sem ajuste fino
`main.py` resolve pesos por ordem: `resultados/best.pt` → `runs/detect/train_crowdhuman_body/weights/best.pt` → `models/best.pt` → `models/yolo26n.pt` → `yolo26n.pt`. Se nenhum existir, o sistema avisa "Usando pesos base" e roda com o modelo **não ajustado** para corpo — a precisão cai bastante.
**Mitigação:** `resultados/best.pt` está versionado no repositório.

### 1.5 Foco do produto único (sem multi-câmera)
Hoje o processo trata **uma câmera por execução** (`camera_id` fixo em `camera_0` no `main.py`). O `config/zonas.yaml` é indexado por câmera, mas não há laço multi-stream. A Fase 6 (RTSP multi-stream + watchdog) trata isso.

### 1.6 Sem detector de stream travado
Não há watchdog de staleness nem reconexão: se a webcam cair, `capturar()` devolve `None` e o loop encerra. É aceitável no v1 de desenvolvimento (Fase 6).

### 1.7 OpenCV e RTSP
`cv2.VideoCapture` corrompe frames RTSP após 15–35 s (consta da pesquisa de 2026-10-08). O pipeline atual **não** deve ser apontado para um DVR real — a Fase 6 troca por PyAV.

---

## 2. Escopo funcional: tripwire desativado

O **tripwire bidirecional** (contagem de entradas/saídas por travessia de linha) está **comentado** em `zona.py` (`_evento_para_travessia`, `verificar_tripwires`), `overlay.py` (`desenhar_tripwires`) e `main.py` (chamada no loop). O código **não foi removido** — está pronto para reativação.

Motivo: a travessia de linha é frágil sob oclusão e perspectiva, e o modelo vigente (recontagem por frame + interseção de área) é mais estável e auditável. `config/zonas.yaml` também deixou de declarar zonas do tipo `tripwire`.

⚠️ **Ao reativar:** o modelo de dados muda — `entradas`/`saidas` voltam a ser contadores acumulados em vez de estado recalculado, e a histerese/debounce (`DEBOUNCE_FRAMES = 3`, `HYSTERESIS_PX = 15.0`) volta a ser necessária.

---

## 3. Dívidas registradas (fora do escopo do pipeline)

| Item | Onde | Situação | Origem |
|---|---|---|---|
| `models/base_face_weights.pt` — pesos de **detecção de face** (`names: {0: 'face'}`), usados apenas como inicialização de *transfer learning* no treino do detector de corpo | `scripts/train_body.py`, `scripts/treinar_crowdhuman.py` | 🚫 **Dívida para a Fase 9 (PRV-03)** — fora do escopo do produto, mas faz o grep repo-wide por "face" não vir vazio | Registro em `.planning/phases/01-*/01-04-PLAN.md` |
| `runs/detect/train_crowdhuman_body/` — artefatos do treino (`train_batch*.jpg` com pessoas do dataset público CrowdHuman, `labels.jpg`, `args.yaml`) | raiz do repositório | Resíduo de treino versionado. `args.yaml` contém **caminhos absolutos da máquina original** (Windows) — registro histórico do run, não deve ser reescrito | — |
| `resultados/best (1).pt` — cópia idêntica de `resultados/best.pt` (mesmo md5) | raiz | Duplicata sem uso; candidata a remoção | — |
| `config/data.yaml` — apontava para `C:\Users\ferna\Desktop\...` (caminho absoluto da máquina de treino original) | `config/` | ✅ **Corrigido em 2026-10-21** — `path` passou a ser relativo (`scripts/dataset`), o mesmo destino gerado por `scripts/treinar_crowdhuman.py`; nenhum caminho absoluto de máquina em arquivos versionados | — |
| `test/gemini_generated_video_8d21d35f.mp4` — vídeo-amostra versionado | `test/` | Usado pelos testes de integração; sem pessoas identificáveis | — |

---

## 4. Invariante LGPD — risco operacional

O risco **real** do projeto não é técnico: é alguém reintroduzir uma gravação. O que já existe para barrar isso:

- `tests/test_privacidade.py` — falha se houver módulo/dependência de face, biometria ou demografia; falha se o pipeline escrever imagem/frame/crop em disco.
- `requirements.txt` fixa `opencv-python` (não `opencv-contrib-python`, que puxaria `cv2.face`).
- Invariantes declaradas em `docs/PLANO_V1_COMPLETO.md` §1 e no doc 08 (diretrizes para agentes de IA).

**Pendências da Fase 9 (PRV-01..05):** auditoria repo-wide (hoje a auditoria de teste cobre os módulos do produto, não o resíduo de treino), RIPD, LIA, ROPA, aviso de monitoramento, encarregado e plano de incidente.

---

## 5. Requisitos de ambiente

- **Python 3.14.4** no venv `.venv/` do repositório (`./.venv/bin/python`). O `python` do sistema não tem as dependências.
- `pip install -r requirements-dev.txt` (inclui `pytest>=8.0`).
- **33 testes** verdes em ~6–10 s: `./.venv/bin/python -m pytest`.
- GPU NVIDIA é recomendado (~320 FPS de inferência); CPU funciona para desenvolvimento.
