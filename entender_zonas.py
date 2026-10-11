#!/usr/bin/env python3
"""
Visualização simples das zonas - roda no terminal e mostra o frame com as zonas desenhadas.
"""
import cv2
import numpy as np
import yaml

# Carrega config
with open('config/zonas.yaml', 'r') as f:
    cfg = yaml.safe_load(f)

camera = cfg['camera_0']
zonas = camera['zonas']

# Frame de referência (480x640)
frame = np.zeros((480, 640, 3), dtype=np.uint8)

print("=" * 60)
print("ZONAS CONFIGURADAS (camera_0)")
print("=" * 60)

for z in zonas:
    print(f"\n[+] Zona: {z['id']}  |  Tipo: {z['tipo']}")
    if z['tipo'] == 'tripwire':
        p1, p2 = z['pontos']
        print(f"   Linha: ({p1[0]}, {p1[1]})  ->  ({p2[0]}, {p2[1]})")
        print(f"   Direção: {z['direcao']}")
        print(f"   [OK] ENTROU = pessoa cruzando no sentido da seta")
        print(f"   [X] SAIU   = pessoa cruzando no sentido oposto")
        # Desenha linha
        cor = (0, 255, 0) if z['direcao'] == 'entrada' else (0, 0, 255)
        cv2.line(frame, tuple(p1), tuple(p2), cor, 3)
        # Label
        mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
        cv2.putText(frame, z['id'], mid, cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
        
    elif z['tipo'] == 'roi':
        pts = np.array(z['pontos'], dtype=np.int32)
        print(f"   Polígono: {len(pts)} pontos")
        for i, p in enumerate(pts):
            print(f"     P{i+1}: ({p[0]}, {p[1]})")
        print(f"   [*] Ocupação = pessoas com pé (bottom-center) DENTRO deste retângulo")
        # Desenha ROI
        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], (255, 0, 0))
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        cv2.polylines(frame, [pts], True, (255, 0, 0), 2)

print(f"\n[*] Capacidade por câmera: {camera.get('capacidade', 'N/A')}")
print("=" * 60)

# Salva imagem para visualizar
cv2.imwrite('zonas_visualizacao.png', frame)
print("\n[OK] Imagem salva: zonas_visualizacao.png")
print("   Abra esse arquivo para ver as zonas desenhadas no frame.")

# Explicação rápida
print("""
+--------------------------------------------------------------+
|  COMO FUNCIONA (resumo)                                      |
+--------------------------------------------------------------+
|  TRIPWIRE (linha):                                           |
|  * YOLO detecta pessoa -> caixa [x1,y1,x2,y2]                |
|  * Pega o PÉ da pessoa: bottom_center = ((x1+x2)/2, y2)      |
|  * Verifica de que lado da linha o pé está (produto vetorial)|
|  * Se lado MUDOU entre frames + debounce(3) + hysteresis(15) |
|       -> ENTROU ou SAIU (conforme direção da linha)          |
|  * 'crossed' evita contar 2x a mesma travessia               |
|                                                              |
|  ROI (polígono):                                             |
|  * A cada frame: conta quantos pés estão DENTRO do polígono  |
|  * cv2.pointPolygonTest(roi, pe, False) >= 0                 |
|  * Ocupação = contagem bruta clamp 0..capacidade             |
|  * Reset diário (meia-noite) OU vazio > 10min zera tudo      |
+--------------------------------------------------------------+
""")