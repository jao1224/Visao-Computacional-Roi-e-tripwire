import os
import sys
from ultralytics import YOLO

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Usar a CÓPIA ISOLADA dos pesos treinados de rosto para transfer learning
    weights_path = os.path.join(base_dir, 'models', 'base_face_weights.pt')
    if not os.path.exists(weights_path):
        weights_path = os.path.join(base_dir, 'models', 'yolo26n.pt')
        print(f"[Aviso] Cópia de pesos não encontrada. Usando modelo base: {weights_path}")
        
    # 2. Descritor do dataset (YOLO): prefere o arquivo gerado pelo script de
    # download/treino (scripts/data.yaml, com o caminho absoluto do dataset local)
    # e cai para o modelo versionado em config/data.yaml (caminho relativo).
    data_yaml = os.path.join(base_dir, 'scripts', 'data.yaml')
    if not os.path.exists(data_yaml):
        data_yaml = os.path.join(base_dir, 'config', 'data.yaml')
    runs_dir = os.path.join(base_dir, 'runs')

    if not os.path.exists(data_yaml):
        print(f"[ERRO] Descritor do dataset não encontrado em "
              f"{os.path.join(base_dir, 'scripts', 'data.yaml')} nem em "
              f"{os.path.join(base_dir, 'config', 'data.yaml')}")
        print("       Rode scripts/treinar_crowdhuman.py para baixar o dataset e gerar o descritor.")
        sys.exit(1)

    print("==================================================================")
    print("      TREINAMENTO YOLOv26 - CORPO INTEIRO (TRANSFER LEARNING)")
    print("==================================================================")
    print(f"--> Pesos Iniciais (Cópia Isolada): {weights_path}")
    print(f"--> Configuração Dataset:           {data_yaml}")
    print(f"--> Pasta de Saída (Isolada):       {runs_dir}")
    print("==================================================================")

    # Carrega a cópia dos pesos na memória (sem alterar o arquivo original de rosto)
    model = YOLO(weights_path)

    # Hiperparâmetros otimizados para detecção de corpo inteiro
    model.train(
        data=data_yaml,
        epochs=300,
        imgsz=640,          # 640px para capturar corpo inteiro e proporção anatômica
        batch=8,            # Tamanho do lote estável
        patience=50,        # Early stopping
        cos_lr=True,        # Agendador de decaimento cosseno
        box=8.5,            # Peso para ajuste fino da caixa de corpo
        cls=0.8,            # Sensibilidade da classe 'person'
        dfl=2.0,            # Refinamento de bordas
        workers=0,          # Compatível com Windows
        project=os.path.join(runs_dir, 'detect'),
        name='train_crowdhuman_body',
        exist_ok=True
    )

if __name__ == "__main__":
    main()
