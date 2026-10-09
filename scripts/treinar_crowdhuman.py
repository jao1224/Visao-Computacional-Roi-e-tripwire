import sys
import os
import time
import json
import zipfile
import urllib3
import requests
import torch
from PIL import Image
from huggingface_hub import snapshot_download
from ultralytics import YOLO

# Desabilitar avisos SSL
urllib3.disable_warnings()

def main():
    print("==================================================", flush=True)
    print(f"[STATUS] Execução Iniciada - Hora: {time.strftime('%H:%M:%S')}", flush=True)
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
    RUNS_DIR = os.path.join(BASE_DIR, 'runs', 'detect')
    WEIGHTS_INIT = os.path.join(BASE_DIR, 'models', 'base_face_weights.pt')
    
    os.makedirs(RUNS_DIR, exist_ok=True)
    
    # 1. Hardware Check
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[GPU ATIVA] {gpu_name} ({vram:.1f} GB VRAM)", flush=True)
    else:
        print("[AVISO] GPU não detectada no momento (usando CPU)", flush=True)
    print("==================================================", flush=True)

    # 2. Pesos Anteriores (Transfer Learning)
    if not os.path.exists(WEIGHTS_INIT):
        alt_path = os.path.join(os.path.dirname(BASE_DIR), 'runs', 'detect', 'train-14', 'weights', 'best.pt')
        if os.path.exists(alt_path):
            os.makedirs(os.path.dirname(WEIGHTS_INIT), exist_ok=True)
            import shutil
            shutil.copy2(alt_path, WEIGHTS_INIT)
            print(f"[OK] Pesos copiados para: {WEIGHTS_INIT}", flush=True)
        else:
            WEIGHTS_INIT = 'yolo26n.pt'
    
    print(f"[OK] Modelo inicial carregado: {WEIGHTS_INIT}", flush=True)
    model = YOLO(WEIGHTS_INIT)

    # 3. Dataset Download e Conversão
    train_img_dir = os.path.join(DATASET_DIR, 'images', 'train')
    val_img_dir = os.path.join(DATASET_DIR, 'images', 'val')
    train_lbl_dir = os.path.join(DATASET_DIR, 'labels', 'train')
    val_lbl_dir = os.path.join(DATASET_DIR, 'labels', 'val')

    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(train_lbl_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)

    print("\n--> Baixando dataset CrowdHuman do Hugging Face...", flush=True)
    try:
        local_dir = snapshot_download(
            repo_id='sshao0516/CrowdHuman',
            repo_type='dataset',
            allow_patterns=['*.zip', '*.odgt']
        )
        print(f"[OK] Cache baixado em: {local_dir}", flush=True)

        def extract_zip(zip_path, extract_to):
            if os.path.exists(zip_path):
                print(f"Extraindo {os.path.basename(zip_path)}...", flush=True)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(extract_to)

        extract_zip(os.path.join(local_dir, 'CrowdHuman_val.zip'), val_img_dir)
        for tz in ['CrowdHuman_train01.zip', 'CrowdHuman_train02.zip', 'CrowdHuman_train03.zip']:
            extract_zip(os.path.join(local_dir, tz), train_img_dir)

        for p in [train_img_dir, val_img_dir]:
            sub = os.path.join(p, 'Images')
            if os.path.exists(sub):
                for f in os.listdir(sub):
                    os.rename(os.path.join(sub, f), os.path.join(p, f))

        def convert_odgt(odgt_path, img_dir, lbl_dir):
            if not os.path.exists(odgt_path): return
            with open(odgt_path, 'r', encoding='utf-8') as f:
                for line in f:
                    d = json.loads(line.strip())
                    img_id = d.get('ID')
                    img_path = os.path.join(img_dir, f'{img_id}.jpg')
                    if not os.path.exists(img_path): continue
                    try:
                        with Image.open(img_path) as img: w_img, h_img = img.size
                    except Exception:
                        continue
                    lines = []
                    for b in d.get('gtboxes', []):
                        if b.get('tag') == 'person' and b.get('fbox'):
                            x, y, w, h = b.get('fbox')
                            if w > 0 and h > 0:
                                xc = max(0.0, min(1.0, (x + w/2.0)/w_img))
                                yc = max(0.0, min(1.0, (y + h/2.0)/h_img))
                                nw = max(0.0, min(1.0, w/float(w_img)))
                                nh = max(0.0, min(1.0, h/float(h_img)))
                                lines.append(f'0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}')
                    with open(os.path.join(lbl_dir, f'{img_id}.txt'), 'w', encoding='utf-8') as out_f:
                        out_f.write('\n'.join(lines))

        print("--> Convertendo anotações para formato YOLO...", flush=True)
        convert_odgt(os.path.join(local_dir, 'annotation_val.odgt'), val_img_dir, val_lbl_dir)
        convert_odgt(os.path.join(local_dir, 'annotation_train.odgt'), train_img_dir, train_lbl_dir)
        print("[OK] Dataset pronto!", flush=True)
    except Exception as e:
        print(f"[Aviso download] {e}", flush=True)

    # 4. Configurar data.yaml
    yaml_path = os.path.join(BASE_DIR, 'data.yaml')
    yaml_content = f"path: {DATASET_DIR}\ntrain: images/train\nval: images/val\nnc: 1\nnames: ['person']"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    # 5. Iniciar Treino
    batch_size = 32 if (torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory > 15*(1024**3)) else 8
    print(f"\n--> Iniciando Treinamento YOLOv26 (batch={batch_size}, imgsz=640)...", flush=True)
    
    model.train(
        data=yaml_path,
        epochs=300,
        imgsz=640,
        batch=batch_size,
        patience=50,
        cos_lr=True,
        box=10.0,
        cls=0.7,
        dfl=2.0,
        device=0 if torch.cuda.is_available() else 'cpu',
        project=RUNS_DIR,
        name='train_crowdhuman_body',
        exist_ok=True
    )
    print("\n[OK] Treinamento Concluído com Sucesso!", flush=True)

if __name__ == "__main__":
    main()
