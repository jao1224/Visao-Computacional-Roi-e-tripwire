# Arquitetura do Sistema

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas, branch `feat/intersecao-area-roi`)
**Escopo:** analytics de fluxo por câmera — contagem e ocupação por zona ROI, **sem identificação, sem gravação em disco**.

---

## 1. Visão Geral

Sistema de visão computacional para hotelaria que transforma câmeras em sensores de negócio: **quantas pessoas estão em cada área e que percentual dela está ocupado**. Toda a privacidade é *by design*: apenas detecção de corpo, rastreio efêmero em RAM e saída agregada. Nenhum frame, crop, ID ou trilha individual toca o disco.

---

## 2. Módulos do Pipeline de Produção

| Módulo | Linhas | Responsabilidade | Ponto de entrada |
|---|---:|---|---|
| `main.py` | 124 | Orquestrador: resolve pesos e fonte de vídeo, carrega as zonas, roda o loop frame a frame, faz o wiring do overlay e mede FPS | `main()` |
| `captura.py` | 19 | Abre a fonte (índice de webcam ou caminho de arquivo) e carimba `capture_ts` no momento da captura | `abrir_fonte`, `capturar` |
| `rastreio.py` | 23 | YOLO de corpo + ByteTrack efêmero; extrai caixas como `(id, (x1,y1,x2,y2), conf)` | `carregar_modelo`, `rastrear`, `extrair_caixas` |
| `zona.py` | 313 | Carrega/valida ROIs do YAML, calcula **ocupação por zona** e **interseção de área**, aplica clamp/reset/reconciliação | `carregar_zonas`, `atualizar_ocupacao`, `calcular_intersecao_area_roi`, `reconciliar_fonte`, `podar_track_states` |
| `overlay.py` | 129 | Desenha ROIs (azul translúcido), interseção (vermelho), **caixas filtradas por ROI**, cards de ocupação e HUD de FPS — tudo *in-place* no frame | `desenhar_rois`, `desenhar_caixas`, `desenhar_contadores`, `desenhar_hud` |
| `entender_zonas.py` | 76 | Utilitário: lê `config/zonas.yaml` e gera `zonas_visualizacao.png` (só polígonos, sem pessoas) | `main()` |

**Fora do pipeline de produção** (`scripts/`): `demarcar_zona.py` (demarcador interativo de ROI), `download_and_convert_crowdhuman.py`, `train_body.py`, `treinar_crowdhuman.py`, `validate_body.py`, `run_pipeline.py`, `setup_colab_ssh.py`, `gerar_relatorio_lgpd.py` (gerador do relatório PDF de conformidade).

---

## 3. Fluxo de Dados por Frame

```
fonte de vídeo (webcam | arquivo)
        │  captura.capturar() → (frame BGR, capture_ts)
        ▼
   rastreio.rastrear(model, frame)
        │  model.track(..., tracker='bytetrack.yaml', conf=0.25, iou=0.60, classes=[0])
        │  → Results único
        ▼
   rastreio.extrair_caixas(results)
        │  → [(id, (x1,y1,x2,y2), conf), ...]     ← guard: lista vazia se boxes.id é None
        ▼
   zona.atualizar_ocupacao(caixas, zonas, estado, agora=capture_ts, frame_shape=frame.shape)
        │  → recontagem de presença por ROI + clamp [0, capacidade]
        │  → calcula_intersecao_area_roi(...) → pct_area  (Área(Objeto) ∩ Área(ROI))
        │  → resets (diário / inatividade) + reconciliação
        ▼
   zona.podar_track_states(track_states, frame_idx)   ← remove tracks > 60 frames sem sighting
        ▼
   overlay.desenhar_rois(frame, zonas, caixas=caixas)
   overlay.desenhar_caixas(frame, caixas, zonas=zonas)   ← só desenha quem intersecta o ROI
   overlay.desenhar_contadores(frame, estado)            ← "Zona hall: OCUP 3 | AREA 12.4%"
   overlay.desenhar_hud(frame, fps, ocupacao_total)
        ▼
   cv2.imshow(...)   ← o frame é desenhado in-place; NUNCA é gravado
```

### Ponto de não-retorno da privacidade
A partir de `extrair_caixas`, o `id` do ByteTrack existe **apenas em RAM** e é descartado com `podar_track_states`. O `estado` (ocupação, `% área`, timestamps) é **recalculado por frame** — não acumula histórico. Nada no fluxo produz um arquivo.

---

## 4. Estado em RAM

| Estrutura | Conteúdo | Ciclo de vida |
|---|---|---|
| `estado` | por zona: `ocupacao`, `entradas`, `saidas`, `pct_area`, `ultima_ocupacao_ts`; + `dia_atual` | vive enquanto o processo roda |
| `track_states` | por track: `frames_vistos`, `ultimo_frame_visto`, `crossed`, `posicoes` | podado após 60 frames sem sighting |
| `zonas` | ROIs normalizadas vindas do YAML | lido uma vez no arranque |

`reconciliar_fonte(estado, track_states)` zera tudo (preservando `dia_atual`) quando a fonte de vídeo reabre.

---

## 5. Arquitetura-Alvo (Fases 3–7 — ainda não implementada)

```
Câmeras RTSP (PyAV, watchdog+backoff)
   → worker por câmera (tracker estritamente por câmera)
      → detecção + ByteTrack efêmero
         → ocupação ROI + interseção de área
            → fila em RAM → batch writer idempotente (UUID por lote)
               → PostgreSQL (config + métricas agregadas)
                  → FastAPI (REST somente-leitura + WebSocket)
                     → Dashboard React + Vite + ECharts
```

Invariantes da arquitetura-alvo: **sem sessão persistida, sem Re-ID/MTMCT, sem frame em disco**. O detalhe está em `.planning/context/ARQUITETURA_TECNICA_E_ENGENHARIA.md`.

---

## 6. Referências

- Escopo e fases: `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`
- Detalhamento do design por fase (rascunho): `.planning/context/DESENHO_POR_FASE.md`
- Roadmap e rastreabilidade: `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`
- Conformidade LGPD: `.planning/context/PARECER_LGPD_E_MARCO_CIVIL.md`
