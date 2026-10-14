---
id: SEED-261014-szc
status: dormant
planted: 2026-10-14
planted_during: v1.0 / Fase 2 concluída (pré-Fase 3)
trigger_when: "ao planejar a Fase 7 (Analytics de permanência e heatmap agregado) — requisito DWL-02"
scope: medium
---

# SEED-261014-szc: Mapa de ocupação por área (não fluxo) — heatmap de presença dentro do ROI

## Why This Matters

O usuário definiu que o objetivo do heatmap é ver **ocupação** (presença / área
ocupada), **não fluxo**. Isso muda a âncora de cálculo:

- **Fluxo** usa a âncora **pé** (`_bottom_center`) — responde "onde a pessoa pisa".
- **Ocupação** deve usar a **área da pessoa** — responde "que região está ocupada",
  porque ocupação é área, não um ponto.

Consequências de design já discutidas e decididas com o usuário:

1. **Rastrear a área, não o pé.** A cada frame, rasterizar a região ocupada por
   cada pessoa (caixa ou base), cruzar com a máscara do ROI e marcar as células
   da grade.
2. **Binário por frame (0/1 por célula).** Evita inflar quando pessoas se
   sobrepõem; ao acumular no tempo, cada célula vira "fração do tempo ocupada".
3. **Somente agregados persistidos.** Nada por pessoa (sem `track_id`), sem
   histórico de posição individual — LGPD art. 12 §2º (ver COMPLIANCE).
4. **Viés de perspectiva é o principal risco.** Pessoa perto da câmera cobre mais
   células que pessoa longe ⇒ "mais quente perto da câmera". Mitigações, em ordem
   de qualidade: (a) **homografia** imagem→planta em metros (ideal, câmera fixa);
   (b) usar só a **base** da caixa e normalizar pela escala; (c) aceitar e
   documentar como "ocupação no espaço da imagem".
5. **Métricas derivadas úteis:** taxa de ocupação da zona (%) = células ocupadas ÷
   células do ROI; mapa de ocupação por janela (célula × tempo).

Decisão de configuração sugerida (a validar na Fase 7):

```yaml
- id: "hall"
  tipo: "roi"
  pontos: [...]
  ocupacao:
    modo: "area"        # "area" (ocupação) | "pe" (contagem por ponto)
    regiao: "base"      # "base" (menos viés) | "caixa"
    binario: true
    grade: [64, 48]
    janela_seg: 300
```

## When to Surface

**Trigger:** ao planejar a **Fase 7 (Analytics de permanência e heatmap agregado)**,
requisito **DWL-02** ("Heatmap de densidade agregado (célula × janela de tempo)").

Nota: a decisão de usar **área** (e não pé) é uma escolha de semântica de
"ocupação"; a Fase 7 deve confirmar `modo/regiao/formalismo` (homografia ou não) e
o formato da tabela de buckets (`heatmap_buckets(camera_id, zone_id, window_start,
cell_x, cell_y, count)` — sem `track_id`).

Este seed também deve ser lido se a Fase 3 (persistência) for reaberta para o
tema heatmap — mas a Fase 3 em si trata só da fila/batch writer + schema de
contagem/ocupação escalar.

## Scope Estimate

**Medium** — é parte da Fase 7: grade configurável, acumulação binária por
frame, render do mapa, tabela de buckets e (opcional) homografia. Não é um
projeto isolado.

## Breadcrumbs

- `zona.py` — `atualizar_ocupacao` (ocupação escalar; hoje usa pé), `_bottom_center`,
  `carregar_zonas`, `_area_roi` (resolução do polígono do ROI)
- `config/zonas.yaml` — zona `hall` (ROI, capacidade 50)
- `overlay.py` — `desenhar_rois` (base do overlay do mapa)
- `.planning/ROADMAP.md` §Phase 7 — goal + success criteria (heatmap agregado)
- `.planning/REQUIREMENTS.md` — **DWL-02** (heatmap agregado), **DWL-01** (dwell),
  **API-01** (schema só agregados)
- `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` — veto a histórico por pessoa;
  heatmap = densidade agregada, sem vetor de identidade
- `.planning/research/FEATURES.md` — "Prefer **dwell-weighted** over raw hits for hotels"
- `prototipo_ocupacao.py` — protótipo que valida a abordagem por área no vídeo-amostra
  `test/gemini_generated_video_8d21d35f.mp4` (1280×720)

## Notes

Capturado em conversa de 2026-10-14. Protótipo (`prototipo_ocupacao.py`) gerou o
mapa de ocupação agregado a partir do vídeo-amostra para validar visualmente a
abordagem por área (máscara ∩ ROI, binário por frame). Imagem de saída **não**
contém pixels de pessoas (canvas agregado), preservando o invariante de "nenhum
frame/imagem de pessoa em disco".
