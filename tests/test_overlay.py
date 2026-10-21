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


def test_desenha_caixas_filtra_fora_do_roi():
    frame = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
    zonas = [{'id': 'hall', 'tipo': 'roi', 'pontos': [[100, 100], [200, 100], [200, 200], [100, 200]]}]
    # Caixa 1: pé em (500, 400) -> FORA do ROI
    caixas_fora = [(1, [450, 300, 550, 400], 0.9)]
    overlay.desenhar_caixas(frame, caixas_fora, zonas=zonas)
    assert not frame.any(), "Nenhuma caixa deveria ser desenhada para pessoa fora do ROI"

    # Caixa 2: pé em (150, 180) -> DENTRO do ROI
    caixas_dentro = [(2, [120, 120, 180, 180], 0.9)]
    overlay.desenhar_caixas(frame, caixas_dentro, zonas=zonas)
    assert frame.any(), "Caixa deveria ser desenhada para pessoa dentro do ROI"


def test_sem_apis_de_escrita():
    caminho = os.path.join(RAIZ, 'overlay.py')
    with open(caminho, encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
    for token in ['imwrite', 'imsave', 'VideoWriter', 'tofile']:
        assert token not in conteudo
