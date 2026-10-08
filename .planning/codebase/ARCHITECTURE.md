# Arquitetura

**Data da Análise:** 2026-10-08

## Visão Geral do Padrão

**Geral:** Pipeline de ML baseado em scripts (coleção plana de scripts Python autônomos, orquestrada via subprocess)

**Características Principais:**
- Sem estrutura de pacote/módulo: cada arquivo `.py` é um executável autossuficiente com seu próprio `main()` e guard `if __name__ == "__main__"`
- Pipeline linear de 4 estágios: download do dataset → conversão de anotações → treinamento → validação → inferência em tempo real
- Orquestração via `subprocess.run()` (`run_pipeline.py`), não importações — os estágios se comunicam apenas pelo sistema de arquivos
- Todo o estado vive no disco (pastas do dataset, artefatos das execuções do YOLO, arquivos de pesos `.pt`); sem banco de dados, sem estado compartilhado em memória
- Implementações duplicadas/paralelas: um caminho modular (`scripts/`) e um caminho monolítico (`treinar_crowdhuman.py` + `treinar_crowdhuman_colab.ipynb`) fazem o mesmo trabalho
- Caminhos resolvidos em tempo de execução em relação a `__file__` (`os.path.dirname(os.path.abspath(__file__))`), mas `data.yaml` embute um caminho absoluto de outra máquina

## Camadas

**Camada de Entrada/Orquestração:**
- Propósito: comandos voltados ao usuário que iniciam estágios do pipeline ou executam inferência
- Localização: `main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`
- Contém: funções `main()`, resolução de caminhos candidatos do modelo, orquestração via subprocess, loop de webcam do OpenCV
- Depende de: `ultralytics.YOLO`, `cv2`, `subprocess`, layout do sistema de arquivos
- Usado por: operador humano via `python <script>`

**Camada de Estágios do Pipeline:**
- Propósito: um script por estágio do pipeline (download/conversão, treino, validação, configuração do ambiente)
- Localização: `scripts/`
- Contém: `scripts/download_and_convert_crowdhuman.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `scripts/setup_colab_ssh.py`
- Depende de: `ultralytics`, `requests`/`urllib3`, `PIL`, `os`/`json`/`zipfile`
- Usado por: `run_pipeline.py` (spawna via subprocess) ou executado diretamente conforme o `README.md`

**Camada de Configuração:**
- Propósito: declarar o layout do dataset e a ontologia de classes para o Ultralytics
- Localização: `data.yaml` (raiz), hiperparâmetros fixados inline em cada script de treino (não externalizados)
- Depende de: `path:` absoluto apontando para `dataset/`
- Usado por: `scripts/train_body.py`, `scripts/validate_body.py`, `treinar_crowdhuman.py`

**Camada de Artefatos/Estado:**
- Propósito: localizações no sistema de arquivos em que cada estágio lê entradas e grava saídas
- Localização: `dataset/` (criado em tempo de execução, atualmente ausente), `runs/detect/`, `resultados/`, `models/`
- Contém: execuções de treino do YOLO (`runs/detect/train_crowdhuman_body/`), pesos copiados (`resultados/best.pt`), pesos base (`models/base_face_weights.pt`, `yolo26n.pt`)
- Depende de: nada (dados puros)
- Usado por: todas as outras camadas

**Camada de Notebook/Remota:**
- Propósito: variante em nuvem (Colab) do pipeline de treino para execução em GPU
- Localização: `treinar_crowdhuman_colab.ipynb`, auxiliado por `scripts/setup_colab_ssh.py` (configuração de túnel SSH via cloudflared)
- Depende de: `huggingface_hub.snapshot_download`, `torch`, `ultralytics`
- Usado por: execução manual do notebook; espelha a lógica de `treinar_crowdhuman.py` célula por célula

## Fluxo de Dados

**Pipeline de Treino (`run_pipeline.py` → `scripts/`):**

1. `run_pipeline.py:12-13` spawna `scripts/download_and_convert_crowdhuman.py`
2. O estágio de download busca 6 arquivos do HuggingFace (`annotation_*.odgt`, `CrowdHuman_*.zip`) para `dataset/downloads_cache/` (`scripts/download_and_convert_crowdhuman.py:16-25`)
3. Os zips são extraídos em `dataset/images/{train,val}/`; as pastas aninhadas `Images/` são achatadas (`flatten_directory`, linha 82)
4. `convert_odgt_to_yolo()` (linha 95) lê as JSON-lines do ODGT, mantém as caixas de corpo inteiro com `tag == 'person'` (`fbox`), grava rótulos YOLO normalizados `0 x_center y_center w h` em `dataset/labels/{train,val}/`
5. `run_pipeline.py:19-20` spawna `scripts/train_body.py` → carrega `models/base_face_weights.pt` (transfer learning) → `model.train(data=data.yaml, epochs=300, imgsz=640, batch=8, ...)` → grava `runs/detect/train_crowdhuman_body/` incluindo `weights/best.pt`
6. Validação (etapa manual): `scripts/validate_body.py` carrega `runs/detect/train_crowdhuman_body/weights/best.pt`, executa `model.val(split='val')`, imprime mAP/P/R/F1 no stdout
7. Inferência: `main.py` testa uma lista ordenada de caminhos candidatos de pesos (linhas 11-17), usa o primeiro que existe, executa detecção na webcam a 5 FPS com `conf=0.25, iou=0.60`

**Fluxo Monolítico Alternativo (`treinar_crowdhuman.py`):**

1. Verificação de GPU via `torch.cuda` (linha 28)
2. Pesos iniciais: `models/base_face_weights.pt`, com fallback para `../runs/detect/train-14/weights/best.pt` (copiado para dentro) ou `'yolo26n.pt'` (linhas 37-45)
3. `snapshot_download(repo_id='sshao0516/CrowdHuman')` e depois lógica inline (duplicada) de extração/achatamento/conversão (linhas 63-116)
4. **Reescreve `data.yaml`** com o caminho absoluto local do dataset (linhas 119-122)
5. Tamanho do batch definido automaticamente entre 8 e 32 conforme a VRAM (linha 125); treina em `runs/detect/train_crowdhuman_body`

**Gerenciamento de Estado:**
- Puramente baseado no sistema de arquivos; cada script é sem estado entre execuções
- A idempotência é ad hoc: o estágio de download pula arquivos cujo tamanho local corresponde ao `content-length`; `exist_ok=True` sobrescreve o mesmo diretório de execução
- `dataset/` e `runs/.../weights/` estão atualmente ausentes neste checkout — os scripts os recriam na primeira execução

## Abstrações-Chave

**Resolução de Candidatos do Modelo:**
- Propósito: encontrar um peso `.pt` utilizável sem falha dura
- Exemplos: `main.py:11-19` (lista de prioridade de 5 caminhos), `scripts/train_body.py:8-12`, `scripts/validate_body.py:8-13`
- Padrão: vence o primeiro que corresponder `next((p for p in candidatos if os.path.exists(p)), None)` com aviso no console e fallback para o base `yolo26n.pt`

**Conversor ODGT → YOLO:**
- Propósito: transformar as anotações JSON-lines do CrowdHuman em rótulos `.txt` normalizados do YOLO
- Exemplos: `convert_odgt_to_yolo()` em `scripts/download_and_convert_crowdhuman.py:95-150`; duplicado inline como `convert_odgt()` em `treinar_crowdhuman.py:86-109`
- Padrão: função independente sobre arquivos comuns; duas cópias divergentes (sem módulo compartilhado)

**Harness de Treino YOLO:**
- Propósito: configurar e iniciar o treino do Ultralytics
- Exemplos: `scripts/train_body.py:29-43`, `treinar_crowdhuman.py:128-142`
- Padrão: chamada direta a `ultralytics.YOLO.train()` com hiperparâmetros inline (sem arquivo de configuração, sem argumentos de CLI)

**Orquestrador do Pipeline:**
- Propósito: encadear estágios como subprocessos
- Exemplos: `run_pipeline.py:12-20`
- Padrão: `subprocess.run([sys.executable, script], check=True)` — a falha do estágio 1 aborta o estágio 2 via `CalledProcessError`

**Promoção de Artefatos de Pesos:**
- Propósito: promover uma execução treinada para um caminho estável
- Exemplos: `resultados/best.pt` (cópia manual do `best.pt` de uma execução), `models/base_face_weights.pt` (cópia isolada dos pesos do rosto para que o treino nunca altere o original)
- Padrão: duplicação simples de arquivos; sem metadados de versionamento

## Pontos de Entrada

**Inferência em tempo real:**
- Localização: `main.py`
- Gatilhos: `python main.py`
- Responsabilidades: resolver pesos, abrir a webcam `cv2.VideoCapture(0)`, executar inferência YOLO com teto de 5 FPS, desenhar caixas/HUD, sair ao pressionar `q`

**Pipeline completo:**
- Localização: `run_pipeline.py`
- Gatilhos: `python run_pipeline.py`
- Responsabilidades: executar o estágio do dataset e depois o estágio de treino como subprocessos (a validação *não* está incluída)

**Estágios individuais:**
- Localização: `scripts/download_and_convert_crowdhuman.py`, `scripts/train_body.py`, `scripts/validate_body.py`
- Gatilhos: `python scripts/<name>.py` (documentado nos passos 1-3 do `README.md`)
- Responsabilidades: um estágio por script; recalcula `base_dir = dirname(dirname(abspath(__file__)))` para localizar a raiz do projeto

**Treinador monolítico/local+Colab:**
- Localização: `treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`
- Gatilhos: `python treinar_crowdhuman.py` ou execução de células do notebook
- Responsabilidades: tudo em um único arquivo — verificação de GPU, inicialização de pesos, download, conversão, regeneração do `data.yaml`, treino

**Configuração do ambiente:**
- Localização: `scripts/setup_colab_ssh.py`
- Gatilhos: `python scripts/setup_colab_ssh.py`
- Responsabilidades: baixar `cloudflared.exe` para `~/.ssh`, acrescentar um bloco `ProxyCommand` ao `~/.ssh/config` para `*.trycloudflare.com`

## Tratamento de Erros

**Estratégia:** fail-fast com mensagens no console; nenhuma exceção é levantada para um manipulador de nível superior, sem framework de logging, sem códigos de saída diferentes de zero (os scripts fazem `print` e `return` na falha).

**Padrões:**
- Verificações de existência antes de agir: `main.py:19-22` imprime `"Erro: Nenhum modelo encontrado."` e retorna
- `run_pipeline.py` usa `check=True` para que um estágio com falha levante `subprocess.CalledProcessError` (traceback não capturado)
- `try/except` amplo que engole erros durante o download do dataset: `treinar_crowdhuman.py:115-116` imprime `[Aviso download]` e segue para o treino mesmo assim
- Pulos por registro na conversão: imagens ausentes ou arquivos PIL ilegíveis são silenciosamente ignorados com `continue` (`scripts/download_and_convert_crowdhuman.py:114,120`)
- Verificação SSL deliberadamente desativada: `urllib3.disable_warnings()` + `verify=False` (`scripts/download_and_convert_crowdhuman.py:10,51`)

## Preocupações Transversais

**Logging:**
- `print()` simples para o stdout, mensagens em português, tags de status entre colchetes (`[OK]`, `[Aviso]`, `-->`, `[STATUS]`); o progresso do treino é delegado à própria saída de console do Ultralytics (`verbose=True` em `main.py:48`)

**Validação:**
- Sem camada de validação de entrada; a correção é garantida implicitamente pelo Ultralytics (ele lê o `data.yaml` e os arquivos de rótulo). O limitamento numérico das anotações para `[0,1]` ocorre inline no conversor (`scripts/download_and_convert_crowdhuman.py:136-139`)

**Configuração:**
- Dividida entre externa (`data.yaml`) e fixa inline (epochs/batch/pesos de loss em cada script de treino — os valores diferem entre `scripts/train_body.py` e `treinar_crowdhuman.py`)
- `data.yaml` contém um `path:` absoluto específico da máquina (`C:\Users\fern\...`), portanto precisa ser reescrito (como faz `treinar_crowdhuman.py:119-122`) ou editado em qualquer máquina nova

**Descoberta de Artefatos:**
- Contrato implícito sobre os nomes de diretórios: o treino sempre grava em `runs/detect/train_crowdhuman_body`, e os consumidores a jusante (`main.py`, `scripts/validate_body.py`) fixam esse mesmo nome

**Reprodutibilidade:**
- Ultralytics `seed: 0`, `deterministic: true` registrados em `runs/detect/train_crowdhuman_body/args.yaml`; nenhum lockfile ou arquivo de requirements fixa o ambiente Python

---

*Análise de arquitetura: 2026-10-08*
*Atualize quando os padrões principais mudarem*
