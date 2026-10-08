# Padrões de Testes

**Data da Análise:** 2026-10-08

## Framework de Testes

**Runner:**
- **Nenhum configurado.** Não existem testes pytest, unittest ou nose; não há `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, `pyproject.toml` ou `requirements.txt`
- `pytest` não está instalado no ambiente (Python 3.11.9)
- Sem configuração de CI (sem `.github/`, sem arquivos de workflow) — nada executa testes automaticamente

**Biblioteca de Asserções:**
- Não se aplica (sem testes). Se adicionar testes, use o `assert` embutido do `pytest`

**Comandos de Execução:**
```bash
python -m pytest                        # seria a entrada padrão (uma vez adicionado)
python scripts/validate_body.py         # "teste" de facto atual: métricas de validação do YOLO
python main.py                          # "teste" de facto atual: teste de fumaça da webcam (pressione q para sair)
python run_pipeline.py                  # verificação ponta a ponta do pipeline (download + treino, check=True aborta em caso de falha)
```

## Organização dos Arquivos de Teste

**Localização:**
- Sem arquivos de teste. `test/` na raiz do repositório contém **apenas um asset de amostra** — `test/gemini_generated_video_8d21d35f.mp4` (6,3 MB). São dados, não uma suíte de testes, apesar do nome do diretório
- **Não** coloque testes em `test/` sem antes renomeá-lo/limpá-lo — o diretório é ambíguo

**Nomenclatura (recomendado para seguir as normas do Python):**
- Testes unitários: `tests/test_<módulo>.py` (novo diretório `tests/` na raiz do repositório)

**Estrutura:**
```
scriptvisaocomput/            # (atual)
├── main.py
├── run_pipeline.py
├── treinar_crowdhuman.py
├── scripts/
│   ├── download_and_convert_crowdhuman.py
│   ├── train_body.py
│   ├── validate_body.py
│   └── setup_colab_ssh.py
├── test/                     # NÃO é testes - contém gemini_generated_video_8d21d35f.mp4
└── (sem tests/, sem conftest.py)
```

## Estrutura de Testes

**Organização da Suíte:**
- Não há padrão de suíte existente para copiar. Padrão recomendado para testes novos (estilo pytest):
```python
# tests/test_convert_odgt.py
def test_convert_odgt_writes_yolo_labels(tmp_path):
    # preparar
    ...
    # executar
    count = convert_odgt_to_yolo(odgt_path, images_dir, labels_dir)
    # asserir
    assert count == 1
    assert "0 0.500000 0.500000 0.250000 0.500000" in (labels_dir / "img1.txt").read_text()
```

**Padrões:**
- Configuração: fixtures do pytest (`tmp_path` para diretórios de dataset) — sem precedente de `beforeEach`/`setUp`
- Limpeza: confiar na limpeza automática de `tmp_path`/`monkeypatch`; nada global a restaurar
- Estrutura: preparar/executar/asserir com comentários explícitos (coincide com o hábito de comentários numerados da base de código)

## Mocking

**Framework:**
- Nenhum em uso. Escolha padrão: `pytest` + `unittest.mock` (`monkeypatch`, `patch`)

**Padrões:**
```python
# Recomendado para esta base de código: mockar as fronteiras de rede + sistema de arquivos
from unittest.mock import patch, MagicMock

@patch("scripts.download_and_convert_crowdhuman.requests.get")
def test_download_file_writes_chunks(mock_get, tmp_path):
    mock_get.return_value.iter_content.return_value = [b"a" * 1024, b"b" * 1024]
    mock_get.return_value.headers = {"content-length": "2048"}
    assert download_file("f.zip", str(tmp_path / "f.zip")) is True
```

**O que Mockar:**
- Rede: `requests.get` / `requests.head` (`scripts/download_and_convert_crowdhuman.py:36,51`), `huggingface_hub.snapshot_download` (`treinar_crowdhuman.py:63`)
- Modelo Ultralytics: `ultralytics.YOLO` (construtor, `.train()`, `.val()`) — o treino dura horas de GPU
- Webcam/OpenCV: `cv2.VideoCapture` (`main.py:28`) para qualquer teste de `main.py`
- `torch.cuda.is_available()` para ramos dependentes de hardware (`treinar_crowdhuman.py:28`, seleção de dispositivo em `train_body.py`)
- `subprocess.run` ao testar `run_pipeline.py`

**O que NÃO Mockar:**
- Funções puras: `convert_odgt_to_yolo`, `flatten_directory`, `extract_zip` — teste contra arquivos reais em `tmp_path`
- Lógica de parsing de JSON/zip (use arquivos de fixture pequenos)

## Fixtures e Fábricas

**Dados de Teste:**
```python
# Recomendado: fixture ODGT mínima (uma linha de JSON do CrowdHuman)
ODGT_LINE = '{"ID": "img1", "gtboxes": [{"tag": "person", "fbox": [100, 50, 200, 400]}]}'

# Saída esperada do rótulo YOLO para uma imagem de 640x400:
# "0 0.250000 0.562500 0.312500 1.000000"  (limitado pelas guarda de max/min)
```
- Um `.jpg` pequeno pode ser gerado com `PIL.Image.new("RGB", (640, 400))` na fixture em vez de distribuir binários

**Localização:**
- Não existem fixtures. Recomendado: `tests/fixtures/` para amostras estáticas `.odgt`/`.jpg`; fábricas inline no arquivo de teste para dados gerados

## Cobertura

**Requisitos:**
- Nenhum imposto (sem ferramenta de cobertura, sem gate de CI, sem meta)

**Configuração:**
- Não configurada. Se adicionada: `pytest-cov` com `--cov=scripts --cov=main` e exclusões para `treinar_crowdhuman_colab.ipynb`

**Ver Cobertura:**
```bash
python -m pytest --cov=scripts --cov-report=term-missing
```

## Tipos de Teste

**Testes Unitários:**
- Escopo (recomendado): matemática de conversão de anotações (`convert_odgt_to_yolo`, limites em `download_and_convert_crowdhuman.py:136-139`), lógica de retomada de download/verificação de tamanho (`download_file`, `:33-44`), resolução de fallback de caminhos (`main.py:11-19`, `scripts/train_body.py:9-12`)
- Mocking: apenas rede + sistema de arquivos; alimente arquivos pequenos reais via `tmp_path`
- Velocidade: deve executar sem GPU/pesos de modelo

**Testes de Integração:**
- Não presentes. Equivalentes mais próximos são execuções de script com dados reais:
  - `python run_pipeline.py` — orquestração completa download→treino, aborta na primeira falha (`check=True`)
  - O Ultralytics emite seus próprios artefatos de treino para `runs/detect/train_crowdhuman_body/` (`args.yaml`, imagens de batch) — inspecione-os para verificações de sanidade

**Testes E2E:**
- Não usados. Apenas verificação manual:
  - `python main.py` — verificação da webcam com humano no loop (o HUD mostra FPS + contagem de pessoas, `q` para sair; `main.py:73-82`)
  - `python scripts/validate_body.py` — imprime mAP@0.5, mAP@0.5:0.95, P, R, F1 a partir de `model.val()` (`validate_body.py:33-39`)
  - A célula 1 do notebook `treinar_crowdhuman_colab.ipynb` está rotulada "Teste de Conexao e Deteccao de GPU" — apenas teste de fumaça de conectividade/GPU

## Padrões Comuns

**Testes Assíncronos:**
- Não se aplica — a base de código é totalmente síncrona

**Testes de Erro:**
```python
# Sem precedente no repositório. Alvos recomendados para testes de caminho de falha:
def test_missing_model_returns_early(capsys, monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda p: False)   # todos os candidatos ausentes
    main()
    assert "Erro: Nenhum modelo encontrado" in capsys.readouterr().out   # main.py:21
```

**Testes de Snapshot:**
- Não usados

**Verificações de Regressão de Métricas (a versão do domínio das asserções):**
- Validadas através do objeto de métricas de `model.val()`: `metrics.box.map50`, `metrics.box.map`, `metrics.box.mp`, `metrics.box.mr` (`scripts/validate_body.py:34-38`)
- F1 calculado inline com guarda de epsilon `1e-16` (`validate_body.py:38`)
- Se automatizar: asserir limiares (ex.: `metrics.box.map50 >= 0.50`) após o treino; os resultados ficam em `runs/detect/train_crowdhuman_body/results.csv`

---

*Análise de testes: 2026-10-08*
*Atualize quando os padrões de teste mudarem*
