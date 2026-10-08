from ultralytics import YOLO


def carregar_modelo(modelo_path):
    """Instancia e devolve um modelo YOLO a partir de um caminho de pesos."""
    return YOLO(modelo_path)


def rastrear(model, frame):
    """Rastreia um frame com ByteTrack efêmero e devolve um único Results."""
    results = model.track(frame, persist=True, tracker='bytetrack.yaml',
                          conf=0.25, iou=0.60, classes=[0], verbose=False)
    return results[0]
