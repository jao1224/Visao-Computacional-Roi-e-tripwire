"""Contagem por zona (tripwire/ocupação) — lógica pura em RAM, zero escrita em disco."""

import os
import time
from datetime import date

import cv2
import numpy as np
import yaml

base_dir = os.path.dirname(os.path.abspath(__file__))

DEBOUNCE_FRAMES = 3
HYSTERESIS_PX = 15.0
RESET_IDLE_SEG = 600
PRUNE_FRAMES = 60


def _bottom_center(xyxy):
    """Devolve a âncora centro-inferior (x, y) da caixa [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = xyxy
    return ((x1 + x2) / 2.0, y2)


def _lado(p1, p2, ponto):
    """Devolve o lado do ponto em relação ao vetor p1->p2: +1 esquerda, -1 direita, 0 na linha."""
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    wx, wy = ponto[0] - p1[0], ponto[1] - p1[1]
    s = vx * wy - vy * wx
    if s > 0:
        return 1
    if s < 0:
        return -1
    return 0


def _dist_ponto_segmento(p1, p2, ponto):
    """Devolve a distância euclidiana do ponto ao segmento p1-p2 (projeção com clamp)."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    q = np.asarray(ponto, dtype=float)
    ab = p2 - p1
    t = np.clip(np.dot(q - p1, ab) / np.dot(ab, ab), 0.0, 1.0)
    return float(np.linalg.norm(q - (p1 + t * ab)))


def _pontos_validos(pontos, minimo):
    """Valida uma lista de pontos como pares numéricos finitos com tamanho mínimo."""
    if not isinstance(pontos, list) or len(pontos) < minimo:
        return False
    for ponto in pontos:
        if not isinstance(ponto, (list, tuple)) or len(ponto) != 2:
            return False
        for valor in ponto:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                return False
            if not np.isfinite(valor):
                return False
    return True


def _normalizar_zona(zona, capacidade):
    """Valida e normaliza uma zona do YAML; devolve (dict_normalizado, None) ou (None, erro)."""
    if not isinstance(zona, dict):
        return None, 'zona não é um mapeamento'
    tipo = zona.get('tipo')
    if tipo not in ('tripwire', 'roi'):
        return None, 'tipo inválido'
    pontos = zona.get('pontos')
    minimo = 2 if tipo == 'tripwire' else 3
    if not _pontos_validos(pontos, minimo):
        return None, 'pontos inválidos'
    normalizada = {'id': str(zona.get('id', '')), 'tipo': tipo,
                   'pontos': [[float(p[0]), float(p[1])] for p in pontos],
                   'capacidade': capacidade}
    if tipo == 'tripwire':
        direcao = zona.get('direcao')
        if direcao not in ('entrada', 'saida'):
            return None, 'direcao inválida'
        normalizada['direcao'] = direcao
    roi_pontos = zona.get('roi_pontos')
    if roi_pontos is not None:
        if not _pontos_validos(roi_pontos, 3):
            return None, 'roi_pontos inválidos'
        normalizada['roi_pontos'] = [[float(p[0]), float(p[1])] for p in roi_pontos]
    return normalizada, None


def carregar_zonas(camera_id, caminho=None):
    """Carrega e normaliza as zonas de uma câmera a partir do YAML de configuração."""
    if caminho is None:
        caminho = os.path.join(base_dir, 'config', 'zonas.yaml')
    if not os.path.exists(caminho):
        print(f'[Erro] Arquivo de zonas não encontrado: {caminho}')
        return []
    with open(caminho, 'r', encoding='utf-8') as arquivo:
        dados = yaml.safe_load(arquivo)
    if not isinstance(dados, dict) or camera_id not in dados:
        print(f'[Aviso] Câmera {camera_id} não configurada em zonas.yaml')
        return []
    camera = dados[camera_id]
    if not isinstance(camera, dict):
        print(f'[Aviso] Câmera {camera_id} inválida em zonas.yaml')
        return []
    capacidade = camera.get('capacidade')
    if isinstance(capacidade, bool) or not isinstance(capacidade, int) or capacidade <= 0:
        print(f'[Aviso] Capacidade inválida na câmera {camera_id} — zonas ignoradas')
        return []
    zonas = []
    for zona in camera.get('zonas') or []:
        normalizada, erro = _normalizar_zona(zona, capacidade)
        if erro is not None:
            ident = zona.get('id', '?') if isinstance(zona, dict) else '?'
            print(f'[Aviso] Zona inválida ignorada: {erro} (id {ident})')
            continue
        zonas.append(normalizada)
    return zonas


# Tripwire desativado temporariamente — foco em ROI
# def _evento_para_travessia(direcao_tripwire, lado_antes, lado_depois):
#     """Decide o tipo de evento ENTROU/SAIU a partir da direção do tripwire e da transição."""
#     lado_entrada = 1 if direcao_tripwire == 'entrada' else -1
#     if lado_depois == lado_entrada and lado_antes != lado_entrada:
#         return 'ENTROU'
#     return 'SAIU'
#
#
# def verificar_tripwires(tracks, zonas, estado, track_states, agora=None, frame_idx=0):
#     """Verifica travessias de tripwire por transição de lado (sem posição fixa)."""
#     if agora is None:
#         agora = time.time()
#     eventos = []
#     for tid, xyxy, _conf in tracks:
#         st = track_states.setdefault(tid, {'frames_vistos': 0, 'ultimo_frame_visto': frame_idx,
#                                          'crossed': set(), 'posicoes': {}})
#         st['frames_vistos'] += 1
#         st['ultimo_frame_visto'] = frame_idx
#         p = _bottom_center(xyxy)
#         for zona in zonas:
#             if zona['tipo'] != 'tripwire':
#                 continue
#             zona_id = zona['id']
#             p1, p2 = zona['pontos'][0], zona['pontos'][1]
#             lado = _lado(p1, p2, p)
#             pos = st['posicoes']
#             pos_z = pos.setdefault(zona_id, {'lado_anterior': lado})
#             lado_anterior = pos_z['lado_anterior']
#             if lado == 0:
#                 lado = lado_anterior
#             if st['frames_vistos'] == 1:
#                 pos_z['lado_anterior'] = lado
#                 continue
#             if lado != lado_anterior:
#                 dist = _dist_ponto_segmento(p1, p2, p)
#                 if zona_id not in st['crossed']:
#                     if st['frames_vistos'] >= DEBOUNCE_FRAMES:
#                         tipo = _evento_para_travessia(zona['direcao'], lado_anterior, lado)
#                         est_z = estado.setdefault(zona_id, {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None})
#                         if tipo == 'ENTROU':
#                             est_z['entradas'] += 1
#                         else:
#                             est_z['saidas'] += 1
#                         st['crossed'].add(zona_id)
#                         eventos.append((tipo, zona_id, tid, agora))
#                 else:
#                     lado_entrada = 1 if zona['direcao'] == 'entrada' else -1
#                     if lado == -lado_entrada and dist > HYSTERESIS_PX:
#                         tipo = _evento_para_travessia(zona['direcao'], lado_anterior, lado)
#                         est_z = estado.setdefault(zona_id, {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None})
#                         if tipo == 'ENTROU':
#                             est_z['entradas'] += 1
#                         else:
#                             est_z['saidas'] += 1
#                         st['crossed'].discard(zona_id)
#                         eventos.append((tipo, zona_id, tid, agora))
#             pos_z['lado_anterior'] = lado
#     return eventos


def podar_track_states(track_states, frame_idx):
    """Remove tracks que não apareceram há mais de PRUNE_FRAMES frames."""
    for tid in list(track_states):
        st = track_states[tid]
        if frame_idx - st['ultimo_frame_visto'] > PRUNE_FRAMES:
            del track_states[tid]


def _area_roi(zona):
    """Retorna os pontos do ROI para esta zona (pode vir em roi_pontos)."""
    if zona.get('roi_pontos'):
        return zona['roi_pontos']
    if zona.get('tipo') == 'roi':
        return zona['pontos']
    return None


def calcular_intersecao_area_roi(caixas, roi_pontos, frame_shape, modo='base'):
    """
    Calcula a interseção entre as regiões ocupadas pelas pessoas e a área do ROI:
        Interseção = Área(Pessoas) ∩ Área(ROI)
    Retorna:
        pct_ocupada: percentual (0.0 a 100.0) da área do ROI coberta por pessoas.
        area_ocupada_px: quantidade de pixels de interseção.
        area_roi_px: quantidade total de pixels do ROI.
        mascara_intersecao: máscara binária uint8 (H, W) da interseção.
    """
    h, w = frame_shape[:2]
    roi_mask = np.zeros((h, w), dtype=np.uint8)
    roi_pts = np.array(roi_pontos, dtype=np.int32)
    cv2.fillPoly(roi_mask, [roi_pts], 1)
    area_roi_px = int(roi_mask.sum())
    if area_roi_px == 0:
        return 0.0, 0, 0, np.zeros((h, w), dtype=np.uint8)

    pessoas_mask = np.zeros((h, w), dtype=np.uint8)
    for _tid, (x1, y1, x2, y2), _conf in caixas:
        x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), min(w, int(x2)), min(h, int(y2))
        if modo == 'base':
            # Usa o terço inferior da bounding box (base de apoio / chão)
            altura_box = y2 - y1
            y_base = y2 - int(altura_box * 0.35)
            cv2.rectangle(pessoas_mask, (x1, y_base), (x2, y2), 1, -1)
        else:
            cv2.rectangle(pessoas_mask, (x1, y1), (x2, y2), 1, -1)

    intersecao = np.logical_and(pessoas_mask, roi_mask).astype(np.uint8)
    area_ocupada_px = int(intersecao.sum())
    pct_ocupada = 100.0 * (area_ocupada_px / area_roi_px)
    return pct_ocupada, area_ocupada_px, area_roi_px, intersecao


def atualizar_ocupacao(tracks, zonas, estado, agora=None, track_states=None, frame_shape=(480, 640)):
    """Reconta ocupação por frame com clamp, resets e cálculo de Interseção de Área (Área(Objeto) ∩ Área(ROI))."""
    if agora is None:
        agora = time.time()
    if track_states is None:
        track_states = {}

    # Reset diário
    lt = time.localtime(agora)
    dia = date(lt.tm_year, lt.tm_mon, lt.tm_mday)
    if estado.get('dia_atual') is None:
        estado['dia_atual'] = dia
    elif dia != estado['dia_atual']:
        for zona in zonas:
            zid = zona['id']
            est_z = estado.setdefault(zid, {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None, 'pct_area': 0.0})
            est_z['ocupacao'] = est_z['entradas'] = est_z['saidas'] = 0
            est_z['ultima_ocupacao_ts'] = None
            est_z['pct_area'] = 0.0
        for st in track_states.values():
            st['crossed'] = set()
        estado['dia_atual'] = dia
        print('[OK] Reset diário (dia trocou)')

    # Processa zonas com ROI
    for zona in zonas:
        pontos_roi = _area_roi(zona)
        if not pontos_roi:
            continue
        zid = zona['id']
        est_z = estado.setdefault(zid, {'ocupacao': 0, 'entradas': 0, 'saidas': 0, 'ultima_ocupacao_ts': None, 'pct_area': 0.0})
        roi = np.array(pontos_roi, dtype=np.int32)
        bruta = 0
        for _tid, xyxy, _conf in tracks:
            p = _bottom_center(xyxy)
            if cv2.pointPolygonTest(roi, p, False) >= 0:
                bruta += 1
        capacidade = zona['capacidade']
        est_z['ocupacao'] = max(0, min(bruta, capacidade))

        # Cálculo da Interseção de Área: Área(Objeto) ∩ Área(ROI)
        pct, _area_px, _roi_px, _mask = calcular_intersecao_area_roi(tracks, pontos_roi, frame_shape, modo='base')
        est_z['pct_area'] = pct

        if bruta > 0:
            est_z['ultima_ocupacao_ts'] = agora
        else:
            uts = est_z['ultima_ocupacao_ts']
            if uts is not None and agora - uts > RESET_IDLE_SEG:
                est_z['ocupacao'] = est_z['entradas'] = est_z['saidas'] = 0
                est_z['pct_area'] = 0.0
                est_z['ultima_ocupacao_ts'] = None
                for st in track_states.values():
                    if zid in st.get('crossed', set()):
                        st['crossed'].discard(zid)


def reconciliar_fonte(estado, track_states):
    """Zera todo o estado de contagem, mantendo dia_atual."""
    for zid, est_z in list(estado.items()):
        if zid == 'dia_atual':
            continue
        if isinstance(est_z, dict):
            est_z['ocupacao'] = 0
            est_z['entradas'] = 0
            est_z['saidas'] = 0
            est_z['ultima_ocupacao_ts'] = None
    track_states.clear()
