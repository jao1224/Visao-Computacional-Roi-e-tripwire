# Integrações Externas

**Data da Análise:** 2026-10-08

## APIs e Serviços Externos

**Registros de ML/Dataset:**
- Hugging Face Hub - dataset de pedestres CrowdHuman (`sshao0516/CrowdHuman`), a única fonte de dados que o código realmente busca.
  - SDK/Cliente (principal): `huggingface_hub.snapshot_download(repo_id='sshao0516/CrowdHuman', repo_type='dataset', allow_patterns=['*.zip','*.odgt'])` em `treinar_crowdhuman.py:63-67`
  - SDK/Cliente (alternativo): streaming HTTP bruto via `requests.get(..., stream=True)` em `scripts/download_and_convert_crowdhuman.py:51`; URL base `https://huggingface.co/datasets/sshao0516/CrowdHuman/resolve/main` (`scripts/download_and_convert_crowdhuman.py:16`)
  - Autenticação: nenhuma - dataset público, nenhum token HF usado em lugar algum (sem referências a token/variável de ambiente no repositório)
  - Arquivos obtidos: `annotation_train.odgt`, `annotation_val.odgt`, `CrowdHuman_val.zip`, `CrowdHuman_train01-03.zip` (`scripts/download_and_convert_crowdhuman.py:18-25`)
  - Cache: `dataset/downloads_cache/` (`scripts/download_and_convert_crowdhuman.py:14`); o cache próprio do HF é reutilizado por `snapshot_download`
  - Observação: a verificação TLS está desativada para esta integração - `verify=False` em `requests.head`/`requests.get` (`scripts/download_and_convert_crowdhuman.py:36,51`) com `urllib3.disable_warnings()` (`scripts/download_and_convert_crowdhuman.py:10`, `treinar_crowdhuman.py:14`) como contorno para proxy/certificado local.

**Downloads:**
- GitHub Releases (Cloudflare) - obtém `cloudflared-windows-amd64.exe` de `https://github.com/cloudflare/cloudflared/releases/latest/download/...`
  - Cliente: `urllib.request.urlretrieve` da stdlib (`scripts/setup_colab_ssh.py:11`)
  - Autenticação: nenhuma
  - Destino: `~/.ssh/cloudflared.exe` (`scripts/setup_colab_ssh.py:6`)

**Manual/Documentado (não automatizado):**
- crowdhuman.org e Roboflow Universe - fontes alternativas manuais de dataset mencionadas em `README.md:43`, sem integração de código.

## Armazenamento de Dados

**Bancos de Dados:**
- Nenhum - nenhum cliente SQL/NoSQL, ORM ou string de conexão em todo o codebase.

**Armazenamento em Arquivos:**
- Apenas sistema de arquivos local - tudo é lido/escrito relativamente ao diretório do projeto:
  - `dataset/` (criado em tempo de execução): `images/{train,val}`, `labels/{train,val}` - produzidos por `scripts/download_and_convert_crowdhuman.py:158-166`
  - `dataset/downloads_cache/` - zips/odgt brutos (`scripts/download_and_convert_crowdhuman.py:14`)
  - `runs/detect/train_crowdhuman_body/` - checkpoints do Ultralytics, `results.csv`, gráficos (`scripts/train_body.py:40-42`)
  - `runs/detect/val_results/val_body/` - saída da validação (`scripts/validate_body.py:18`)
  - `resultados/`, `models/` - pesos finais (`best.pt`, `base_face_weights.pt`, `yolo26n.pt`)
- Google Drive (apenas Colab) - artefatos das execuções salvos em `/content/drive/MyDrive/yolo_crowdhuman_treinamento/runs` quando montado, caso contrário `/content/runs` (`treinar_crowdhuman_colab.ipynb`)

**Cache:**
- Nenhum (sem Redis/Memcached). Apenas cache de downloads no nível do sistema de arquivos, conforme acima.

## Autenticação e Identidade

**Provedor de Autenticação:**
- Nenhum - sem usuários, sem login, sem sessões, sem tokens. Toda chamada externa é anônima/pública.

**Integrações OAuth:**
- Nenhuma

**Acesso SSH (máquina remota de treinamento):**
- `scripts/setup_colab_ssh.py` configura SSH de saída do Windows para o Colab através de um Cloudflare Tunnel: anexa um bloco `Host *.trycloudflare.com` com `ProxyCommand cloudflared access ssh --hostname %h` a `~/.ssh/config` (`scripts/setup_colab_ssh.py:18-24`), `User root`, `Port 22`.
  - Credenciais: qualquer chave SSH já existente em `~/.ssh/` (nenhuma gerenciada/gerada por este repositório).

## Monitoramento e Observabilidade

**Rastreamento de Erros:**
- Nenhum (sem Sentry/Datadog/etc.)

**Análíticas:**
- Nenhuma

**Logs:**
- Apenas stdout - `print(...)` com prefixos `[OK]`/`[Aviso]`/`[STATUS]`, `flush=True` em `treinar_crowdhuman.py`
- O Ultralytics grava suas próprias métricas de treinamento em `runs/detect/train_crowdhuman_body/results.csv` e gráficos JPG (`runs/detect/train_crowdhuman_body/*.jpg`)

## CI/CD e Implantação

**Hospedagem:**
- Nenhuma - sem Dockerfile, sem configuração de implantação em nuvem.
- Google Colab - treinamento interativo em GPU via `treinar_crowdhuman_colab.ipynb`; detecção de runtime via `'google.colab' in sys.modules or os.path.exists('/content')`

**Pipeline de CI:**
- Não detectado - sem `.github/workflows/`, sem pre-commit, sem executor de testes. (O repositório tem um diretório `.git/`, mas todos os arquivos estão atualmente não rastreados.)

## Configuração de Ambiente

**Variáveis de ambiente obrigatórias:**
- Nenhuma. O projeto não lê variáveis de ambiente.

**Local dos segredos:**
- Nenhum presente - sem `.env*`, sem arquivos de credenciais, sem chaves de API referenciadas no código (a busca por `api_key|token|secret` só corresponde à detecção de runtime do Colab).

**Diferenças por ambiente:**
- Windows local: pipeline completo (`run_pipeline.py`), inferência por webcam (`main.py`)
- Colab: mesma lógica de treinamento em `treinar_crowdhuman_colab.ipynb` com persistência no Drive e `!pip install -q ultralytics huggingface_hub pillow`
- Staging/Produção: não aplicável

**Ressalva de portabilidade:**
- `data.yaml:1` e `runs/detect/train_crowdhuman_body/args.yaml:3-4,15,116` incorporam caminhos absolutos de outra máquina (`C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\...`). Apenas `treinar_crowdhuman.py:118-122` reescreve `data.yaml` antes do treinamento; `scripts/train_body.py`/`scripts/validate_body.py` o consomem inalterado.

## Webhooks e Callbacks

**Recebidos:**
- Nenhum

**Enviados:**
- Nenhum

---

*Auditoria de integrações: 2026-10-08*
*Atualizar ao adicionar/remover serviços externos*
