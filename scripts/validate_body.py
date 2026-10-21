import os
import sys
from ultralytics import YOLO

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Busca o melhor modelo treinado
    model_path = os.path.join(base_dir, 'runs', 'detect', 'train_crowdhuman_body', 'weights', 'best.pt')
    if not os.path.exists(model_path):
        # Fallback para o modelo base se ainda não treinou
        model_path = os.path.join(base_dir, 'models', 'yolo26n.pt')
        print(f"[Aviso] Modelo treinado não encontrado. Avaliando modelo base: {model_path}")
    else:
        print(f"--> Carregando modelo treinado: {model_path}")
        
    # Descritor do dataset (YOLO): prefere o arquivo gerado pelo script de
    # download/treino (scripts/data.yaml, com o caminho absoluto do dataset local)
    # e cai para o modelo versionado em config/data.yaml (caminho relativo).
    data_yaml = os.path.join(base_dir, 'scripts', 'data.yaml')
    if not os.path.exists(data_yaml):
        data_yaml = os.path.join(base_dir, 'config', 'data.yaml')
    val_output_dir = os.path.join(base_dir, 'runs', 'detect', 'val_results')

    if not os.path.exists(data_yaml):
        print(f"[ERRO] Descritor do dataset não encontrado em "
              f"{os.path.join(base_dir, 'scripts', 'data.yaml')} nem em "
              f"{os.path.join(base_dir, 'config', 'data.yaml')}")
        print("       Rode scripts/treinar_crowdhuman.py para baixar o dataset e gerar o descritor.")
        sys.exit(1)

    print(f"--> Executando validação oficial (model.val) no dataset CrowdHuman...")
    model = YOLO(model_path)
    metrics = model.val(
        data=data_yaml,
        split='val',
        imgsz=640,
        batch=16,
        device=0,
        project=val_output_dir,
        name='val_body',
        exist_ok=True
    )

    print("\n================ RESULTADOS DA VALIDAÇÃO (CORPO) ================")
    print(f"mAP@0.5:        {metrics.box.map50:.4f} ({metrics.box.map50*100:.2f}%)")
    print(f"mAP@0.5:0.95:   {metrics.box.map:.4f} ({metrics.box.map*100:.2f}%)")
    print(f"Precisão (P):   {metrics.box.mp:.4f} ({metrics.box.mp*100:.2f}%)")
    print(f"Recall (R):     {metrics.box.mr:.4f} ({metrics.box.mr*100:.2f}%)")
    print(f"F1-Score:       {2 * (metrics.box.mp * metrics.box.mr) / (metrics.box.mp + metrics.box.mr + 1e-16):.4f}")
    print("==================================================================")

if __name__ == "__main__":
    main()
