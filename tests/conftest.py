import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

CANDIDATOS_MODELO = [
    os.path.join(BASE_DIR, 'resultados', 'best.pt'),
    os.path.join(BASE_DIR, 'runs', 'detect', 'train_crowdhuman_body', 'weights', 'best.pt'),
    os.path.join(BASE_DIR, 'models', 'best.pt'),
    os.path.join(ROOT_DIR, 'models', 'yolo26n.pt'),
    os.path.join(BASE_DIR, 'yolo26n.pt')
]

CAMINHO_VIDEO_AMOSTRA = os.path.join(BASE_DIR, 'test', 'gemini_generated_video_8d21d35f.mp4')


@pytest.fixture(scope='session')
def caminho_modelo():
    """Devolve o primeiro peso existente da lista de candidatos de main.py."""
    caminho = next((p for p in CANDIDATOS_MODELO if os.path.exists(p)), None)
    if caminho is None:
        pytest.skip('Nenhum modelo encontrado na lista de candidatos')
    return caminho


@pytest.fixture(scope='session')
def caminho_video_amostra():
    """Devolve o caminho do vídeo-amostra em test/."""
    if not os.path.exists(CAMINHO_VIDEO_AMOSTRA):
        pytest.skip('Vídeo-amostra não encontrado em test/')
    return CAMINHO_VIDEO_AMOSTRA
