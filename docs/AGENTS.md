<!-- GSD:project-start source:PROJECT.md -->
## Project

**Visão Computacional para Hotelaria (Analytics de Fluxo)**

Sistema de inteligência artificial com visão computacional que transforma câmeras de segurança convencionais do hotel em sensores de inteligência de negócios: contagem de pessoas por zona, tempo de permanência (dwell time), mapas de calor e ocupação em tempo real. Usuário final: gestão do hotel (equipes operacionais, recepção, segurança). Desenvolvimento parte do detector de corpo atual (`main.py`, YOLO CrowdHuman) e evolui conforme a documentação em `DOCUMENTACAO_PROJETO_E_LGPD/`.

**Core Value:** Contagem, fluxo e permanência por zona — confiáveis e em tempo real — com **zero biometria**: usar somente detecção de corpo/silhueta, mantendo o sistema 100% conforme a LGPD.

### Constraints

- **LGPD**: somente detecção de corpo (sem biometria); frames nunca persistidos; métricas anonimizadas (Art. 6º III, Art. 12)
- **Performance**: latência ≤ 5 ms por frame em GPU; I/O de banco nunca dentro do loop de vídeo (doc 08)
- **Marco Civil**: logs de acesso à API por 6 meses sob sigilo (Art. 15)
- **Idioma**: código e mensagens em português (pt-BR), convenções atuais do repo
- **Hardware**: GPU NVIDIA para inferência (~320 FPS); desenvolvimento local pode usar CPU/webcam
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Linguagens
- Python 3.11.9 - Todo o código da aplicação (`main.py` — arquivo principal; `run_pipeline.py`, `treinar_crowdhuman.py`, `scripts/*.py` — apenas para teste). Não existe fixação em `.python-version`/`pyproject.toml`; 3.11.9 é o interpretador na máquina de análise.
- Jupyter Notebook / IPython (variante Google Colab) - variante de treinamento em GPU: `treinar_crowdhuman_colab.ipynb`
- YAML - Apenas configuração de dataset e execução: `data.yaml`, `runs/detect/train_crowdhuman_body/args.yaml`
## Ambiente de Execução
- CPython 3.11 no Windows (treinamento/inferência local; acesso à webcam via `cv2.VideoCapture(0)`, `workers=0` definido explicitamente "Compatível com Windows" em `scripts/train_body.py:39`)
- Google Colab (Linux, GPU CUDA) - ambiente de treinamento alternativo via `treinar_crowdhuman_colab.ipynb`
- GPU CUDA/PyTorch opcional - `treinar_crowdhuman.py:28-33` verifica `torch.cuda.is_available()` e recorre à CPU; `scripts/validate_body.py:27` define `device=0` de forma fixa (GPU obrigatória para validação)
- pip (Python do sistema)
- Lockfile: **ausente** - não há `requirements.txt`, `pyproject.toml`, `environment.yml`, `Pipfile` ou `poetry.lock` em nenhum lugar do repositório. As dependências são apenas implícitas pelos imports.
## Frameworks
- Ultralytics YOLO `8.3.169` - treinamento, validação e inferência de detecção de objetos (arquitetura YOLOv26 nano, pesos base `yolo26n.pt`). Usado em `main.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `treinar_crowdhuman.py`
- PyTorch `2.6.0` (+ `torchvision 0.21.0`) - backend de tensores/GPU sob o Ultralytics; uso direto em `treinar_crowdhuman.py:8,28-31,125,138`
- OpenCV (`opencv-python 4.12.0.88`) - captura de webcam, desenho, sobreposição de HUD, janela de exibição em `main.py`
- Hugging Face Hub (`huggingface-hub 0.34.1`) - download do dataset via `snapshot_download` em `treinar_crowdhuman.py:10,63-67`
- Não detectado - nenhum framework de testes, nenhum arquivo `*.test.*`/`*.spec.*`, nenhuma configuração de pytest/unittest.
- Não detectado - nenhuma etapa de build, nenhuma configuração de linter/formatter (sem `.eslintrc`, `ruff`, `black`, `flake8`, `mypy`).
- O notebook do Google Colab atua como o ambiente de dev/CI de facto para execuções em GPU (`treinar_crowdhuman_colab.ipynb` instala via `!pip install -q ultralytics huggingface_hub pillow`).
## Dependências Principais
- `ultralytics` 8.3.169 - Tudo: carregamento de modelo, `.train()`, `.val()`, inferência. A versão importa: a nomenclatura de modelo "YOLOv26" (`yolo26n.pt`) só existe em versões recentes da série 8.3.x.
- `torch` 2.6.0 / `torchvision` 0.21.0 - Motor de treinamento, kernels CUDA, AMP (`amp: true` em `runs/detect/train_crowdhuman_body/args.yaml:29`).
- `opencv-python` 4.12.0.88 - Laço de webcam em tempo real em `main.py`.
- `huggingface-hub` 0.34.1 - Obtenção do dataset CrowdHuman (caminho alternativo ao HTTP bruto).
- `requests` 2.32.4 + `urllib3` 2.6.3 - Download do dataset em streaming com retomada/verificação de tamanho e supressão de avisos de TLS (`scripts/download_and_convert_crowdhuman.py:5,10`).
- `pillow` 11.0.0 - Leitura das dimensões das imagens durante a conversão `.odgt` → rótulos YOLO (`scripts/download_and_convert_crowdhuman.py:117`, `treinar_crowdhuman.py:95`).
- Apenas stdlib do Python para orquestração - `subprocess` (`run_pipeline.py:13,20`), `zipfile`, `json`, `os`, `urllib.request` (`scripts/setup_colab_ssh.py:2`).
- `numpy` 2.1.3 (transitiva, exigida por ultralytics/opencv).
- `yolo26n.pt` (5.3 MB) - pesos base YOLOv26-nano
- `models/base_face_weights.pt` (5.3 MB) - cópia isolada dos pesos treinados para rostos, usada como inicialização de transfer learning (`scripts/train_body.py:8`)
- `resultados/best.pt`, `resultados/best (1).pt` (5.2 MB cada) - detectores de corpo treinados; o primeiro candidato é carregado por `main.py:12`
## Configuração
- Nenhuma variável de ambiente e nenhum arquivo `.env` - o projeto é totalmente autoconfigurável a partir dos caminhos de arquivos.
- A configuração é baseada em caminhos: cada script calcula `base_dir` via `os.path.dirname(os.path.abspath(__file__))` e resolve os recursos relativamente a ele.
- `data.yaml` - configuração de dataset do Ultralytics: classe única `person`, `train: images/train`, `val: images/val`. **Contém um caminho absoluto fixo de outra máquina** (`path: C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\dataset`); `treinar_crowdhuman.py:118-122` o reescreve em tempo de execução, mas `scripts/train_body.py` e `scripts/validate_body.py` o leem como está.
- `runs/detect/train_crowdhuman_body/args.yaml` - instantâneo gerado pelo Ultralytics da última execução de treinamento (hiperparâmetros: `epochs: 300`, `imgsz: 640`, `batch: 8`, `patience: 50`, `cos_lr: true`, `box: 8.5`, `cls: 0.8`, `dfl: 2.0`). Também contém os caminhos absolutos de outra máquina.
- `scripts/train_body.py:29-43` - a fonte autoritativa de hiperparâmetros para o caminho do pipeline.
- `treinar_crowdhuman.py:128-142` - um segundo conjunto de hiperparâmetros divergente (`box: 10.0`, `cls: 0.7`, `batch` dinâmico, `device=0`).
## Requisitos da Plataforma
- Windows 10/11 com Python 3.11+, uma webcam para `main.py`
- Qualquer plataforma para preparação/treinamento do dataset, exceto: `scripts/validate_body.py` requer uma GPU CUDA (`device=0`)
- Opcional: conta Google para treinamento em GPU no Colab (`treinar_crowdhuman_colab.ipynb`)
- Opcional: cliente SSH + `cloudflared.exe` para a ponte SSH do Colab (`scripts/setup_colab_ssh.py`)
- Nenhum alvo de implantação - este é um projeto local de pesquisa/CLI. Os pontos de entrada são executados manualmente:
- Google Colab + Google Drive para persistência do treinamento em nuvem (`/content/drive/MyDrive/yolo_crowdhuman_treinamento/runs` em `treinar_crowdhuman_colab.ipynb`)
- Sem Docker, sem CI, sem metadados de empacotamento.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Padrões de Nomenclatura
- `snake_case.py` para todos os arquivos Python, mas os nomes são **de idioma misto**: inglês para scripts de pipeline (`run_pipeline.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `scripts/download_and_convert_crowdhuman.py`) e português para scripts de nível raiz/treinamento (`treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`)
- Regra geral: mantenha os nomes de arquivos existentes como estão; nomeie **novos** arquivos em inglês `snake_case` ao adicionar em `scripts/`
- Configuração: `data.yaml` (raiz) para a configuração de dataset do Ultralytics
- Não existem arquivos de teste em lugar nenhum (veja `TESTING.md`)
- `snake_case` em todo lugar: `main()`, `download_file()`, `extract_zip()`, `flatten_directory()`, `convert_odgt_to_yolo()`
- Todo script executável expõe uma única entrada `main()` protegida por `if __name__ == "__main__":` (veja `main.py:87`, `run_pipeline.py:22`, `scripts/train_body.py:45`, `scripts/validate_body.py:41`, `treinar_crowdhuman.py:145`)
- Auxiliares pequenos definidos **aninhados dentro de `main()`** quando usados apenas lá (`extract_zip`, `convert_odgt` em `treinar_crowdhuman.py:70,86`) ou no escopo do módulo quando compartilhados (`download_and_convert_crowdhuman.py:27-150`)
- `scripts/setup_colab_ssh.py` é o único script **sem** `main()` — é código puramente procedural de nível superior
- `camelCase` para variáveis locais/de caminho: estilo `weightsPath` nunca usado; o estilo real é `weights_path`, `train_img_dir`, `val_lbl_dir`, `modelo_path`, `downloaded`
- `UPPER_SNAKE_CASE` apenas para constantes de módulo: `BASE_DIR`, `DATASET_DIR`, `CACHE_DIR`, `HF_BASE_URL`, `FILES_TO_DOWNLOAD` (`scripts/download_and_convert_crowdhuman.py:12-25`)
- Desvio: `treinar_crowdhuman.py:20-23` usa `UPPER_SNAKE_CASE` para variáveis **locais** dentro de `main()`; `main.py:7` e `scripts/train_body.py:5` usam `base_dir` minúsculo para o mesmo valor. Prefira `base_dir`/`root_dir` minúsculos para locais em código novo; mantenha `UPPER_SNAKE_CASE` para constantes verdadeiras de módulo.
- Identificadores em português aparecem para variáveis de domínio: `candidatos`, `modelo_path`, `num_pessoas`, `webcam` (`main.py:11-28`). Adapte-se ao idioma do arquivo ao redor.
- Não se aplica — a base de código é Python sem tipagem (sem anotações de tipo em lugar nenhum)
## Estilo de Código
- Nenhum formatador configurado (sem `black`, `ruff format`, equivalente a `.prettierrc`). Combine o estilo manual: indentação de 4 espaços, linhas de ~100-120 caracteres
- As aspas são **inconsistentes**: aspas simples predominam para caminhos/strings curtas (`'resultados'`, `'best.pt'`), aspas duplas nas f-strings de `download_and_convert_crowdhuman.py` e no notebook. Prefira aspas simples para código novo, a menos que a linha contenha apóstrofos/aspas simples internas
- Vírgulas finais não são usadas; linha em branco separa etapas numeradas
- Nenhum configurado (sem `.flake8`, `.pylintrc`, `ruff`/`black`/`mypy` em qualquer arquivo de configuração; sem `requirements.txt`, `pyproject.toml` ou `setup.cfg`)
- Se for introduzir um linter, adicione `ruff` com um `pyproject.toml` na raiz do repositório em vez de empilhar várias ferramentas
## Organização de Imports
- Um bloco só, stdlib primeiro e depois terceiros, sem linhas em branco entre grupos (`treinar_crowdhuman.py:1-11`)
- Imports inline ocorrem no meio da função quando necessários de forma preguiçosa: `import shutil` em `treinar_crowdhuman.py:41`; células do notebook importam por célula (`treinar_crowdhuman_colab.ipynb` células 1, 3, 4). Aceitável em notebooks; coloque os imports no topo em arquivos `.py`.
- Nenhum. Todos os caminhos resolvidos com `os.path.join` relativo a `os.path.dirname(os.path.abspath(__file__))`
## Tratamento de Erros
- Falha suave / continuar apesar do erro: `try/except Exception` amplo que imprime um aviso e prossegue (`treinar_crowdhuman.py:115-116`, `download_and_convert_crowdhuman.py:35-39,116-120`, célula 4 do notebook)
- Retornos antecipados por guarda de condição para condições fatais com mensagem impressa e `return` — nunca exceções levantadas (`main.py:19-22` modelo ausente, `main.py:29-31` falha ao abrir a webcam)
- Cadeias de fallback em vez de exceções: lista de caminhos candidatos resolvida com `next((p for p in candidatos if os.path.exists(p)), None)` (`main.py:11-19`) ou `if not os.path.exists(...)` com fallback para os pesos base e impressão com `[Aviso]` (`scripts/train_body.py:9-12`, `scripts/validate_body.py:9-13`)
- Etapas de subprocesso usam `check=True` para que falhas abortem o pipeline (`run_pipeline.py:13,20`)
- HTTP: `response.raise_for_status()` após `requests.get` (`download_and_convert_crowdhuman.py:52`)
- Sem classes de exceção personalizadas; nenhuma exceção relançada; exceções quase nunca capturadas são registradas com contexto além da string da mensagem
- Fatais (retorno antecipado): pesos do modelo ausentes, falha da câmera, falha de subprocesso
- Recuperáveis (imprimir `[Aviso]`/`[AVISO]` e continuar): arquivos opcionais ausentes, problemas de download/extração, imagens ilegíveis (pular linha: `except Exception: continue` em `download_and_convert_crowdhuman.py:119-120`)
- Nunca use exceções para controle de fluxo em laços de dados — use `continue`
## Logging
- Apenas `print()` — sem módulo `logging` em lugar nenhum
- Tags de status entre colchetes como um sistema de pseudo-níveis: `[OK]` sucesso, `[Aviso]`/`[AVISO]` aviso, `[STATUS]` progresso, `[GPU ATIVA]` contexto, `-->` anúncios de etapa, `[Erro: ...]` fatal (`main.py:21,30`)
- Faixas ASCII de caracteres `=` ao redor dos cabeçalhos de estágios principais (`run_pipeline.py:9-11`, `scripts/train_body.py:17-23`, `scripts/validate_body.py:33-39`)
- `flush=True` em todo `print` de `treinar_crowdhuman.py` e do notebook do Colab (mantém a saída ordenada em logs do Colab/CI); outros scripts omitem
- Progresso no console para downloads com linha de porcentagem `end='\r'` (`download_and_convert_crowdhuman.py:66`)
- Combine o vocabulário das tags exatamente ao adicionar mensagens: `[OK]`, `[Aviso]`, `-->`, faixas para estágios
## Comentários
- Os comentários estão em **português (pt-BR)** e marcam etapas numeradas do pipeline: `# 1. Hardware Check`, `# 4. Configurar data.yaml` (`treinar_crowdhuman.py:27,118`)
- Comentários de justificativa para escolhas não óbvias: `# workers=0  # Compatível com Windows`, `# 640px para capturar corpo inteiro...` (`scripts/train_body.py:32,39`)
- Um comentário em inglês acaba escapando (`main.py:57`); prefira português para consistência
- Evite repetir o código; documente *por que* um fallback/peculiaridade existe
- Docstrings de uma linha em português apenas em `scripts/download_and_convert_crowdhuman.py` (`"""Download resiliente com suporte a retomar download e bypass SSL."""` na linha 28). Use esse estilo (uma linha, português, imperativo) para novas funções auxiliares; não é aplicado em outros lugares
- Não usados (sem marcadores TODO/FIXME/HACK na base de código)
## Design de Funções
- A tolerância é alta: `main()` executa 100+ linhas do início ao fim (`treinar_crowdhuman.py:16-143`, `main.py:6-85`). A convenção existente é um `main()` longo por script com estágios de comentário numerados
- Extraia auxiliares apenas para unidades reutilizáveis (download, extração de zip, conversão de anotações) — prefira uma função `snake_case` de nível superior com docstring de uma linha
- 2-4 parâmetros posicionais é o típico (`convert_odgt_to_yolo(odgt_path, images_dir, labels_output_dir)`); sem padrões de options-dict/kwargs
- Caminhos são sempre parâmetros explícitos ou derivados das constantes de módulo `BASE_DIR`
- Scripts de CLI retornam `None` e sinalizam falha via mensagem impressa + `return`
- Auxiliares retornam um status/contador: `bool` para sucesso de download/extração (`download_file`, `extract_zip`), contagem `int` para conversão (`convert_odgt_to_yolo` retorna `converted_count`)
- Retornos antecipados por guarda de condição preferidos a blocos else aninhados
## Design de Módulos
- Sem pacotes, sem `__init__.py`, sem imports entre arquivos do projeto — cada script é autônomo e rederiva os caminhos a partir de `__file__`
- Os scripts se compõem apenas através de `subprocess`: `run_pipeline.py` invoca `scripts/download_and_convert_crowdhuman.py` e depois `scripts/train_body.py` via `subprocess.run([sys.executable, script], check=True)` (`run_pipeline.py:12-20`). Siga isso: reutilização entre scripts = subprocess, não `import`
- Não se aplica
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Visão Geral do Padrão
- Sem estrutura de pacote/módulo: cada arquivo `.py` é um executável autossuficiente com seu próprio `main()` e guard `if __name__ == "__main__"`
- Pipeline linear de 4 estágios: download do dataset → conversão de anotações → treinamento → validação → inferência em tempo real
- Orquestração via `subprocess.run()` (`run_pipeline.py`), não importações — os estágios se comunicam apenas pelo sistema de arquivos
- Todo o estado vive no disco (pastas do dataset, artefatos das execuções do YOLO, arquivos de pesos `.pt`); sem banco de dados, sem estado compartilhado em memória
- Implementações duplicadas/paralelas: um caminho modular (`scripts/`) e um caminho monolítico (`treinar_crowdhuman.py` + `treinar_crowdhuman_colab.ipynb`) fazem o mesmo trabalho
- Caminhos resolvidos em tempo de execução em relação a `__file__` (`os.path.dirname(os.path.abspath(__file__))`), mas `data.yaml` embute um caminho absoluto de outra máquina
## Camadas
- Propósito: comandos voltados ao usuário que iniciam estágios do pipeline ou executam inferência
- Localização: `main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`
- Contém: funções `main()`, resolução de caminhos candidatos do modelo, orquestração via subprocess, loop de webcam do OpenCV
- Depende de: `ultralytics.YOLO`, `cv2`, `subprocess`, layout do sistema de arquivos
- Usado por: operador humano via `python <script>`
- Propósito: um script por estágio do pipeline (download/conversão, treino, validação, configuração do ambiente)
- Localização: `scripts/`
- Contém: `scripts/download_and_convert_crowdhuman.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `scripts/setup_colab_ssh.py`
- Depende de: `ultralytics`, `requests`/`urllib3`, `PIL`, `os`/`json`/`zipfile`
- Usado por: `run_pipeline.py` (spawna via subprocess) ou executado diretamente conforme o `README.md`
- Propósito: declarar o layout do dataset e a ontologia de classes para o Ultralytics
- Localização: `data.yaml` (raiz), hiperparâmetros fixados inline em cada script de treino (não externalizados)
- Depende de: `path:` absoluto apontando para `dataset/`
- Usado por: `scripts/train_body.py`, `scripts/validate_body.py`, `treinar_crowdhuman.py`
- Propósito: localizações no sistema de arquivos em que cada estágio lê entradas e grava saídas
- Localização: `dataset/` (criado em tempo de execução, atualmente ausente), `runs/detect/`, `resultados/`, `models/`
- Contém: execuções de treino do YOLO (`runs/detect/train_crowdhuman_body/`), pesos copiados (`resultados/best.pt`), pesos base (`models/base_face_weights.pt`, `yolo26n.pt`)
- Depende de: nada (dados puros)
- Usado por: todas as outras camadas
- Propósito: variante em nuvem (Colab) do pipeline de treino para execução em GPU
- Localização: `treinar_crowdhuman_colab.ipynb`, auxiliado por `scripts/setup_colab_ssh.py` (configuração de túnel SSH via cloudflared)
- Depende de: `huggingface_hub.snapshot_download`, `torch`, `ultralytics`
- Usado por: execução manual do notebook; espelha a lógica de `treinar_crowdhuman.py` célula por célula
## Fluxo de Dados
- Puramente baseado no sistema de arquivos; cada script é sem estado entre execuções
- A idempotência é ad hoc: o estágio de download pula arquivos cujo tamanho local corresponde ao `content-length`; `exist_ok=True` sobrescreve o mesmo diretório de execução
- `dataset/` e `runs/.../weights/` estão atualmente ausentes neste checkout — os scripts os recriam na primeira execução
## Abstrações-Chave
- Propósito: encontrar um peso `.pt` utilizável sem falha dura
- Exemplos: `main.py:11-19` (lista de prioridade de 5 caminhos), `scripts/train_body.py:8-12`, `scripts/validate_body.py:8-13`
- Padrão: vence o primeiro que corresponder `next((p for p in candidatos if os.path.exists(p)), None)` com aviso no console e fallback para o base `yolo26n.pt`
- Propósito: transformar as anotações JSON-lines do CrowdHuman em rótulos `.txt` normalizados do YOLO
- Exemplos: `convert_odgt_to_yolo()` em `scripts/download_and_convert_crowdhuman.py:95-150`; duplicado inline como `convert_odgt()` em `treinar_crowdhuman.py:86-109`
- Padrão: função independente sobre arquivos comuns; duas cópias divergentes (sem módulo compartilhado)
- Propósito: configurar e iniciar o treino do Ultralytics
- Exemplos: `scripts/train_body.py:29-43`, `treinar_crowdhuman.py:128-142`
- Padrão: chamada direta a `ultralytics.YOLO.train()` com hiperparâmetros inline (sem arquivo de configuração, sem argumentos de CLI)
- Propósito: encadear estágios como subprocessos
- Exemplos: `run_pipeline.py:12-20`
- Padrão: `subprocess.run([sys.executable, script], check=True)` — a falha do estágio 1 aborta o estágio 2 via `CalledProcessError`
- Propósito: promover uma execução treinada para um caminho estável
- Exemplos: `resultados/best.pt` (cópia manual do `best.pt` de uma execução), `models/base_face_weights.pt` (cópia isolada dos pesos do rosto para que o treino nunca altere o original)
- Padrão: duplicação simples de arquivos; sem metadados de versionamento
## Pontos de Entrada
- Localização: `main.py`
- Gatilhos: `python main.py`
- Responsabilidades: resolver pesos, abrir a webcam `cv2.VideoCapture(0)`, executar inferência YOLO com teto de 5 FPS, desenhar caixas/HUD, sair ao pressionar `q`
- Localização: `run_pipeline.py`
- Gatilhos: `python run_pipeline.py`
- Responsabilidades: executar o estágio do dataset e depois o estágio de treino como subprocessos (a validação *não* está incluída)
- Localização: `scripts/download_and_convert_crowdhuman.py`, `scripts/train_body.py`, `scripts/validate_body.py`
- Gatilhos: `python scripts/<name>.py` (documentado nos passos 1-3 do `README.md`)
- Responsabilidades: um estágio por script; recalcula `base_dir = dirname(dirname(abspath(__file__)))` para localizar a raiz do projeto
- Localização: `treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`
- Gatilhos: `python treinar_crowdhuman.py` ou execução de células do notebook
- Responsabilidades: tudo em um único arquivo — verificação de GPU, inicialização de pesos, download, conversão, regeneração do `data.yaml`, treino
- Localização: `scripts/setup_colab_ssh.py`
- Gatilhos: `python scripts/setup_colab_ssh.py`
- Responsabilidades: baixar `cloudflared.exe` para `~/.ssh`, acrescentar um bloco `ProxyCommand` ao `~/.ssh/config` para `*.trycloudflare.com`
## Tratamento de Erros
- Verificações de existência antes de agir: `main.py:19-22` imprime `"Erro: Nenhum modelo encontrado."` e retorna
- `run_pipeline.py` usa `check=True` para que um estágio com falha levante `subprocess.CalledProcessError` (traceback não capturado)
- `try/except` amplo que engole erros durante o download do dataset: `treinar_crowdhuman.py:115-116` imprime `[Aviso download]` e segue para o treino mesmo assim
- Pulos por registro na conversão: imagens ausentes ou arquivos PIL ilegíveis são silenciosamente ignorados com `continue` (`scripts/download_and_convert_crowdhuman.py:114,120`)
- Verificação SSL deliberadamente desativada: `urllib3.disable_warnings()` + `verify=False` (`scripts/download_and_convert_crowdhuman.py:10,51`)
## Preocupações Transversais
- `print()` simples para o stdout, mensagens em português, tags de status entre colchetes (`[OK]`, `[Aviso]`, `-->`, `[STATUS]`); o progresso do treino é delegado à própria saída de console do Ultralytics (`verbose=True` em `main.py:48`)
- Sem camada de validação de entrada; a correção é garantida implicitamente pelo Ultralytics (ele lê o `data.yaml` e os arquivos de rótulo). O limitamento numérico das anotações para `[0,1]` ocorre inline no conversor (`scripts/download_and_convert_crowdhuman.py:136-139`)
- Dividida entre externa (`data.yaml`) e fixa inline (epochs/batch/pesos de loss em cada script de treino — os valores diferem entre `scripts/train_body.py` e `treinar_crowdhuman.py`)
- `data.yaml` contém um `path:` absoluto específico da máquina (`C:\Users\fern\...`), portanto precisa ser reescrito (como faz `treinar_crowdhuman.py:119-122`) ou editado em qualquer máquina nova
- Contrato implícito sobre os nomes de diretórios: o treino sempre grava em `runs/detect/train_crowdhuman_body`, e os consumidores a jusante (`main.py`, `scripts/validate_body.py`) fixam esse mesmo nome
- Ultralytics `seed: 0`, `deterministic: true` registrados em `runs/detect/train_crowdhuman_body/args.yaml`; nenhum lockfile ou arquivo de requirements fixa o ambiente Python
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
