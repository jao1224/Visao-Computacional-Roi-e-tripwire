import os
import main

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_sem_argumento_webcam_0():
    assert main.resolver_fonte([]) == 0


def test_indice_vira_int():
    resultado = main.resolver_fonte(['1'])
    assert resultado == 1
    assert isinstance(resultado, int)


def test_caminho_existente(caminho_video_amostra):
    assert main.resolver_fonte([caminho_video_amostra]) == caminho_video_amostra


def test_caminho_inexistente_none(capsys):
    assert main.resolver_fonte(['nao_existe.mp4']) is None
    saida = capsys.readouterr().out
    assert '[Erro]' in saida


def test_resolver_modelo_usa_candidatos():
    inexistente = os.path.join(RAIZ, 'nao_existe_xyz.pt')
    real = os.path.abspath(__file__)
    assert main.resolver_modelo([inexistente, real]) == real
    assert main.resolver_modelo([inexistente]) is None


def test_importa_modulos():
    caminho = os.path.join(RAIZ, 'main.py')
    with open(caminho, encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
    for token in ['import captura', 'import rastreio', 'import overlay']:
        assert token in conteudo
