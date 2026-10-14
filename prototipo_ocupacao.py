#!/usr/bin/env python3
"""
Protótipo: MAPA DE OCUPAÇÃO por área dentro de um ROI (não é fluxo).

Ideia (validada com o usuário): para "ocupação", a âncora certa não é o pé
(ponto), e sim a ÁREA ocupada pela pessoa. Então, a cada frame:

  1. Rasteriza a região ocupada por cada pessoa (caixa da bbox, ou só a base).
  2. Cruza (AND) com a máscara do ROI da câmera.
  3. Marca as células da grade que ficaram ocupadas -> BINÁRIO por frame (0/1).
  4. Acumula por célula no tempo => "fração do tempo em que a célula esteve ocupada".

Privacidade: NÃO grava nenhum frame/imagem com pessoas. O PNG final é um mapa
AGREGADO (densidade), desenhado num canvas vazio. Nada por pessoa é salvo.

Uso:
    python prototipo_ocupacao.py [video] [saida.png] [--stride N] [--modo base|caixa]

Exemplo:
    python prototipo_ocupacao.py test/gemini_generated_video_8d21d35f.mp4 /tmp/opencode/mapa_ocupacao.png
"""
import os
import sys

import cv2
import numpy as np

import captura
import rastreio
import zona

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# config/zonas.yaml foi calibrado nesta resolução (webcam/amostra)
REF_W, REF_H = 640, 480

# Grade do mapa de ocupação (células)
COLS, ROWS = 64, 48

VIDEO_PADRAO = os.path.join(BASE_DIR, 'test', 'gemini_generated_video_8d21d35f.mp4')
SAIDA_PADRAO = '/tmp/opencode/mapa_ocupacao.png'

CANDIDATOS_MODELO = [
    os.path.join(BASE_DIR, 'resultados', 'best.pt'),
    os.path.join(BASE_DIR, 'runs', 'detect', 'train_crowdhuman_body', 'weights', 'best.pt'),
    os.path.join(BASE_DIR, 'models', 'best.pt'),
    os.path.join(ROOT_DIR, 'models', 'yolo26n.pt'),
    os.path.join(BASE_DIR, 'yolo26n.pt'),
]


def resolver_modelo():
    """Devolve o primeiro peso existente (mesma lista do conftest/main.py)."""
    return next((p for p in CANDIDATOS_MODELO if os.path.exists(p)), None)


def escalar_pontos(pontos, largura, altura):
    """Escala os pontos do YAML (calibrados em REF_WxREF_H) para o frame real."""
    s = min(largura / REF_W, altura / REF_H)
    return [[float(p[0]) * s, float(p[1]) * s] for p in pontos]


def _parse_args(argv):
    """Parser simples de argumentos: posicionais (video, saida) + flags."""
    video, saida, stride, modo = VIDEO_PADRAO, SAIDA_PADRAO, 2, 'base'
    posicionais = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--stride' and i + 1 < len(argv):
            stride = max(1, int(argv[i + 1])); i += 2; continue
        if a == '--modo' and i + 1 < len(argv):
            modo = argv[i + 1]; i += 2; continue
        posicionais.append(a); i += 1
    if len(posicionais) >= 1:
        video = posicionais[0]
    if len(posicionais) >= 2:
        saida = posicionais[1]
    return video, saida, stride, modo


def imprimir_ascii(heat, largura_alvo=48):
    """Imprime o mapa de ocupação como texto (blocos) — ajuda a 'ver' sem imagem."""
    if heat.max() <= 0:
        print('[Aviso] Mapa vazio.')
        return
    # reduz por blocos (máximo) até ~largura_alvo colunas
    passo_c = max(1, COLS // largura_alvo)
    passo_r = max(1, ROWS // 12)
    chars = ' .:-=+*#%@'
    linhas = []
    for r0 in range(0, ROWS, passo_r):
        linha = ''
        for c0 in range(0, COLS, passo_c):
            bloco = heat[r0:r0 + passo_r, c0:c0 + passo_c]
            v = bloco.max() / heat.max()
            linha += chars[min(len(chars) - 1, int(v * (len(chars) - 1) + 0.5))]
        linhas.append(linha)
    print('[ASCII] Mapa de ocupação (linhas=topo→base, colunas=esq→dir):')
    for linha in linhas:
        print('   |' + linha + '|')


def _regiao_pessoa(x1, y1, x2, y2, modo):
    """Devolve o retângulo (pt1, pt2) da região ocupada pela pessoa."""
    if modo == 'caixa':
        return (x1, y1), (x2, y2)
    # 'base': pé + 25% de baixo da caixa (menos viés de altura/perspectiva)
    base_y = y1 + 0.75 * (y2 - y1)
    return (x1, base_y), (x2, y2)


def main():
    video, saida, stride, modo = _parse_args(sys.argv[1:])

    modelo_path = resolver_modelo()
    if not modelo_path:
        print('[Erro] Nenhum modelo encontrado.')
        return
    print(f'[OK] Modelo: {modelo_path}')

    zonas = zona.carregar_zonas('camera_0')
    roi_zona = next((z for z in zonas if z.get('tipo') == 'roi'), None)
    if roi_zona is None:
        print('[Erro] Nenhuma zona ROI configurada para camera_0.')
        return
    print(f'[OK] Zona ROI: {roi_zona["id"]}')

    cap = captura.abrir_fonte(video)
    if not cap.isOpened():
        print(f'[Erro] Não foi possível abrir a fonte: {video}')
        return
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f'[OK] Fonte: {video} ({largura}x{altura}, stride={stride}, modo={modo})')

    # 1. Máscara do ROI (raster única) e grade de células que tocam o ROI
    roi = np.array(escalar_pontos(roi_zona['pontos'], largura, altura), dtype=np.int32)
    roi_mask = np.zeros((altura, largura), dtype=np.uint8)
    cv2.fillPoly(roi_mask, [roi], 1)
    roi_cel = (cv2.resize(roi_mask.astype(np.float32), (COLS, ROWS),
                          interpolation=cv2.INTER_AREA) > 0).astype(np.uint8)
    total_celulas_roi = int(roi_cel.sum())
    print(f'[OK] ROI escalado: {roi.tolist()}  |  células no ROI: {total_celulas_roi}')

    model = rastreio.carregar_modelo(modelo_path)

    heat = np.zeros((ROWS, COLS), dtype=np.float32)   # acumulador (somas por célula)
    frame_idx = 0
    processados = 0
    max_pct = 0.0
    serie = []  # (frame, % ocupação)

    while True:
        frame, _cap_ts = captura.capturar(cap)
        if frame is None:
            break
        if frame_idx % stride == 0:
            caixas = rastreio.extrair_caixas(rastreio.rastrear(model, frame))

            # 2. Máscara de pessoas do frame (raster por bbox/base)
            pessoas = np.zeros((altura, largura), dtype=np.uint8)
            for _tid, (x1, y1, x2, y2), _conf in caixas:
                (ax, ay), (bx, by) = _regiao_pessoa(x1, y1, x2, y2, modo)
                cv2.rectangle(pessoas, (int(ax), int(ay)), (int(bx), int(by)), 1, -1)

            # 3. Ocupação = pessoas ∩ ROI, reduzida para a grade (binária por frame)
            ocupados = np.logical_and(pessoas, roi_mask).astype(np.float32)
            cel = (cv2.resize(ocupados, (COLS, ROWS),
                              interpolation=cv2.INTER_AREA) > 0).astype(np.float32)
            heat += cel
            processados += 1

            pct = 100.0 * float(cel.sum()) / total_celulas_roi if total_celulas_roi else 0.0
            max_pct = max(max_pct, pct)
            if processados % 20 == 0:
                serie.append((frame_idx, round(pct, 1)))
                print(f'  frame {frame_idx:4d} | ocupação {pct:5.1f}%')
        frame_idx += 1

    cap.release()

    if processados == 0:
        print('[Aviso] Nenhum frame processado.')
        return

    # 4. Render: canvas vazio (SEM pessoas) com o mapa de ocupação dentro do ROI
    canvas = np.zeros((altura, largura, 3), dtype=np.uint8)
    canvas[roi_mask > 0] = (35, 35, 35)  # fundo do ROI

    if heat.max() > 0:
        heat_u8 = (heat / heat.max() * 255).astype(np.uint8)
    else:
        heat_u8 = heat.astype(np.uint8)
    heat_color = cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET)          # ROWS x COLS
    grande = cv2.resize(heat_color, (largura, altura), interpolation=cv2.INTER_NEAREST)
    tem_dado = cv2.resize(((heat > 0).astype(np.uint8) * 255), (largura, altura),
                          interpolation=cv2.INTER_NEAREST) > 0
    sel = np.logical_and(tem_dado, roi_mask > 0)
    canvas[sel] = grande[sel]

    cv2.polylines(canvas, [roi], True, (255, 160, 0), 2)  # contorno do ROI

    media_pct = 100.0 * float(heat.sum()) / (processados * total_celulas_roi) if total_celulas_roi else 0.0
    linhas = [
        f'Mapa de OCUPACAO - zona: {roi_zona["id"]}  (modo={modo})',
        f'frames processados: {processados} (stride {stride})  |  grade {COLS}x{ROWS}',
        f'ocupacao media: {media_pct:.1f}%  |  pico: {max_pct:.1f}%',
        'celula mais quente = mais tempo ocupada (azul=frio, vermelho=quente)',
    ]
    y = 28
    for linha in linhas:
        cv2.putText(canvas, linha, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
        cv2.putText(canvas, linha, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y += 26

    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    cv2.imwrite(saida, canvas)

    imprimir_ascii(heat)
    print('')
    print(f'[OK] Ocupacao media: {media_pct:.1f}%  |  pico: {max_pct:.1f}%')
    print(f'[OK] Mapa salvo (AGREGADO, sem pessoas): {saida}')
    if serie:
        print('[OK] Amostra da série (frame, % ocupação):')
        for f, p in serie[:12]:
            print(f'     frame {f:4d} -> {p:5.1f}%')


if __name__ == '__main__':
    main()
