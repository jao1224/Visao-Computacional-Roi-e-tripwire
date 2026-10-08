import os
import time
import cv2
from ultralytics import YOLO

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    # 1. Carregar o modelo treinado de corpo
    candidatos = [
        os.path.join(base_dir, 'resultados', 'best.pt'),
        os.path.join(base_dir, 'runs', 'detect', 'train_crowdhuman_body', 'weights', 'best.pt'),
        os.path.join(base_dir, 'models', 'best.pt'),
        os.path.join(root_dir, 'models', 'yolo26n.pt'),
        os.path.join(base_dir, 'yolo26n.pt')
    ]
    
    modelo_path = next((p for p in candidatos if os.path.exists(p)), None)
    if not modelo_path:
        print("Erro: Nenhum modelo encontrado.")
        return
    print(f"Carregando modelo de: {modelo_path}")

    model = YOLO(modelo_path)

    # 2. Abrir webcam
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Erro: Não foi possível abrir a webcam.")
        return

    print("Iniciando detecção de corpo inteiro em tempo real. Pressione 'q' para sair.")

    target_fps = 5
    frame_duration = 1.0 / target_fps
    prev_time = time.time()

    while True:
        loop_start = time.time()
        
        ret, frame = webcam.read()
        if not ret:
            print("Erro ao ler quadro da câmera.")
            break

        # Executa inferência otimizada com logs no terminal
        results = model(frame, conf=0.25, iou=0.60, verbose=True)

        num_pessoas = 0
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                num_pessoas += 1
                
                # Desenhar caixa azul / ciano para corpo inteiro
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
                label = f'Pessoa {conf*100:.1f}%'
                
                # Fundo do texto para melhor leitura
                (w_text, h_text), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x1, y1 - 22), (x1 + w_text, y1), (255, 165, 0), -1)
                cv2.putText(frame, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Cálculo de FPS real medido
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # HUD Informativo no topo da tela
        cv2.putText(frame, f"FPS: {fps:.1f} | Pessoas Detectadas: {num_pessoas}", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('YOLO - Deteccao de Corpo Inteiro (CrowdHuman)', frame)
        
        # Controle de tempo para travar em 5 FPS
        elapsed = time.time() - loop_start
        delay_ms = max(1, int((frame_duration - elapsed) * 1000))
        if cv2.waitKey(delay_ms) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
