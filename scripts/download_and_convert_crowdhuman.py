import os
import sys
import json
import zipfile
import urllib3
import requests
from PIL import Image

# Desabilitar avisos SSL para redes com proxy/certificados locais
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
CACHE_DIR = os.path.join(DATASET_DIR, 'downloads_cache')

HF_BASE_URL = "https://huggingface.co/datasets/sshao0516/CrowdHuman/resolve/main"

FILES_TO_DOWNLOAD = [
    ("annotation_val.odgt", "annotation_val.odgt"),
    ("annotation_train.odgt", "annotation_train.odgt"),
    ("CrowdHuman_val.zip", "CrowdHuman_val.zip"),
    ("CrowdHuman_train01.zip", "CrowdHuman_train01.zip"),
    ("CrowdHuman_train02.zip", "CrowdHuman_train02.zip"),
    ("CrowdHuman_train03.zip", "CrowdHuman_train03.zip"),
]

def download_file(filename, output_path):
    """Download resiliente com suporte a retomar download e bypass SSL."""
    url = f"{HF_BASE_URL}/{filename}"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Se já baixou completamente
    if os.path.exists(output_path):
        remote_size = 0
        try:
            head = requests.head(url, verify=False, timeout=10)
            remote_size = int(head.headers.get('content-length', 0))
        except Exception:
            pass
        
        local_size = os.path.getsize(output_path)
        if remote_size > 0 and local_size == remote_size:
            print(f"[OK] Já baixado: {filename} ({local_size / (1024*1024):.1f} MB)")
            return True

    print(f"\n--> Baixando {filename} de {url}...")
    headers = {}
    mode = 'wb'
    initial_pos = 0

    response = requests.get(url, headers=headers, stream=True, verify=False, timeout=30)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))

    downloaded = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(output_path, mode) as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    if int(pct) % 10 == 0:
                        print(f"    {filename}: {downloaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB ({pct:.1f}%)", end='\r')

    print(f"\n[OK] Concluído: {filename} ({os.path.getsize(output_path) / (1024*1024):.1f} MB)")
    return True

def extract_zip(zip_path, extract_to):
    """Extrai arquivo zip."""
    if not os.path.exists(zip_path):
        print(f"[Aviso] Zip não encontrado: {zip_path}")
        return False
    print(f"--> Extraindo {os.path.basename(zip_path)} para {extract_to}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"[OK] Extraído com sucesso: {os.path.basename(zip_path)}")
    return True

def flatten_directory(parent_dir):
    """Move imagens de subpastas 'Images/' para a pasta principal."""
    sub_images = os.path.join(parent_dir, 'Images')
    if os.path.exists(sub_images):
        for f in os.listdir(sub_images):
            src = os.path.join(sub_images, f)
            dst = os.path.join(parent_dir, f)
            if not os.path.exists(dst):
                try:
                    os.rename(src, dst)
                except Exception:
                    pass

def convert_odgt_to_yolo(odgt_path, images_dir, labels_output_dir):
    """Converte anotações fbox para formato YOLO .txt (x_center, y_center, w, h)."""
    os.makedirs(labels_output_dir, exist_ok=True)
    if not os.path.exists(odgt_path):
        print(f"[Aviso] Arquivo de anotação não encontrado: {odgt_path}")
        return 0

    converted_count = 0
    with open(odgt_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            image_id = data.get('ID')
            img_path = os.path.join(images_dir, f"{image_id}.jpg")
            
            if not os.path.exists(img_path):
                img_path_alt = os.path.join(images_dir, 'Images', f"{image_id}.jpg")
                if os.path.exists(img_path_alt):
                    img_path = img_path_alt
                else:
                    continue

            try:
                with Image.open(img_path) as img:
                    img_w, img_h = img.size
            except Exception:
                continue

            yolo_lines = []
            for box in data.get('gtboxes', []):
                tag = box.get('tag', 'person')
                if tag != 'person':
                    continue

                fbox = box.get('fbox') # Corpo inteiro
                if not fbox:
                    continue

                x, y, w, h = fbox
                if w <= 0 or h <= 0:
                    continue

                x_center = max(0.0, min(1.0, (x + w / 2.0) / img_w))
                y_center = max(0.0, min(1.0, (y + h / 2.0) / img_h))
                norm_w = max(0.0, min(1.0, w / float(img_w)))
                norm_h = max(0.0, min(1.0, h / float(img_h)))

                yolo_lines.append(f"0 {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

            label_file = os.path.join(labels_output_dir, f"{image_id}.txt")
            with open(label_file, 'w', encoding='utf-8') as out_f:
                out_f.write("\n".join(yolo_lines))

            converted_count += 1

    print(f"[OK] Convertidas {converted_count} anotações em {labels_output_dir}")
    return converted_count

def main():
    print("==================================================================")
    print("      DOWNLOAD E PREPARAÇÃO DO DATASET CROWDHUMAN (CORPO)")
    print("==================================================================")
    
    os.makedirs(CACHE_DIR, exist_ok=True)
    train_img_dir = os.path.join(DATASET_DIR, 'images', 'train')
    val_img_dir = os.path.join(DATASET_DIR, 'images', 'val')
    train_lbl_dir = os.path.join(DATASET_DIR, 'labels', 'train')
    val_lbl_dir = os.path.join(DATASET_DIR, 'labels', 'val')

    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(train_lbl_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)

    # 1. Download de anotações e validação primeiro
    for remote_name, local_name in FILES_TO_DOWNLOAD:
        local_path = os.path.join(CACHE_DIR, local_name)
        download_file(remote_name, local_path)

    # 2. Extrair Validação
    val_zip = os.path.join(CACHE_DIR, 'CrowdHuman_val.zip')
    extract_zip(val_zip, val_img_dir)
    flatten_directory(val_img_dir)

    # 3. Extrair Treino
    for tz in ['CrowdHuman_train01.zip', 'CrowdHuman_train02.zip', 'CrowdHuman_train03.zip']:
        train_zip = os.path.join(CACHE_DIR, tz)
        if os.path.exists(train_zip):
            extract_zip(train_zip, train_img_dir)
    flatten_directory(train_img_dir)

    # 4. Converter anotações
    train_odgt = os.path.join(CACHE_DIR, 'annotation_train.odgt')
    val_odgt = os.path.join(CACHE_DIR, 'annotation_val.odgt')

    print("\nConvertendo anotações de Validação...")
    convert_odgt_to_yolo(val_odgt, val_img_dir, val_lbl_dir)

    print("\nConvertendo anotações de Treino...")
    convert_odgt_to_yolo(train_odgt, train_img_dir, train_lbl_dir)

    print("\n==================================================================")
    print("Dataset CrowdHuman pronto!")
    print("Iniciando treinamento automaticamente...")
    print("==================================================================")

if __name__ == "__main__":
    main()
