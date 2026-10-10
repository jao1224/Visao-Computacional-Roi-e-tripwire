"""Contagem por zona (tripwire/ocupação) — lógica pura em RAM, zero escrita em disco."""

import os
import time

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
