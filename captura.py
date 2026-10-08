import time
import cv2


def abrir_fonte(fonte):
    """Abre uma fonte de vídeo por índice de webcam (int) ou caminho de arquivo (str)."""
    cap = cv2.VideoCapture(fonte)
    if isinstance(fonte, int):
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def capturar(cap):
    """Lê um frame e devolve (frame, capture_ts), carimbando o tempo na captura."""
    ok, frame = cap.read()
    if not ok:
        return None, None
    capture_ts = time.time()
    return frame, capture_ts
