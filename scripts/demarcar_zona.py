#!/usr/bin/env python3
"""
Utilitário local de calibração interativa de ROI com recursos de edição e alinhamento automático.

Uso:
    python scripts/demarcar_zona.py [fonte] [--camera camera_0] [--zona hall]
"""
import argparse
import math
import os
import sys

import cv2
import numpy as np
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_CONFIG = os.path.join(BASE_DIR, 'config', 'zonas.yaml')


def parse_args():
    parser = argparse.ArgumentParser(description='Demarcador visual de zonas ROI com alinhamento e edição.')
    parser.add_argument('fonte', nargs='?', default='0',
                        help='Índice da webcam (ex: 0) ou caminho de arquivo/stream (padrão: 0)')
    parser.add_argument('--camera', default='camera_0', help='ID da câmera no YAML (padrão: camera_0)')
    parser.add_argument('--zona', default='hall', help='ID da zona a atualizar/criar (padrão: hall)')
    parser.add_argument('--capacidade', type=int, default=50, help='Capacidade máxima padrão se câmera for nova')
    return parser.parse_args()


def carregar_yaml():
    if os.path.exists(CAMINHO_CONFIG):
        with open(CAMINHO_CONFIG, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}
    return cfg


def salvar_yaml(cfg):
    os.makedirs(os.path.dirname(CAMINHO_CONFIG), exist_ok=True)
    with open(CAMINHO_CONFIG, 'w', encoding='utf-8') as f:
        yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=None)
    print(f'[OK] Configuração salva com sucesso em: {CAMINHO_CONFIG}')


def atualizar_zona_config(cfg, camera_id, zona_id, pontos, capacidade_padrao):
    if camera_id not in cfg:
        cfg[camera_id] = {'capacidade': capacidade_padrao, 'zonas': []}

    cam = cfg[camera_id]
    if 'capacidade' not in cam:
        cam['capacidade'] = capacidade_padrao
    if 'zonas' not in cam or not isinstance(cam['zonas'], list):
        cam['zonas'] = []

    zona_existente = None
    for z in cam['zonas']:
        if isinstance(z, dict) and z.get('id') == zona_id:
            zona_existente = z
            break

    if zona_existente is not None:
        zona_existente['tipo'] = 'roi'
        zona_existente['pontos'] = pontos
    else:
        cam['zonas'].append({
            'id': zona_id,
            'tipo': 'roi',
            'pontos': pontos
        })


def alinhar_pontos_ortogonais(pontos, tolerancia=25):
    """Alinha automaticamente pontos vizinhos que estão quase no mesmo eixo."""
    if len(pontos) < 3:
        return pontos

    novos = [list(p) for p in pontos]
    n = len(novos)

    for i in range(n):
        p1 = novos[i]
        p2 = novos[(i + 1) % n]

        # Quase horizontal (mesmo Y)
        if abs(p1[1] - p2[1]) <= tolerancia:
            y_medio = int(round((p1[1] + p2[1]) / 2.0))
            p1[1] = y_medio
            p2[1] = y_medio

        # Quase vertical (mesmo X)
        if abs(p1[0] - p2[0]) <= tolerancia:
            x_medio = int(round((p1[0] + p2[0]) / 2.0))
            p1[0] = x_medio
            p2[0] = x_medio

    return novos


def alinhar_como_retangulo(pontos):
    """Calcula o retângulo delimitador perfeito (bounding box reto)."""
    if len(pontos) < 2:
        return pontos
    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return [
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y]
    ]


def desenhar_painel_ajuda(frame, largura, pontos_qtd):
    """Cria um painel dedicado no topo com os comandos e atalhos bem legíveis."""
    painel_altura = 85
    painel = np.zeros((painel_altura, largura, 3), dtype=np.uint8)
    painel[:] = (35, 35, 35)  # Fundo cinza escuro

    # Linha divisória
    cv2.line(painel, (0, painel_altura - 1), (largura, painel_altura - 1), (0, 200, 255), 2)

    # Linha 1: Status e Mouse
    status = f"ZONA ROI ({pontos_qtd} pts) | Clique: Add Ponto | Clique+Arraste nos circulos verdes: Mover Ponto"
    cv2.putText(painel, status, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)

    # Linha 2: Teclas de ação rápida
    atalhos_1 = "[A] Alinhar Retas   |   [R] Retangulo 100%   |   [U] Desfazer Ponto"
    cv2.putText(painel, atalhos_1, (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

    # Linha 3: Salvar e Sair
    atalhos_2 = "[S] Salvar no YAML   |   [C] Limpar Tudo   |   [Q / ESC] Sair"
    cv2.putText(painel, atalhos_2, (15, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (100, 255, 100), 1, cv2.LINE_AA)

    return np.vstack([painel, frame])


def main():
    args = parse_args()
    fonte_str = args.fonte
    fonte = int(fonte_str) if fonte_str.isdigit() else fonte_str

    cap = cv2.VideoCapture(fonte)
    if not cap.isOpened():
        print(f'[Erro] Não foi possível abrir a fonte: {fonte}')
        sys.exit(1)

    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        print('[Erro] Falha ao capturar o quadro de referência.')
        sys.exit(1)

    cfg_inicial = carregar_yaml()
    pontos = []
    cam_init = cfg_inicial.get(args.camera, {})
    for z in cam_init.get('zonas', []):
        if z.get('id') == args.zona and z.get('pontos'):
            pontos = [list(p) for p in z['pontos']]
            print(f'[Info] Carregados {len(pontos)} pontos já existentes para a zona "{args.zona}".')
            break

    offset_y = 85  # Compensação pela barra superior de ajuda
    idx_ponto_selecionado = None
    raio_selecao = 15

    def mouse_callback(event, x, y, flags, param):
        nonlocal pontos, idx_ponto_selecionado

        # Se clicou na área do painel superior, ignora
        if y < offset_y:
            return

        frame_y = y - offset_y
        frame_x = x

        if event == cv2.EVENT_LBUTTONDOWN:
            idx_encontrado = None
            for i, p in enumerate(pontos):
                dist = math.hypot(p[0] - frame_x, p[1] - frame_y)
                if dist <= raio_selecao:
                    idx_encontrado = i
                    break

            if idx_encontrado is not None:
                idx_ponto_selecionado = idx_encontrado
            else:
                pontos.append([int(frame_x), int(frame_y)])
                idx_ponto_selecionado = None

        elif event == cv2.EVENT_MOUSEMOVE:
            if idx_ponto_selecionado is not None and (flags & cv2.EVENT_FLAG_LBUTTON):
                pontos[idx_ponto_selecionado] = [int(frame_x), int(frame_y)]

        elif event == cv2.EVENT_LBUTTONUP:
            idx_ponto_selecionado = None

    nome_janela = f'Demarcador ROI - [{args.camera} | {args.zona}]'
    cv2.namedWindow(nome_janela)
    cv2.setMouseCallback(nome_janela, mouse_callback)

    while True:
        display = frame.copy()

        # Desenha polígono sobre o frame da câmera
        if len(pontos) > 0:
            for i, p in enumerate(pontos):
                cv2.circle(display, tuple(p), 6, (0, 255, 0), -1)
                cv2.circle(display, tuple(p), 8, (0, 0, 0), 1)
                cv2.putText(display, str(i + 1), (p[0] + 8, p[1] - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)

            if len(pontos) > 1:
                pts_arr = np.array(pontos, dtype=np.int32)
                cv2.polylines(display, [pts_arr], len(pontos) >= 3, (0, 255, 255), 2)

            if len(pontos) >= 3:
                overlay = display.copy()
                cv2.fillPoly(overlay, [np.array(pontos, dtype=np.int32)], (255, 0, 0))
                cv2.addWeighted(overlay, 0.25, display, 0.75, 0, display)

        # Adiciona o painel superior fixo com os atalhos
        tela_final = desenhar_painel_ajuda(display, display.shape[1], len(pontos))

        cv2.imshow(nome_janela, tela_final)
        key = cv2.waitKey(20) & 0xFF

        if key in (27, ord('q')):
            print('[Aviso] Cancelado. Nenhuma alteração foi salva.')
            break
        elif key == ord('c'):
            pontos.clear()
            print('[Info] Pontos limpos.')
        elif key == ord('u'):
            if pontos:
                removido = pontos.pop()
                print(f'[Info] Ponto {removido} desfeito.')
        elif key == ord('a'):
            pontos = alinhar_pontos_ortogonais(pontos)
            print('[OK] Alinhamento automático aplicado (arestas ortogonais ajustadas).')
        elif key == ord('r'):
            if len(pontos) >= 2:
                pontos = alinhar_como_retangulo(pontos)
                print('[OK] Polígono ajustado para retângulo perfeito.')
            else:
                print('[Aviso] Marque pelo menos 2 pontos para gerar retângulo.')
        elif key == ord('s'):
            if len(pontos) < 3:
                print('[Aviso] Um polígono ROI precisa de pelo menos 3 pontos.')
                continue
            cfg = carregar_yaml()
            atualizar_zona_config(cfg, args.camera, args.zona, pontos, args.capacidade)
            salvar_yaml(cfg)
            break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
