import os
import sys
import time
import cv2
from ultralytics import YOLO
import captura
import rastreio
import overlay


def resolver_fonte(argumentos):
    """Mapeia o argumento de linha de comando para a fonte (índice de webcam ou arquivo)."""
    if not argumentos:
        return 0
    if argumentos[0].isdigit():
        return int(argumentos[0])
    if os.path.exists(argumentos[0]):
        return argumentos[0]
    print(f'[Erro] Fonte não encontrada: {argumentos[0]}')
    return None


def resolver_modelo(candidatos):
    """Devolve o primeiro peso existente da lista de candidatos."""
    return next((p for p in candidatos if os.path.exists(p)), None)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    # 1. Resolver o modelo treinado de corpo
    candidatos = [
        os.path.join(base_dir, 'resultados', 'best.pt'),
        os.path.join(base_dir, 'runs', 'detect', 'train_crowdhuman_body', 'weights', 'best.pt'),
        os.path.join(base_dir, 'models', 'best.pt'),
        os.path.join(root_dir, 'models', 'yolo26n.pt'),
        os.path.join(base_dir, 'yolo26n.pt')
    ]

    modelo_path = resolver_modelo(candidatos)
    if not modelo_path:
        print('[Erro] Nenhum modelo encontrado.')
        return
    print(f'[OK] Modelo: {modelo_path}')
    if os.path.basename(modelo_path) != 'best.pt':
        print('[Aviso] Usando pesos base — detecção restrita a classe 0 (corpo)')

    # 2. Resolver a fonte de vídeo (webcam por índice ou arquivo)
    fonte = resolver_fonte(sys.argv[1:])
    if fonte is None:
        return
    cap = captura.abrir_fonte(fonte)
    if not cap.isOpened():
        print(f'[Erro] Não foi possível abrir a fonte: {fonte}')
        return
    print(f'[OK] Fonte: {fonte} — pressione q para sair.')

    model = rastreio.carregar_modelo(modelo_path)

    target_fps = 5
    frame_duration = 1.0 / target_fps
    prev_time = time.time()

    while True:
        loop_start = time.time()

        frame, capture_ts = captura.capturar(cap)
        if frame is None:
            print('[Aviso] Quadro não lido — encerrando.')
            break

        result = rastreio.rastrear(model, frame)
        caixas = rastreio.extrair_caixas(result)

        overlay.desenhar_caixas(frame, caixas)

        # Cálculo de FPS real medido (tempo de parede)
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        overlay.desenhar_hud(frame, fps, len(caixas))

        cv2.imshow('YOLO - Corpo + ByteTrack (CrowdHuman)', frame)

        # Controle de tempo para travar em 5 FPS
        elapsed = time.time() - loop_start
        delay_ms = max(1, int((frame_duration - elapsed) * 1000))
        if cv2.waitKey(delay_ms) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print('[OK] Encerrado.')


if __name__ == "__main__":
    main()
