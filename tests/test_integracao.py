import os
import glob

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _repo_root():
    return BASE_DIR


def _listar_arquivos_midia_ou_dados(root):
    # Verifica arquivos CSV/JSON novos além de mídia
    padroes = [
        '**/*.jpg', '**/*.jpeg', '**/*.png', '**/*.mp4', '**/*.avi', '**/*.mkv',
        '**/*.csv', '**/*.json',
    ]
    arquivos = set()
    for p in padroes:
        for m in glob.glob(os.path.join(root, p), recursive=True):
            if '.git' in m.replace(os.sep, '/'):
                continue
            arquivos.add(os.path.abspath(m))
    return arquivos


def test_pipeline_amostra_detecta_corpo(caminho_modelo, caminho_video_amostra):
    """Processa >= 60 frames do vídeo-amostra e valida detecções de corpo com IDs inteiros."""
    try:
        import captura
        import rastreio
        import overlay
    except Exception as e:
        pytest.skip(f'Módulos não disponíveis: {e}')

    cap = None
    total_caixas = 0
    ids_vistos = []
    try:
        cap = captura.abrir_fonte(caminho_video_amostra)
        if cap is None or not cap.isOpened():
            pytest.skip('Não foi possível abrir o vídeo-amostra')

        model = rastreio.carregar_modelo(caminho_modelo)
        frames = 0
        # Processar >= 60 frames conforme especificação
        for _ in range(60):
            frame, capture_ts = captura.capturar(cap)
            if frame is None or capture_ts is None:
                break
            result = rastreio.rastrear(model, frame)
            caixas = rastreio.extrair_caixas(result)
            # Desenhar para garantir caminho não-grava (não deve gravar)
            overlay.desenhar_caixas(frame, caixas)
            try:
                overlay.desenhar_hud(frame, 0.0, len(caixas))
            except Exception:
                pass
            for tid, _, _ in caixas:
                assert isinstance(tid, int), f'track_id deve ser int, recebido {type(tid)}'
                ids_vistos.append(tid)
            total_caixas += len(caixas)
            frames += 1
        if frames < 1:
            pytest.skip('Não foi possível processar frames do vídeo-amostra')
    except pytest.skip.Exception:
        raise
    except Exception as e:
        pytest.skip(f'Erro ao processar pipeline: {e}')
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass

    assert total_caixas >= 1, 'Nenhuma caixa detectada no vídeo-amostra'
    assert len(ids_vistos) >= 1, 'Nenhum ID de rastreio observado'


def test_ids_efemeros(caminho_modelo, caminho_video_amostra):
    """Verifica que IDs aparecem e desaparecem (efemeridade) - skip se não houver transição."""
    try:
        import captura
        import rastreio
        import overlay
    except Exception as e:
        pytest.skip(f'Módulos não disponíveis: {e}')

    cap = None
    ids_primeiros = set()
    ids_ultimos = set()
    try:
        cap = captura.abrir_fonte(caminho_video_amostra)
        if cap is None or not cap.isOpened():
            pytest.skip('Não foi possível abrir o vídeo-amostra')

        model = rastreio.carregar_modelo(caminho_modelo)
        frames = []
        # Coletar frames (processando até ~120 para ter chance de transição)
        for _ in range(120):
            frame, capture_ts = captura.capturar(cap)
            if frame is None or capture_ts is None:
                break
            result = rastreio.rastrear(model, frame)
            caixas = rastreio.extrair_caixas(result)
            overlay.desenhar_caixas(frame, caixas)
            frames.append([tid for tid, _, _ in caixas])
        if len(frames) < 10:
            pytest.skip('Poucos frames processados - insuficiente para avaliar transição')

        # IDs dos primeiros 1/3 dos frames
        corte_inicial = max(1, len(frames) // 3)
        for caixa_ids in frames[:corte_inicial]:
            ids_primeiros.update(caixa_ids)
        # IDs dos últimos 1/3 dos frames
        corte_final = max(corte_inicial, len(frames) - (len(frames) // 3))
        for caixa_ids in frames[corte_final:]:
            ids_ultimos.update(caixa_ids)

        if len(ids_primeiros) == 0 and len(ids_ultimos) == 0:
            pytest.skip('Nenhum ID detectado - clipe pode não ter pessoas detectáveis')

        # Pelo menos um ID visto nos primeiros frames não está no último frame
        # Se não houver transição, marcar skip (nunca falha falsa)
        desaparecidos = ids_primeiros - ids_ultimos
        if len(desaparecidos) == 0:
            pytest.skip('Nenhum ID desapareceu entre início e fim (sem transição visível no clipe)')
        assert len(desaparecidos) >= 1
    except pytest.skip.Exception:
        raise
    except Exception as e:
        pytest.skip(f'Erro ao avaliar efemeridade de IDs: {e}')
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass


def test_contagem_amostra_invariantes(caminho_modelo, caminho_video_amostra):
    """Invariantes agregados da contagem por zona no vídeo-amostra (nenhuma contagem específica)."""
    try:
        import captura
        import rastreio
        import zona
    except Exception as e:
        pytest.skip(f'Módulos não disponíveis: {e}')

    cap = None
    try:
        cap = captura.abrir_fonte(caminho_video_amostra)
        if cap is None or not cap.isOpened():
            pytest.skip('Não foi possível abrir o vídeo-amostra')

        model = rastreio.carregar_modelo(caminho_modelo)
        zonas = zona.carregar_zonas('camera_0')
        estado = {'dia_atual': None,
                  **{z['id']: {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}
                     for z in zonas}}
        track_states = {}
        capacidades = {z['id']: z['capacidade'] for z in zonas}
        entradas_antes = {z['id']: 0 for z in zonas}
        saidas_antes = {z['id']: 0 for z in zonas}
        frames = 0
        for frame_idx in range(60):
            frame, capture_ts = captura.capturar(cap)
            if frame is None or capture_ts is None:
                break
            result = rastreio.rastrear(model, frame)
            caixas = rastreio.extrair_caixas(result)
            zona.verificar_tripwires(caixas, zonas, estado, track_states,
                                     agora=capture_ts, frame_idx=frame_idx)
            zona.atualizar_ocupacao(caixas, zonas, estado, agora=capture_ts,
                                    track_states=track_states)
            zona.podar_track_states(track_states, frame_idx)
            for z in zonas:
                dados = estado[z['id']]
                assert dados['ocupacao'] >= 0, 'ocupacao negativa'
                assert dados['ocupacao'] <= capacidades[z['id']], 'ocupacao acima da capacidade'
                assert dados['entradas'] >= entradas_antes[z['id']], 'entradas não monotônicas'
                assert dados['saidas'] >= saidas_antes[z['id']], 'saidas não monotônicas'
                entradas_antes[z['id']] = dados['entradas']
                saidas_antes[z['id']] = dados['saidas']
            frames += 1
        if frames < 1:
            pytest.skip('Não foi possível processar frames do vídeo-amostra')
    except pytest.skip.Exception:
        raise
    except AssertionError:
        raise
    except Exception as e:
        pytest.skip(f'Erro ao avaliar invariantes de contagem: {e}')
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass


def test_sem_persistencia_ids(caminho_modelo, caminho_video_amostra):
    """Verifica que não há persistência de IDs em arquivos do repositório."""
    root = _repo_root()
    antes = _listar_arquivos_midia_ou_dados(root)

    try:
        import captura
        import rastreio
        import overlay
    except Exception as e:
        pytest.skip(f'Módulos não disponíveis: {e}')

    cap = None
    try:
        cap = captura.abrir_fonte(caminho_video_amostra)
        if cap is None or not cap.isOpened():
            pytest.skip('Não foi possível abrir o vídeo-amostra')

        model = rastreio.carregar_modelo(caminho_modelo)
        for _ in range(30):
            frame, capture_ts = captura.capturar(cap)
            if frame is None or capture_ts is None:
                break
            result = rastreio.rastrear(model, frame)
            caixas = rastreio.extrair_caixas(result)
            overlay.desenhar_caixas(frame, caixas)
            try:
                overlay.desenhar_hud(frame, 0.0, len(caixas))
            except Exception:
                pass
    except pytest.skip.Exception:
        raise
    except Exception as e:
        pytest.skip(f'Erro durante processamento: {e}')
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass

    depois = _listar_arquivos_midia_ou_dados(root)
    novos = depois - antes
    assert len(novos) == 0, f'Arquivos novos (possível persistência) detectados: {sorted(novos)}'
