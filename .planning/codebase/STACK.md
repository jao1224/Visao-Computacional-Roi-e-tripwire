# Pilha Tecnológica

**Data da Análise:** 2026-10-08

## Linguagens

**Principal:**
- Python 3.11.9 - Todo o código da aplicação (`main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`, `scripts/*.py`). Não existe fixação em `.python-version`/`pyproject.toml`; 3.11.9 é o interpretador na máquina de análise.

**Secundária:**
- Jupyter Notebook / IPython (variante Google Colab) - variante de treinamento em GPU: `treinar_crowdhuman_colab.ipynb`
- YAML - Apenas configuração de dataset e execução: `data.yaml`, `runs/detect/train_crowdhuman_body/args.yaml`

## Ambiente de Execução

**Ambiente:**
- CPython 3.11 no Windows (treinamento/inferência local; acesso à webcam via `cv2.VideoCapture(0)`, `workers=0` definido explicitamente "Compatível com Windows" em `scripts/train_body.py:39`)
- Google Colab (Linux, GPU CUDA) - ambiente de treinamento alternativo via `treinar_crowdhuman_colab.ipynb`
- GPU CUDA/PyTorch opcional - `treinar_crowdhuman.py:28-33` verifica `torch.cuda.is_available()` e recorre à CPU; `scripts/validate_body.py:27` define `device=0` de forma fixa (GPU obrigatória para validação)

**Gerenciador de Pacotes:**
- pip (Python do sistema)
- Lockfile: **ausente** - não há `requirements.txt`, `pyproject.toml`, `environment.yml`, `Pipfile` ou `poetry.lock` em nenhum lugar do repositório. As dependências são apenas implícitas pelos imports.

## Frameworks

**Núcleo:**
- Ultralytics YOLO `8.3.169` - treinamento, validação e inferência de detecção de objetos (arquitetura YOLOv26 nano, pesos base `yolo26n.pt`). Usado em `main.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `treinar_crowdhuman.py`
- PyTorch `2.6.0` (+ `torchvision 0.21.0`) - backend de tensores/GPU sob o Ultralytics; uso direto em `treinar_crowdhuman.py:8,28-31,125,138`
- OpenCV (`opencv-python 4.12.0.88`) - captura de webcam, desenho, sobreposição de HUD, janela de exibição em `main.py`
- Hugging Face Hub (`huggingface-hub 0.34.1`) - download do dataset via `snapshot_download` em `treinar_crowdhuman.py:10,63-67`

**Testes:**
- Não detectado - nenhum framework de testes, nenhum arquivo `*.test.*`/`*.spec.*`, nenhuma configuração de pytest/unittest.

**Build/Dev:**
- Não detectado - nenhuma etapa de build, nenhuma configuração de linter/formatter (sem `.eslintrc`, `ruff`, `black`, `flake8`, `mypy`).
- O notebook do Google Colab atua como o ambiente de dev/CI de facto para execuções em GPU (`treinar_crowdhuman_colab.ipynb` instala via `!pip install -q ultralytics huggingface_hub pillow`).

## Dependências Principais

**Críticas:**
- `ultralytics` 8.3.169 - Tudo: carregamento de modelo, `.train()`, `.val()`, inferência. A versão importa: a nomenclatura de modelo "YOLOv26" (`yolo26n.pt`) só existe em versões recentes da série 8.3.x.
- `torch` 2.6.0 / `torchvision` 0.21.0 - Motor de treinamento, kernels CUDA, AMP (`amp: true` em `runs/detect/train_crowdhuman_body/args.yaml:29`).
- `opencv-python` 4.12.0.88 - Laço de webcam em tempo real em `main.py`.
- `huggingface-hub` 0.34.1 - Obtenção do dataset CrowdHuman (caminho alternativo ao HTTP bruto).
- `requests` 2.32.4 + `urllib3` 2.6.3 - Download do dataset em streaming com retomada/verificação de tamanho e supressão de avisos de TLS (`scripts/download_and_convert_crowdhuman.py:5,10`).
- `pillow` 11.0.0 - Leitura das dimensões das imagens durante a conversão `.odgt` → rótulos YOLO (`scripts/download_and_convert_crowdhuman.py:117`, `treinar_crowdhuman.py:95`).

**Infraestrutura:**
- Apenas stdlib do Python para orquestração - `subprocess` (`run_pipeline.py:13,20`), `zipfile`, `json`, `os`, `urllib.request` (`scripts/setup_colab_ssh.py:2`).
- `numpy` 2.1.3 (transitiva, exigida por ultralytics/opencv).

**Artefatos do modelo (binários, versionados):**
- `yolo26n.pt` (5.3 MB) - pesos base YOLOv26-nano
- `models/base_face_weights.pt` (5.3 MB) - cópia isolada dos pesos treinados para rostos, usada como inicialização de transfer learning (`scripts/train_body.py:8`)
- `resultados/best.pt`, `resultados/best (1).pt` (5.2 MB cada) - detectores de corpo treinados; o primeiro candidato é carregado por `main.py:12`

## Configuração

**Ambiente:**
- Nenhuma variável de ambiente e nenhum arquivo `.env` - o projeto é totalmente autoconfigurável a partir dos caminhos de arquivos.
- A configuração é baseada em caminhos: cada script calcula `base_dir` via `os.path.dirname(os.path.abspath(__file__))` e resolve os recursos relativamente a ele.

**Arquivos de configuração de build/execução:**
- `data.yaml` - configuração de dataset do Ultralytics: classe única `person`, `train: images/train`, `val: images/val`. **Contém um caminho absoluto fixo de outra máquina** (`path: C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\dataset`); `treinar_crowdhuman.py:118-122` o reescreve em tempo de execução, mas `scripts/train_body.py` e `scripts/validate_body.py` o leem como está.
- `runs/detect/train_crowdhuman_body/args.yaml` - instantâneo gerado pelo Ultralytics da última execução de treinamento (hiperparâmetros: `epochs: 300`, `imgsz: 640`, `batch: 8`, `patience: 50`, `cos_lr: true`, `box: 8.5`, `cls: 0.8`, `dfl: 2.0`). Também contém os caminhos absolutos de outra máquina.
- `scripts/train_body.py:29-43` - a fonte autoritativa de hiperparâmetros para o caminho do pipeline.
- `treinar_crowdhuman.py:128-142` - um segundo conjunto de hiperparâmetros divergente (`box: 10.0`, `cls: 0.7`, `batch` dinâmico, `device=0`).

## Requisitos da Plataforma

**Desenvolvimento:**
- Windows 10/11 com Python 3.11+, uma webcam para `main.py`
- Qualquer plataforma para preparação/treinamento do dataset, exceto: `scripts/validate_body.py` requer uma GPU CUDA (`device=0`)
- Opcional: conta Google para treinamento em GPU no Colab (`treinar_crowdhuman_colab.ipynb`)
- Opcional: cliente SSH + `cloudflared.exe` para a ponte SSH do Colab (`scripts/setup_colab_ssh.py`)

**Produção:**
- Nenhum alvo de implantação - este é um projeto local de pesquisa/CLI. Os pontos de entrada são executados manualmente:
  - `python run_pipeline.py` (download + treinamento, via `subprocess`)
  - `python main.py` (inferência por webcam)
  - `python scripts/validate_body.py` (métricas)
- Google Colab + Google Drive para persistência do treinamento em nuvem (`/content/drive/MyDrive/yolo_crowdhuman_treinamento/runs` em `treinar_crowdhuman_colab.ipynb`)
- Sem Docker, sem CI, sem metadados de empacotamento.

---

*Análise da pilha: 2026-10-08*
*Atualizar após mudanças principais de dependências*
