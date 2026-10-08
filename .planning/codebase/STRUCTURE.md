# Estrutura do Codebase

**Data da Análise:** 2026-10-08

## Layout de Diretórios

```
scriptvisaocomput/
├── main.py                     # ★ ARQUIVO PRINCIPAL — inferência em tempo real na webcam
├── run_pipeline.py             # [teste] Orquestrador de pipeline de 2 estágios (subprocess)
├── treinar_crowdhuman.py       # [teste] Script de treino monolítico ponta a ponta
├── treinar_crowdhuman_colab.ipynb  # [teste] Variante em Colab do treinador
├── data.yaml                   # Config do dataset Ultralytics (class: person)
├── README.md                   # Guia passo a passo em português
├── yolo26n.pt                  # Pesos base YOLOv26-nano (5.3 MB)
├── scripts/                    # [teste] Scripts de estágios do pipeline
│   ├── download_and_convert_crowdhuman.py  # Estágio 1: download do dataset + ODGT→YOLO
│   ├── train_body.py          # Estágio 2: treino com transfer learning
│   ├── validate_body.py       # Estágio 3: métricas formais do split de val
│   └── setup_colab_ssh.py     # Utilitário: config SSH com cloudflared para o Colab
├── models/                     # Pesos base/iniciais isolados
│   └── base_face_weights.pt   # Cópia dos pesos do modelo de rosto para transfer learning
├── resultados/                 # Pesos treinados promovidos (cópias manuais)
│   ├── best.pt
│   └── best (1).pt
├── runs/                       # Saída das execuções do Ultralytics (gerada)
│   └── detect/train_crowdhuman_body/
│       ├── args.yaml          # Registro completo de hiperparâmetros da última execução
│       ├── train_batch*.jpg, labels.jpg  # Gráficos de pré-visualização do treino
│       └── weights/           # (vazio neste checkout — best.pt está em outro lugar)
├── test/                       # Mídia de exemplo, NÃO testes unitários
│   └── gemini_generated_video_8d21d35f.mp4
├── .planning/codebase/         # Documentos de análise de codebase do GSD (este arquivo)
└── .git/                       # Repo inicializado, sem commits ainda
```

Ausente, mas criado em tempo de execução: `dataset/` (com `images/{train,val}`, `labels/{train,val}`, `downloads_cache/`) — referenciado por `data.yaml` e `scripts/download_and_convert_crowdhuman.py:13-14`.

## Papéis dos Arquivos (definido pelo usuário)

- **`main.py` — ARQUIVO PRINCIPAL.** É o programa real do projeto (inferência na webcam). Todo o desenvolvimento deve convergir para ele.
- **Demais arquivos são apenas para teste/experimentação:** `run_pipeline.py`, `treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb` e todo o diretório `scripts/`. Servem para testar download/treino/validação, não são o produto.

## Propósitos dos Diretórios

**scripts/:**
- Propósito: um script por estágio do pipeline de ML, cada um executável independentemente
- Contém: scripts de estágio `*.py` (nomes em snake_case, com o verbo primeiro)
- Arquivos-chave: `download_and_convert_crowdhuman.py` (download do HuggingFace + conversão ODGT→YOLO), `train_body.py` (treino Ultralytics), `validate_body.py` (métricas), `setup_colab_ssh.py` (configuração de túnel SSH do ambiente de desenvolvimento para o Colab)
- Subdiretórios: nenhum (plano)

**models/:**
- Propósito: pesos base/iniciais isolados usados para iniciar o transfer learning
- Contém: checkpoints `*.pt` do PyTorch
- Arquivos-chave: `base_face_weights.pt` — uma *cópia* dos pesos de detecção de rosto para que o treino nunca altere o original (conforme o comentário em `scripts/train_body.py:7-8`)
- Observação: os scripts também usam fallback para um caminho em diretório irmão `../models/yolo26n.pt` (`scripts/train_body.py:11`, `main.py:15`), que não existe aqui

**resultados/:**
- Propósito: local estável, curado manualmente, para os pesos treinados promovidos ("resultados", do inglês "results")
- Contém: `best.pt`, `best (1).pt` (artefatos duplicados de download/cópia)
- Consumido por: `main.py:12` (primeiro candidato na lista de resolução de pesos)

**runs/:**
- Propósito: saída de treino/validação do Ultralytics YOLO (gerada pelo framework)
- Contém: `detect/train_crowdhuman_body/` com `args.yaml` (registro de hiperparâmetros de 116 linhas), JPGs de pré-visualização, subdiretório `weights/`
- Arquivos-chave: `runs/detect/train_crowdhuman_body/args.yaml` — registro oficial da última execução de treino, incluindo caminhos absolutos da máquina original
- Subdiretórios: `runs/detect/val_results/` é criado por `scripts/validate_body.py:18` mas ainda não está presente

**test/:**
- Propósito: guarda um único vídeo de exemplo gerado (`gemini_generated_video_8d21d35f.mp4`, ~6 MB)
- Contém: apenas mídia — sem framework de testes, sem arquivos `*.test.py`/`*.spec.*` em lugar nenhum do repo
- Não é um diretório de testes no sentido convencional

**Raiz (raiz do projeto):**
- Propósito: scripts de entrada e configuração/documentação de nível superior
- Contém: `main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`, `data.yaml`, `README.md`, `yolo26n.pt`

## Locais dos Arquivos-Chave

**Pontos de Entrada:**
- `main.py` **(principal)**: detecção de corpo em tempo real na webcam (`python main.py`, pressione `q` para sair)
- `run_pipeline.py` *(teste)*: orquestra a preparação do dataset e depois o treino via `subprocess.run(..., check=True)`
- `treinar_crowdhuman.py` *(teste)*: treino local autossuficiente (download + conversão + treino em um único arquivo)
- `treinar_crowdhuman_colab.ipynb` *(teste)*: o mesmo fluxo como notebook Colab para execução em GPU

**Configuração:**
- `data.yaml`: especificação de dataset do Ultralytics (`path`, `train`, `val`, `nc: 1`, `names: ['person']`) — `path` é um caminho absoluto fixo de outra máquina e deve ser atualizado em cada host
- `runs/detect/train_crowdhuman_body/args.yaml`: registro gerado de todos os hiperparâmetros de treino
- Demais hiperparâmetros estão fixados inline: `scripts/train_body.py:29-43` (epochs=300, imgsz=640, batch=8, box=8.5, cls=0.8, dfl=2.0) vs `treinar_crowdhuman.py:128-142` (box=10.0, cls=0.7, batch adaptativo 8/32)
- Não existem `requirements.txt`, `pyproject.toml`, `.gitignore` nem configuração de lint/formatação

**Lógica Central:**
- `scripts/download_and_convert_crowdhuman.py`: aquisição do dataset e conversão de rótulos (`download_file`, `extract_zip`, `flatten_directory`, `convert_odgt_to_yolo`)
- `scripts/train_body.py`: estágio de treino com resolução de fallback de pesos
- `scripts/validate_body.py`: estágio de validação que imprime mAP@0.5, mAP@0.5:0.95, P, R, F1
- `main.py:11-19`: resolução de caminhos candidatos de pesos (5 fallbacks ordenados)
- `treinar_crowdhuman.py`: conversor duplicado + regeneração do `data.yaml` + dimensionamento de batch conforme a GPU

**Testes:**
- Não existem arquivos de teste. `test/` contém apenas um MP4 de exemplo. A lacuna de testes está documentada na análise de qualidade/preocupações.

**Documentação:**
- `README.md`: guia em português com o fluxo de uso em 4 passos (download → treino → validação → webcam)

## Convenções de Nomenclatura

**Arquivos:**
- `snake_case.py` para todos os arquivos Python, com o verbo primeiro nas ações: `train_body.py`, `validate_body.py`, `run_pipeline.py`, `download_and_convert_crowdhuman.py`
- Idiomas mistos: termos técnicos em inglês em `scripts/`, português nos nomes de nível raiz (`treinar_crowdhuman.py`, `resultados/`)
- Notebooks: `{task}_{context}_{platform}.ipynb` — `treinar_crowdhuman_colab.ipynb`
- MAIÚSCULAS para documentos: `README.md`
- Cópias de artefatos podem conter espaços/parênteses: `resultados/best (1).pt` (evite esse padrão em arquivos novos)

**Diretórios:**
- Minúsculas, singular/plural, sem separadores: `scripts/`, `models/`, `runs/`, `test/`, `resultados/`
- Hierarquia gerada pelo framework preservada: `runs/detect/{task}_{name}/` pela convenção do Ultralytics

**Código:**
- Todo script: guard `def main():` + `if __name__ == "__main__": main()`
- Idiomática de resolução de caminhos: `base_dir = os.path.dirname(os.path.abspath(__file__))` na raiz, `os.path.dirname(os.path.dirname(...))` dentro de `scripts/`
- Tags de status no console: `[OK]`, `[Aviso]`, `-->`, separadores de banner `====`; mensagens em português

## Onde Adicionar Código Novo

**Novo Estágio do Pipeline:**
- Implementação: `scripts/{verb}_{noun}.py` com um guard `main()`
- Invocação: conectá-lo ao `run_pipeline.py` como uma etapa adicional `subprocess.run([sys.executable, ...], check=True)`
- Documentação: acrescentar um passo numerado ao `README.md`

**Novo Script de Ponto de Entrada (voltado ao usuário):**
- Código principal: raiz do projeto (ex.: ao lado de `main.py`), seguindo o padrão de fallback de caminhos candidatos para localizar pesos

**Lógica Auxiliar Compartilhada:**
- Hoje não existe módulo compartilhado. Prefira extrair um módulo comum (ex.: `scripts/common.py` ou `utils/`) em vez de adicionar uma terceira cópia — o conversor ODGT já está duplicado em `scripts/download_and_convert_crowdhuman.py:95` e `treinar_crowdhuman.py:86`
- Scripts utilitários/de ambiente: `scripts/` (ver `setup_colab_ssh.py`)

**Nova Configuração:**
- Config de dataset/classes: `data.yaml` (arquivo único, raiz)
- Hiperparâmetros: atualmente inline no script de treino; se externalizar, adicionar um YAML ao lado do `data.yaml` e referenciá-lo a partir de `scripts/train_body.py`

**Pesos Treinados:**
- Manter a saída do framework em `runs/detect/{run_name}/weights/best.pt`; promover uma cópia estável para `resultados/` ou `models/` quando for consumida por `main.py`

**Artefatos Gerados/De Modelo (não editar manualmente):**
- `runs/**`, `dataset/**`, checkpoints `*.pt`, `yolo26n.pt`

## Diretórios Especiais

**runs/**
- Propósito: artefatos de treino/validação gerados pelo Ultralytics
- Fonte: gravado por `scripts/train_body.py` (`project=runs/detect`, `name=train_crowdhuman_body`, `exist_ok=True` — reexecuções sobrescrevem)
- Commitado: Sim (atualmente aparece no git status como não rastreado, mas presente; contém JPGs de pré-visualização grandes)

**resultados/**
- Propósito: pesos treinados promovidos manualmente
- Fonte: cópia manual do `best.pt` de uma execução
- Commitado: Sim (não rastreado; ~5 MB por arquivo `.pt`)

**dataset/** (ausente)
- Propósito: imagens do CrowdHuman + rótulos YOLO + `downloads_cache/`
- Fonte: criado por `scripts/download_and_convert_crowdhuman.py` ou `treinar_crowdhuman.py`
- Commitado: não presente neste checkout; referenciado por `data.yaml`

**.planning/**
- Propósito: documentos de planejamento/análise de codebase do GSD
- Fonte: gerado por `/gsd-map-codebase` e comandos relacionados
- Commitado: Sim

**.git/**
- Propósito: controle de versão (repo inicializado em `master`, zero commits, sem `.gitignore`)
- Fonte: `git init`
- Commitado: tudo está atualmente não rastreado; binários grandes (`*.pt`, MP4, JPG) serão commitados a menos que sejam ignorados

---

*Análise de estrutura: 2026-10-08*
*Atualize quando a estrutura de diretórios mudar*
