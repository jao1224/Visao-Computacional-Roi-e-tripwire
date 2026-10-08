import os
from ultralytics import YOLO

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Busca o melhor modelo treinado
    model_path = os.path.join(base_dir, 'runs', 'detect', 'train_crowdhuman_body', 'weights', 'best.pt')
    if not os.path.exists(model_path):
        # Fallback para o modelo base se ainda não treinou
        root_dir = os.path.dirname(base_dir)
        model_path = os.path.join(root_dir, 'models', 'yolo26n.pt')
        print(f"[Aviso] Modelo treinado não encontrado. Avaliando modelo base: {model_path}")
    else:
        print(f"--> Carregando modelo treinado: {model_path}")
        
    data_yaml = os.path.join(base_dir, 'data.yaml')
    val_output_dir = os.path.join(base_dir, 'runs', 'detect', 'val_results')

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
