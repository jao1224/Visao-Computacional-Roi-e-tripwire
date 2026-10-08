# Convenções de Código

**Data da Análise:** 2026-10-08

## Padrões de Nomenclatura

**Arquivos:**
- `snake_case.py` para todos os arquivos Python, mas os nomes são **de idioma misto**: inglês para scripts de pipeline (`run_pipeline.py`, `scripts/train_body.py`, `scripts/validate_body.py`, `scripts/download_and_convert_crowdhuman.py`) e português para scripts de nível raiz/treinamento (`treinar_crowdhuman.py`, `treinar_crowdhuman_colab.ipynb`)
- Regra geral: mantenha os nomes de arquivos existentes como estão; nomeie **novos** arquivos em inglês `snake_case` ao adicionar em `scripts/`
- Configuração: `data.yaml` (raiz) para a configuração de dataset do Ultralytics
- Não existem arquivos de teste em lugar nenhum (veja `TESTING.md`)

**Funções:**
- `snake_case` em todo lugar: `main()`, `download_file()`, `extract_zip()`, `flatten_directory()`, `convert_odgt_to_yolo()`
- Todo script executável expõe uma única entrada `main()` protegida por `if __name__ == "__main__":` (veja `main.py:87`, `run_pipeline.py:22`, `scripts/train_body.py:45`, `scripts/validate_body.py:41`, `treinar_crowdhuman.py:145`)
- Auxiliares pequenos definidos **aninhados dentro de `main()`** quando usados apenas lá (`extract_zip`, `convert_odgt` em `treinar_crowdhuman.py:70,86`) ou no escopo do módulo quando compartilhados (`download_and_convert_crowdhuman.py:27-150`)
- `scripts/setup_colab_ssh.py` é o único script **sem** `main()` — é código puramente procedural de nível superior

**Variáveis:**
- `camelCase` para variáveis locais/de caminho: estilo `weightsPath` nunca usado; o estilo real é `weights_path`, `train_img_dir`, `val_lbl_dir`, `modelo_path`, `downloaded`
- `UPPER_SNAKE_CASE` apenas para constantes de módulo: `BASE_DIR`, `DATASET_DIR`, `CACHE_DIR`, `HF_BASE_URL`, `FILES_TO_DOWNLOAD` (`scripts/download_and_convert_crowdhuman.py:12-25`)
- Desvio: `treinar_crowdhuman.py:20-23` usa `UPPER_SNAKE_CASE` para variáveis **locais** dentro de `main()`; `main.py:7` e `scripts/train_body.py:5` usam `base_dir` minúsculo para o mesmo valor. Prefira `base_dir`/`root_dir` minúsculos para locais em código novo; mantenha `UPPER_SNAKE_CASE` para constantes verdadeiras de módulo.
- Identificadores em português aparecem para variáveis de domínio: `candidatos`, `modelo_path`, `num_pessoas`, `webcam` (`main.py:11-28`). Adapte-se ao idioma do arquivo ao redor.

**Tipos:**
- Não se aplica — a base de código é Python sem tipagem (sem anotações de tipo em lugar nenhum)

## Estilo de Código

**Formatação:**
- Nenhum formatador configurado (sem `black`, `ruff format`, equivalente a `.prettierrc`). Combine o estilo manual: indentação de 4 espaços, linhas de ~100-120 caracteres
- As aspas são **inconsistentes**: aspas simples predominam para caminhos/strings curtas (`'resultados'`, `'best.pt'`), aspas duplas nas f-strings de `download_and_convert_crowdhuman.py` e no notebook. Prefira aspas simples para código novo, a menos que a linha contenha apóstrofos/aspas simples internas
- Vírgulas finais não são usadas; linha em branco separa etapas numeradas

**Linting:**
- Nenhum configurado (sem `.flake8`, `.pylintrc`, `ruff`/`black`/`mypy` em qualquer arquivo de configuração; sem `requirements.txt`, `pyproject.toml` ou `setup.cfg`)
- Se for introduzir um linter, adicione `ruff` com um `pyproject.toml` na raiz do repositório em vez de empilhar várias ferramentas

## Organização de Imports

**Ordem:**
1. Biblioteca padrão (`os`, `sys`, `json`, `time`, `zipfile`, `shutil`, `subprocess`, `urllib`)
2. Terceiros (`cv2`, `requests`, `urllib3`, `torch`, `PIL.Image`, `huggingface_hub`, `ultralytics`)
3. Locais (nenhum — o projeto **não tem imports de módulos locais**; os scripts nunca importam uns aos outros)

**Agrupamento:**
- Um bloco só, stdlib primeiro e depois terceiros, sem linhas em branco entre grupos (`treinar_crowdhuman.py:1-11`)
- Imports inline ocorrem no meio da função quando necessários de forma preguiçosa: `import shutil` em `treinar_crowdhuman.py:41`; células do notebook importam por célula (`treinar_crowdhuman_colab.ipynb` células 1, 3, 4). Aceitável em notebooks; coloque os imports no topo em arquivos `.py`.

**Aliases de Caminho:**
- Nenhum. Todos os caminhos resolvidos com `os.path.join` relativo a `os.path.dirname(os.path.abspath(__file__))`

## Tratamento de Erros

**Padrões:**
- Falha suave / continuar apesar do erro: `try/except Exception` amplo que imprime um aviso e prossegue (`treinar_crowdhuman.py:115-116`, `download_and_convert_crowdhuman.py:35-39,116-120`, célula 4 do notebook)
- Retornos antecipados por guarda de condição para condições fatais com mensagem impressa e `return` — nunca exceções levantadas (`main.py:19-22` modelo ausente, `main.py:29-31` falha ao abrir a webcam)
- Cadeias de fallback em vez de exceções: lista de caminhos candidatos resolvida com `next((p for p in candidatos if os.path.exists(p)), None)` (`main.py:11-19`) ou `if not os.path.exists(...)` com fallback para os pesos base e impressão com `[Aviso]` (`scripts/train_body.py:9-12`, `scripts/validate_body.py:9-13`)
- Etapas de subprocesso usam `check=True` para que falhas abortem o pipeline (`run_pipeline.py:13,20`)
- HTTP: `response.raise_for_status()` após `requests.get` (`download_and_convert_crowdhuman.py:52`)
- Sem classes de exceção personalizadas; nenhuma exceção relançada; exceções quase nunca capturadas são registradas com contexto além da string da mensagem

**Tipos de Erro:**
- Fatais (retorno antecipado): pesos do modelo ausentes, falha da câmera, falha de subprocesso
- Recuperáveis (imprimir `[Aviso]`/`[AVISO]` e continuar): arquivos opcionais ausentes, problemas de download/extração, imagens ilegíveis (pular linha: `except Exception: continue` em `download_and_convert_crowdhuman.py:119-120`)
- Nunca use exceções para controle de fluxo em laços de dados — use `continue`

## Logging

**Framework:**
- Apenas `print()` — sem módulo `logging` em lugar nenhum

**Padrões:**
- Tags de status entre colchetes como um sistema de pseudo-níveis: `[OK]` sucesso, `[Aviso]`/`[AVISO]` aviso, `[STATUS]` progresso, `[GPU ATIVA]` contexto, `-->` anúncios de etapa, `[Erro: ...]` fatal (`main.py:21,30`)
- Faixas ASCII de caracteres `=` ao redor dos cabeçalhos de estágios principais (`run_pipeline.py:9-11`, `scripts/train_body.py:17-23`, `scripts/validate_body.py:33-39`)
- `flush=True` em todo `print` de `treinar_crowdhuman.py` e do notebook do Colab (mantém a saída ordenada em logs do Colab/CI); outros scripts omitem
- Progresso no console para downloads com linha de porcentagem `end='\r'` (`download_and_convert_crowdhuman.py:66`)
- Combine o vocabulário das tags exatamente ao adicionar mensagens: `[OK]`, `[Aviso]`, `-->`, faixas para estágios

## Comentários

**Quando Comentar:**
- Os comentários estão em **português (pt-BR)** e marcam etapas numeradas do pipeline: `# 1. Hardware Check`, `# 4. Configurar data.yaml` (`treinar_crowdhuman.py:27,118`)
- Comentários de justificativa para escolhas não óbvias: `# workers=0  # Compatível com Windows`, `# 640px para capturar corpo inteiro...` (`scripts/train_body.py:32,39`)
- Um comentário em inglês acaba escapando (`main.py:57`); prefira português para consistência
- Evite repetir o código; documente *por que* um fallback/peculiaridade existe

**Docstrings:**
- Docstrings de uma linha em português apenas em `scripts/download_and_convert_crowdhuman.py` (`"""Download resiliente com suporte a retomar download e bypass SSL."""` na linha 28). Use esse estilo (uma linha, português, imperativo) para novas funções auxiliares; não é aplicado em outros lugares

**Comentários TODO:**
- Não usados (sem marcadores TODO/FIXME/HACK na base de código)

## Design de Funções

**Tamanho:**
- A tolerância é alta: `main()` executa 100+ linhas do início ao fim (`treinar_crowdhuman.py:16-143`, `main.py:6-85`). A convenção existente é um `main()` longo por script com estágios de comentário numerados
- Extraia auxiliares apenas para unidades reutilizáveis (download, extração de zip, conversão de anotações) — prefira uma função `snake_case` de nível superior com docstring de uma linha

**Parâmetros:**
- 2-4 parâmetros posicionais é o típico (`convert_odgt_to_yolo(odgt_path, images_dir, labels_output_dir)`); sem padrões de options-dict/kwargs
- Caminhos são sempre parâmetros explícitos ou derivados das constantes de módulo `BASE_DIR`

**Valores de Retorno:**
- Scripts de CLI retornam `None` e sinalizam falha via mensagem impressa + `return`
- Auxiliares retornam um status/contador: `bool` para sucesso de download/extração (`download_file`, `extract_zip`), contagem `int` para conversão (`convert_odgt_to_yolo` retorna `converted_count`)
- Retornos antecipados por guarda de condição preferidos a blocos else aninhados

## Design de Módulos

**Exportações:**
- Sem pacotes, sem `__init__.py`, sem imports entre arquivos do projeto — cada script é autônomo e rederiva os caminhos a partir de `__file__`
- Os scripts se compõem apenas através de `subprocess`: `run_pipeline.py` invoca `scripts/download_and_convert_crowdhuman.py` e depois `scripts/train_body.py` via `subprocess.run([sys.executable, script], check=True)` (`run_pipeline.py:12-20`). Siga isso: reutilização entre scripts = subprocess, não `import`

**Arquivos Barril:**
- Não se aplica

---

*Análise de convenções: 2026-10-08*
*Atualize quando os padrões mudarem*
