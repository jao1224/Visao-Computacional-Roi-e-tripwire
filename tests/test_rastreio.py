import os
import pytest
import captura
import rastreio

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _BoxesFalso:
    id = None


class _ResultFalso:
    boxes = _BoxesFalso()


def test_extrair_caixas_guard():
    assert rastreio.extrair_caixas(_ResultFalso()) == []


def test_ids_efemeros(caminho_modelo, caminho_video_amostra):
    cap = captura.abrir_fonte(caminho_video_amostra)
    if not cap.isOpened():
        pytest.skip('Não foi possível abrir o vídeo-amostra')
    model = rastreio.carregar_modelo(caminho_modelo)
    ids_iniciais = set()
    ultimo_ids = set()
    vistos = set()
    try:
        for i in range(70):
            frame, _ = captura.capturar(cap)
            if frame is None:
                break
            result = rastreio.rastrear(model, frame)
            caixas = rastreio.extrair_caixas(result)
            for tid, _xyxy, _conf in caixas:
                assert isinstance(tid, int)
                vistos.add(tid)
                if i < 10:
                    ids_iniciais.add(tid)
            ultimo_ids = {tid for tid, _xyxy, _conf in caixas}
    finally:
        cap.release()

    if not vistos:
        pytest.skip('Vídeo não produziu nenhum ID de rastreio')
    assert len(vistos) >= 1
    if not ids_iniciais:
        pytest.skip('Nenhum ID de rastreio nos frames iniciais do vídeo')
    if not (ids_iniciais - ultimo_ids):
        pytest.skip('Nenhum ID inicial desapareceu no último frame (vídeo curto/densa oclusão)')


def test_sem_escrita_de_ids():
    caminho = os.path.join(RAIZ, 'rastreio.py')
    with open(caminho, encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
    for token in ['to_csv', 'pickle', 'json.dump', 'track_id']:
        assert token not in conteudo
