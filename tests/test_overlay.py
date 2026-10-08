import os
import numpy
import overlay

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_desenha_caixas_in_place():
    frame = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
    caixas = [(1, [100, 100, 200, 200], 0.9)]
    retorno = overlay.desenhar_caixas(frame, caixas)
    assert retorno is None
    assert frame[100:200, 100:200].any()


def test_desenha_hud_in_place():
    frame = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
    overlay.desenhar_hud(frame, 4.8, 3)
    assert frame[:40, :].any()


def test_sem_apis_de_escrita():
    caminho = os.path.join(RAIZ, 'overlay.py')
    with open(caminho, encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
    for token in ['imwrite', 'imsave', 'VideoWriter', 'tofile']:
        assert token not in conteudo
