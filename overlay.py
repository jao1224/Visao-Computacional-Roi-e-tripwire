import cv2


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


def desenhar_hud(frame, fps, n_pessoas):
    """Desenha o HUD de FPS e contagem in-place no frame (sem gravar)."""
    cv2.putText(frame, f'FPS: {fps:.1f} | Pessoas: {n_pessoas}', (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
