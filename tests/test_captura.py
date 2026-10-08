import captura


def test_abre_video_amostra(caminho_video_amostra):
    cap = captura.abrir_fonte(caminho_video_amostra)
    try:
        assert cap.isOpened() is True
        frame, capture_ts = captura.capturar(cap)
        assert frame is not None
        assert frame.ndim == 3
        assert isinstance(capture_ts, float)
        assert capture_ts > 0
    finally:
        cap.release()


def test_fonte_inexistente_nao_lanca():
    cap = captura.abrir_fonte('nao_existe.mp4')
    try:
        assert cap.isOpened() is False
    finally:
        cap.release()


def test_capture_ts_apos_frame(caminho_video_amostra):
    cap = captura.abrir_fonte(caminho_video_amostra)
    try:
        frame1, ts1 = captura.capturar(cap)
        frame2, ts2 = captura.capturar(cap)
        assert frame1 is not None
        assert frame2 is not None
        assert ts2 >= ts1
    finally:
        cap.release()
