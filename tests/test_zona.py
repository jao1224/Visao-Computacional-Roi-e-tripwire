"""Testes determinísticos de contagem por zona (CNT-02/CNT-04) — Wave 0 da Fase 2."""

import os
import time
from datetime import date

import numpy as np
import pytest

import overlay
import zona

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def caixa_bottom(tid, cx, y2, w=40, h=100):
    """Cria uma caixa de rastreio cuja âncora centro-inferior fica em (cx, y2)."""
    x1 = cx - w / 2
    x2 = cx + w / 2
    y1 = y2 - h
    return (tid, [x1, y1, x2, y2], 0.9)


def _zona_tripwire(ident='recepcao', direcao='entrada'):
    """Zona tripwire de exemplo (linha horizontal em y=240)."""
    return {'id': ident, 'tipo': 'tripwire',
            'pontos': [[100.0, 240.0], [540.0, 240.0]],
            'direcao': direcao, 'capacidade': 30}


def _zona_roi(ident='hall', pontos=None, capacidade=30):
    """Zona ROI de exemplo (polígono quadrado ou customizado)."""
    return {'id': ident, 'tipo': 'roi',
            'pontos': pontos or [[50.0, 50.0], [590.0, 50.0], [590.0, 360.0], [50.0, 360.0]],
            'capacidade': capacidade}


def _epoch(ano, mes, dia, hora, minuto, segundo):
    """Converte uma data/hora local em epoch (segundos), determinístico no host."""
    return time.mktime(time.struct_time((ano, mes, dia, hora, minuto, segundo, 0, 0, -1)))


def rodar_verificacao(cena, zonas, estado, track_states, agora=0.0):
    """Processa uma cena quadro a quadro, acumulando apenas os eventos retornados."""
    eventos = []
    for frame_idx, tracks in enumerate(cena):
        t = agora + frame_idx / 5.0
        eventos.extend(zona.verificar_tripwires(tracks, zonas, estado, track_states, agora=t, frame_idx=frame_idx))
        zona.atualizar_ocupacao(tracks, zonas, estado, agora=t)
        zona.podar_track_states(track_states, frame_idx)
    return eventos


@pytest.fixture
def zonas_config():
    """Zonas reais de camera_0 (ou inline, caso o arquivo não exista)."""
    zonas = zona.carregar_zonas('camera_0')
    if zonas:
        return zonas
    return [_zona_tripwire(), _zona_roi()]


def test_zonas_yaml_camera0():
    zonas = zona.carregar_zonas('camera_0')
    ids = [z['id'] for z in zonas]
    assert ids == ['hall']
    hall = next(z for z in zonas if z['id'] == 'hall')
    assert hall['tipo'] == 'roi'
    assert len(hall['pontos']) >= 3
    assert hall['capacidade'] == 50


def test_carregar_zonas(tmp_path):
    conteudo = (
        'camera_0:\n'
        '  capacidade: 10\n'
        '  zonas:\n'
        '    - id: "ok"\n'
        '      tipo: "tripwire"\n'
        '      pontos: [[0, 0], [10, 0]]\n'
        '      direcao: "entrada"\n'
        '    - id: "poucos_pontos"\n'
        '      tipo: "tripwire"\n'
        '      pontos: [[0, 0]]\n'
        '      direcao: "entrada"\n'
        '    - id: "roi_curto"\n'
        '      tipo: "roi"\n'
        '      pontos: [[0, 0], [10, 0]]\n'
        '    - id: "nao_numerico"\n'
        '      tipo: "roi"\n'
        '      pontos: [[0, 0], [10, 0], ["x", 5]]\n'
        '    - id: "direcao_ruim"\n'
        '      tipo: "tripwire"\n'
        '      pontos: [[0, 0], [10, 0]]\n'
        '      direcao: "lateral"\n'
    )
    caminho = tmp_path / 'zonas.yaml'
    caminho.write_text(conteudo, encoding='utf-8')
    zonas = zona.carregar_zonas('camera_0', caminho=str(caminho))
    assert [z['id'] for z in zonas] == ['ok']
    assert zona.carregar_zonas('camera_inexistente', caminho=str(caminho)) == []
    assert zona.carregar_zonas('camera_0', caminho=str(tmp_path / 'nao_existe.yaml')) == []


def test_tripwire_entrada_saida():
    zona_t = _zona_tripwire()
    ys = list(range(140, 341, 20)) + list(range(320, 139, -20))
    cena = [[caixa_bottom(1, 320, y)] for y in ys]
    estado = {'dia_atual': None,
              'recepcao': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    track_states = {}
    eventos = rodar_verificacao(cena, [zona_t], estado, track_states, agora=0.0)
    assert [(e[0], e[1]) for e in eventos] == [('ENTROU', 'recepcao'), ('SAIU', 'recepcao')]
    assert estado['recepcao']['entradas'] == 1
    assert estado['recepcao']['saidas'] == 1


def test_sem_dupla_contagem():
    zona_t = _zona_tripwire()
    ys = [140, 180, 220, 260, 245, 230, 260, 245, 260, 255]
    cena = [[caixa_bottom(1, 320, y)] for y in ys]
    estado = {'dia_atual': None,
              'recepcao': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    track_states = {}
    eventos = rodar_verificacao(cena, [zona_t], estado, track_states, agora=0.0)
    assert len(eventos) == 1
    assert eventos[0][0] == 'ENTROU'
    assert estado['recepcao']['entradas'] == 1
    assert estado['recepcao']['saidas'] == 0


def test_hysteresis():
    zona_t = _zona_tripwire()
    ys = [230, 230, 230, 250, 230, 250, 235, 255, 230, 250]
    cena = [[caixa_bottom(1, 320, y)] for y in ys]
    estado = {'dia_atual': None,
              'recepcao': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    track_states = {}
    eventos = rodar_verificacao(cena, [zona_t], estado, track_states, agora=0.0)
    assert len(eventos) == 1
    assert eventos[0][0] == 'ENTROU'
    assert estado['recepcao']['entradas'] == 1
    assert estado['recepcao']['saidas'] == 0


def test_debounce_frames():
    zona_t = _zona_tripwire()
    cena = [[caixa_bottom(1, 320, 140)], [caixa_bottom(1, 320, 260)]]
    estado = {'dia_atual': None,
              'recepcao': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    track_states = {}
    eventos = rodar_verificacao(cena, [zona_t], estado, track_states, agora=0.0)
    assert eventos == []
    assert estado['recepcao']['entradas'] == 0
    assert estado['recepcao']['saidas'] == 0


def test_poda_track_states():
    track_states = {7: {'frames_vistos': 1, 'ultimo_frame_visto': 0, 'crossed': set(), 'posicoes': {}}}
    zona.podar_track_states(track_states, 60)
    assert 7 in track_states
    zona.podar_track_states(track_states, 61)
    assert 7 not in track_states


def test_ocupacao_roi():
    zona_r = _zona_roi(ident='zona', pontos=[[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
    zonas = [zona_r, _zona_tripwire(ident='recepcao')]
    tracks = [caixa_bottom(1, 50, 50), caixa_bottom(2, 20, 20),
              caixa_bottom(3, 0, 50), caixa_bottom(4, 200, 200)]
    estado = {'dia_atual': None,
              'zona': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None},
              'recepcao': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    zona.atualizar_ocupacao(tracks, zonas, estado, agora=0.0)
    assert estado['zona']['ocupacao'] == 3
    assert estado['recepcao']['ocupacao'] == 0


def test_clamp_capacidade():
    zona_r = _zona_roi(ident='zona', capacidade=30)
    tracks = [caixa_bottom(i, 50, 50) for i in range(40)]
    estado = {'dia_atual': None,
              'zona': {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    zona.atualizar_ocupacao(tracks, [zona_r], estado, agora=0.0)
    assert estado['zona']['ocupacao'] == 30


def test_reset_diario():
    t1 = _epoch(2026, 10, 8, 23, 59, 59)
    t2 = _epoch(2026, 10, 9, 0, 0, 1)
    zona_t = _zona_tripwire()
    estado = {'dia_atual': date(2026, 10, 8),
              'recepcao': {'ocupacao': 5, 'entradas': 10, 'saidas': 5, 'ultima_ocupacao_ts': t1}}
    track_states = {1: {'frames_vistos': 4, 'ultimo_frame_visto': 3, 'crossed': {'recepcao'},
                        'posicoes': {'recepcao': {'lado_anterior': 1, 'lado_cruzado': 1}}}}
    zona.atualizar_ocupacao([], [zona_t], estado, track_states=track_states, agora=t1)
    assert estado['dia_atual'] == date(2026, 10, 8)
    zona.atualizar_ocupacao([], [zona_t], estado, track_states=track_states, agora=t2)
    assert estado['dia_atual'] == date(2026, 10, 9)
    assert estado['recepcao']['ocupacao'] == 0
    assert estado['recepcao']['entradas'] == 0
    assert estado['recepcao']['saidas'] == 0
    assert track_states[1]['crossed'] == set()


def test_reset_known_empty():
    t = _epoch(2026, 10, 8, 12, 0, 0)
    zona_r = _zona_roi(ident='zona')
    estado = {'dia_atual': date(2026, 10, 8),
              'zona': {'ocupacao': 5, 'entradas': 7, 'saidas': 2, 'ultima_ocupacao_ts': t}}
    zona.atualizar_ocupacao([], [zona_r], estado, agora=t + 300)
    assert estado['zona']['entradas'] == 7
    assert estado['zona']['saidas'] == 2
    assert estado['zona']['ultima_ocupacao_ts'] == t
    zona.atualizar_ocupacao([], [zona_r], estado, agora=t + 601)
    assert estado['zona']['entradas'] == 0
    assert estado['zona']['saidas'] == 0
    assert estado['zona']['ultima_ocupacao_ts'] is None


def test_reconciliacao_fonte():
    estado = {'dia_atual': date(2026, 10, 8),
              'recepcao': {'ocupacao': 4, 'entradas': 9, 'saidas': 5, 'ultima_ocupacao_ts': 123.0}}
    track_states = {1: {'frames_vistos': 4, 'ultimo_frame_visto': 3, 'crossed': {'recepcao'}, 'posicoes': {}}}
    zona.reconciliar_fonte(estado, track_states)
    assert estado['dia_atual'] == date(2026, 10, 8)
    assert estado['recepcao']['ocupacao'] == 0
    assert estado['recepcao']['entradas'] == 0
    assert estado['recepcao']['saidas'] == 0
    assert estado['recepcao']['ultima_ocupacao_ts'] is None
    assert track_states == {}


def test_desenhos_retornam_frame():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    zonas = [_zona_tripwire(ident='recepcao', direcao='entrada'),
             _zona_tripwire(ident='saida1', direcao='saida'),
             _zona_roi(ident='hall')]
    estado = {'dia_atual': None,
              'recepcao': {'ocupacao': 1, 'entradas': 2, 'saidas': 1, 'ultima_ocupacao_ts': None},
              'hall': {'ocupacao': 3, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None}}
    antes = frame.copy()
    r1 = overlay.desenhar_tripwires(frame, zonas)
    r2 = overlay.desenhar_rois(frame, zonas)
    r3 = overlay.desenhar_contadores(frame, estado)
    assert r1 is None and r2 is None and r3 is None
    assert not np.array_equal(frame, antes)
