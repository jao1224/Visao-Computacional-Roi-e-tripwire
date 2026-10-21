---
issue: "Identificando pessoas fora da zona ROI"
date: "2026-10-16"
status: diagnosed
root_cause: "Dois fatores principais: 1) overlay desenha caixas de TODAS as pessoas do frame indiscriminadamente; 2) HUD mostra contagem global do frame, enquanto o card da zona conta apenas quem está no ROI."
---

# Relatório de Diagnóstico — Identificação Fora da Zona ROI

## Sintoma
O usuário reporta que o sistema "ainda está identificando quem está fora da zona".

## Investigação do Código

### 1. No `overlay.py` e `main.py`:
- `main.py` linha 100: `overlay.desenhar_caixas(frame, caixas)`
  - Essa função desenha o retângulo laranja com `ID {tid} | conf%` para **todas** as pessoas detectadas pelo YOLO no frame inteiro, quer estejam dentro ou fora da zona ROI.
- `main.py` linha 107: `overlay.desenhar_hud(frame, fps, len(caixas))`
  - Mostra no canto superior esquerdo: `FPS: 5.0 | Pessoas: N`, onde `N` é o total de pessoas no campo de visão da câmera, mesmo que estejam fora do ROI.

### 2. Na lógica de Zonas (`zona.py`):
- `zona.atualizar_ocupacao`:
  - `bruta`: conta apenas quem tem o pé dentro do polígono via `cv2.pointPolygonTest(roi, p, False) >= 0`.
  - `calcular_intersecao_area_roi`: calcula `np.logical_and(pessoas_mask, roi_mask)`, considerando apenas os pixels dentro do ROI.
  - Portanto, a **métrica de ocupação da zona** (`OCUP` e `AREA %`) já ignora quem está fora.

## Causa Raiz
O detector/rastreador (YOLO + ByteTrack) processa a cena inteira da câmera. Visualmente, o `main.py` está desenhando as caixas de **todo mundo** que aparece no vídeo, dando a impressão de que o sistema está considerando quem está fora do ROI.

## Soluções Possíveis
1. **Filtrar visualização por ROI:** Desenhar caixas delimitadoras apenas para pessoas cujo pé/base esteja dentro de algum ROI ativo (ou destacar caixas fora com cor cinza/translúcida e dentro com cor viva).
2. **Filtrar o HUD:** Mudar `Pessoas: {len(caixas)}` para `Pessoas no ROI: {ocupacao_total}` ou mostrar ambos.
