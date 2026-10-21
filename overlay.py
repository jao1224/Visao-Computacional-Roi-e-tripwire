import cv2
import numpy as np



def desenhar_caixas(frame, caixas, zonas=None):
    """Desenha caixas com ID e confiança in-place no frame. Se zonas for fornecido, desenha quem intercepta o ROI."""
    rois_poligonos = []
    if zonas:
        for z in zonas:
            pts = z.get('roi_pontos') or z.get('pontos')
            if pts and len(pts) >= 3 and (z.get('tipo') == 'roi' or z.get('roi_pontos')):
                rois_poligonos.append(np.array(pts, dtype=np.int32))

    for tid, (x1, y1, x2, y2), conf in caixas:
        x1_i, y1_i, x2_i, y2_i = int(x1), int(y1), int(x2), int(y2)

        # Se houver zonas ROI configuradas, desenha apenas se a pessoa tocar ou estiver no ROI
        if rois_poligonos:
            pe_x, pe_y = (x1 + x2) / 2.0, float(y2)
            centro_x, centro_y = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            
            # Verifica pé, centro ou qualquer vértice da caixa
            toca_roi = False
            for roi in rois_poligonos:
                if (cv2.pointPolygonTest(roi, (pe_x, pe_y), False) >= 0 or
                    cv2.pointPolygonTest(roi, (centro_x, centro_y), False) >= 0 or
                    cv2.pointPolygonTest(roi, (float(x1), float(y1)), False) >= 0 or
                    cv2.pointPolygonTest(roi, (float(x2), float(y1)), False) >= 0):
                    toca_roi = True
                    break

            # Se ainda não detectou (ex: ROI é menor que a pessoa e está no meio dela)
            if not toca_roi:
                for roi in rois_poligonos:
                    rx, ry, rw, rh = cv2.boundingRect(roi)
                    # Interseção de bounding boxes rápida
                    if not (x2_i < rx or x1_i > rx + rw or y2_i < ry or y1_i > ry + rh):
                        toca_roi = True
                        break

            if not toca_roi:
                continue

        cv2.rectangle(frame, (x1_i, y1_i), (x2_i, y2_i), (255, 165, 0), 2)
        label = f'ID {tid} | {conf*100:.1f}%'
        (w_text, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1_i, y1_i - 22), (x1_i + w_text, y1_i), (255, 165, 0), -1)
        cv2.putText(frame, label, (x1_i, y1_i - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)


# Tripwire desativado temporariamente — foco em ROI
# def desenhar_tripwires(frame, zonas):
#     """Desenha tripwires: verde para 'entrada', vermelho para 'saida'."""
#     for zona in zonas:
#         if zona.get('tipo') == 'tripwire':
#             p1 = tuple(int(v) for v in zona['pontos'][0])
#             p2 = tuple(int(v) for v in zona['pontos'][1])
#             cor = (0, 255, 0) if zona.get('direcao') == 'entrada' else (0, 0, 255)
#             cv2.line(frame, p1, p2, cor, 2)
#             mx, my = (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))
#             ident = zona.get('id', '')
#             cv2.putText(frame, ident, (mx, my), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
#             cv2.putText(frame, ident, (mx, my + 1), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)


def desenhar_rois(frame, zonas, caixas=None):
    """Desenha ROIs semi-transparentes (azul) e destaca a interseção ocupada em vermelho/laranja."""
    h, w = frame.shape[:2]
    for zona in zonas:
        pontos_roi = zona.get('roi_pontos') if zona.get('roi_pontos') else zona.get('pontos')
        if not pontos_roi or len(pontos_roi) < 3:
            continue
        if zona.get('tipo') != 'roi' and not zona.get('roi_pontos'):
            continue
        pts = np.array(pontos_roi, dtype=np.int32)
        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], (255, 0, 0))

        # Se houver caixas, desenha a interseção da área no ROI
        if caixas:
            pessoas_mask = np.zeros((h, w), dtype=np.uint8)
            roi_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(roi_mask, [pts], 1)
            for _tid, (x1, y1, x2, y2), _conf in caixas:
                x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), min(w, int(x2)), min(h, int(y2))
                altura_box = y2 - y1
                y_base = y2 - int(altura_box * 0.35)
                cv2.rectangle(pessoas_mask, (x1, y_base), (x2, y2), 1, -1)
            intersecao = np.logical_and(pessoas_mask, roi_mask)
            overlay[intersecao] = (0, 0, 255)  # Vermelho para a interseção exata

        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
        cv2.polylines(frame, [pts], True, (255, 0, 0), 2)


def desenhar_contadores(frame, estado):
    """Desenha cards de contadores no topo-direita, incluindo ocupação de pessoas e % de área."""
    h, w = frame.shape[:2]
    cards = []
    for zona_id, dados in estado.items():
        if zona_id == 'dia_atual':
            continue
        if isinstance(dados, dict):
            pct_area = dados.get('pct_area', 0.0)
            texto = f'Zona {zona_id}: OCUP {dados.get("ocupacao", 0)} | AREA {pct_area:.1f}%'
            cards.append(texto)
    cards = cards[:6]
    y = 10
    for texto in cards:
        (tw, th), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        card_w, card_h = tw + 20, th + 10
        x = w - card_w - 10
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + card_w, y + card_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.putText(frame, texto, (x + 10, y + th + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y += card_h + 8


def desenhar_hud(frame, fps, n_pessoas):
    """Desenha o HUD de FPS e contagem in-place no frame (sem gravar)."""
    cv2.putText(frame, f'FPS: {fps:.1f} | Pessoas: {n_pessoas}', (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)




