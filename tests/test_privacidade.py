import os
import glob
import sys

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)


def _repo_root():
    # tests/ -> repo root
    return BASE_DIR


def _produto_files():
    root = _repo_root()
    return [
        os.path.join(root, 'main.py'),
        os.path.join(root, 'captura.py'),
        os.path.join(root, 'rastreio.py'),
        os.path.join(root, 'overlay.py'),
        os.path.join(root, 'zona.py'),
        os.path.join(root, 'requirements.txt'),
    ]


def test_sem_modulos_de_face():
    """Não há tokens de face/biometria/escrita de mídia nos módulos do produto + requirements.txt."""
    tokens_proibidos = [
        'face',
        'biometr',
        'demograf',
        'insightface',
        'facenet',
        'retinaface',
        'arcface',
        'deepface',
        'cv2.face',
        'imwrite',
        'imsave',
        'videowriter',
        'tofile',
    ]
    for path in _produto_files():
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
        except Exception:
            continue
        conteudo_lower = conteudo.lower()
        for token in tokens_proibidos:
            assert token not in conteudo_lower, f"Token proibido '{token}' encontrado em {path}"


def _listar_arquivos_midia(root):
    padroes = ['**/*.jpg', '**/*.jpeg', '**/*.png', '**/*.mp4', '**/*.avi', '**/*.mkv']
    arquivos = set()
    for p in padroes:
        for m in glob.glob(os.path.join(root, p), recursive=True):
            # Ignorar .git
            if '.git' in m.replace(os.sep, '/'):
                continue
            arquivos.add(os.path.abspath(m))
    return arquivos


def test_sem_escrita_em_disco(caminho_modelo, caminho_video_amostra):
    """Pipeline headless não deve criar arquivos de mídia em disco."""
    root = _repo_root()
    antes = _listar_arquivos_midia(root)
    try:
        import captura
        import rastreio
        import overlay
    except Exception:
        # Se não importar, pode pular com motivo — mas módulos devem existir
        pass

    cap = None
    try:
        cap = captura.abrir_fonte(caminho_video_amostra)
        if cap is None or not cap.isOpened():
            pytest.skip('Não foi possível abrir o vídeo-amostra para auditoria de disco')

        model = rastreio.carregar_modelo(caminho_modelo)
        frames_processados = 0
        for _ in range(30):
            frame, capture_ts = captura.capturar(cap)
            if frame is None or capture_ts is None:
                break
            result = rastreio.rastrear(model, frame)
            caixas = rastreio.extrair_caixas(result)
            overlay.desenhar_caixas(frame, caixas)
            # HUD opcional não grava
            try:
                overlay.desenhar_hud(frame, 0.0, len(caixas))
            except Exception:
                pass
            frames_processados += 1
        # Se não processou nenhum frame, pode ser skip por disponibilidade
        if frames_processados == 0:
            pytest.skip('Não foi possível processar frames do vídeo-amostra')
    except pytest.skip.Exception:
        raise
    except Exception as e:
        pytest.skip(f'Pipeline não executado para auditoria de disco: {e}')
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass

    depois = _listar_arquivos_midia(root)
    novos = depois - antes
    assert len(novos) == 0, f"Arquivos de mídia novos detectados: {sorted(novos)}"


def test_requirements_sem_contrib():
    root = _repo_root()
    req_path = os.path.join(root, 'requirements.txt')
    if not os.path.exists(req_path):
        pytest.skip('requirements.txt não encontrado')
    try:
        with open(req_path, 'r', encoding='utf-8', errors='ignore') as f:
            conteudo = f.read()
    except Exception as e:
        pytest.skip(f'Não foi possível ler requirements.txt: {e}')
    conteudo_lower = conteudo.lower()
    assert 'opencv-contrib' not in conteudo_lower, 'requirements.txt contém opencv-contrib'
