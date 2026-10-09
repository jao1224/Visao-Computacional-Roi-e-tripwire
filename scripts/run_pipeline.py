import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Download e Preparação do Dataset
    print("\n=======================================================")
    print("   ETAPA 1: DOWNLOAD E PREPARAÇÃO DO DATASET CROWDHUMAN")
    print("=======================================================\n")
    download_script = os.path.join(base_dir, 'scripts', 'download_and_convert_crowdhuman.py')
    res = subprocess.run([sys.executable, download_script], check=True)

    # 2. Iniciar Treinamento
    print("\n=======================================================")
    print("   ETAPA 2: INICIANDO TREINAMENTO YOLOv26 CORPO")
    print("=======================================================\n")
    train_script = os.path.join(base_dir, 'scripts', 'train_body.py')
    subprocess.run([sys.executable, train_script], check=True)

if __name__ == "__main__":
    main()
