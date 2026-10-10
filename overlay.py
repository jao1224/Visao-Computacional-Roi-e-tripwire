import cv2
import numpy as np



def desenhar_caixas(frame, caixas):
    """Desenha caixas com ID e confiança in-place no frame (sem gravar)."""
    for tid, (x1, y1, x2, y2), conf in caixas:
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
        label = f'ID {tid} | {conf*100:.1f}%'
        (w_text, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - 22), (x1 + w_text, y1), (255, 165, 0), -1)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)


def desenhar_tripwires(frame, zonas):
    """Desenha tripwires: verde para 'entrada', vermelho para 'saida'."""
    for zona in zonas:
        if zona.get('tipo') == 'tripwire':
            p1 = tuple(int(v) for v in zona['pontos'][0])
            p2 = tuple(int(v) for v in zona['pontos'][1])
            cor = (0, 255, 0) if zona.get('direcao') == 'entrada' else (0, 0, 255)
            cv2.line(frame, p1, p2, cor, 2)
            mx, my = (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))
            ident = zona.get('id', '')
            cv2.putText(frame, ident, (mx, my), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.putText(frame, ident, (mx, my + 1), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)


def desenhar_rois(frame, zonas):
    """Desenha ROIs semi-transparentes (azul)."""
    for zona in zonas:
        pontos_roi = zona.get('roi_pontos') if zona.get('roi_pontos') else zona.get('pontos')
        if not pontos_roi or len(pontos_roi) < 3:
            continue
        if zona.get('tipo') != 'roi' and not zona.get('roi_pontos'):
            continue
        pts = np.array(pontos_roi, dtype=np.int32)
        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], (255, 0, 0))
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        cv2.polylines(frame, [pts], True, (255, 0, 0), 2)


def desenhar_contadores(frame, estado):
    """Desenha cards de contadores no topo-direita."""
    h, w = frame.shape[:2]
    cards = []
    for zona_id, dados in estado.items():
        if zona_id == 'dia_atual':
            continue
        if isinstance(dados, dict):
            texto = f'Zona {zona_id}: IN {dados.get('entradas', 0)} | OUT {dados.get('saidas', 0)} | OCUP {dados.get('ocupacao', 0)}'
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




