# Preocupações do Código-Fonte

**Data da Análise:** 2026-10-08

Escopo: repositório completo em `C:\Users\Windows\Desktop\scriptvisaocomput` (pipeline de detecção de corpo inteiro YOLO/CrowdHuman). Python 3.11.9, `ultralytics 8.3.169`, `torch 2.6.0`, `opencv-python 4.12.0.88` instalados. O repositório Git existe com **zero commits** e **sem `.gitignore`**.

## Dívida Técnica

**Sem manifesto de dependências:**
- Problema: Não há `requirements.txt`, `pyproject.toml`, `environment.yml` ou lockfile em lugar nenhum do repositório; todo pacote de terceiros é implícito.
- Arquivos: raiz do repositório (ausente); importações espalhadas entre `main.py:3-4`, `treinar_crowdhuman.py:6-11`, `scripts/download_and_convert_crowdhuman.py:5-7`
- Motivo: os scripts foram escritos para rodar em uma máquina onde o ambiente já estava provisionado (um `.venv` irmão existe em `C:\Users\Windows\Desktop\visao computacional\.venv`)
- Impacto: a configuração não é reproduzível; uma máquina nova não consegue instalar o projeto; execuções em CI/Colab divergem do comportamento local; o comportamento de `YOLO('yolo26n.pt')` depende da build exata do `ultralytics`
- Abordagem da correção: adicionar `requirements.txt` (ou `pyproject.toml`) fixando `ultralytics`, `torch`, `torchvision`, `opencv-python`, `huggingface_hub`, `requests`, `pillow`; documentar a etapa de instalação no `README.md`

**Sem `.gitignore`, com ~29 MB de binários prontos para o primeiro commit:**
- Problema: o repositório ainda não tem commits nem regras de ignoramento; `git status` mostra `models/`, `resultados/`, `runs/`, `test/`, `yolo26n.pt` como não rastreados
- Arquivos: `yolo26n.pt` (5.5 MB), `models/base_face_weights.pt` (5.5 MB), `resultados/best.pt` (5.4 MB), `resultados/best (1).pt` (5.4 MB), `test/gemini_generated_video_8d21d35f.mp4` (6.2 MB), `runs/detect/train_crowdhuman_body/*.jpg` (~2.1 MB)
- Motivo: pesos e artefatos foram mantidos ao lado do código por conveniência
- Impacto: o primeiro commit infla o repositório permanentemente; saídas futuras de treinamento (`runs/`, `dataset/downloads_cache/` — os zips do CrowdHuman têm escala de GB) também serão commitados; o repositório se torna inclonável
- Abordagem da correção: adicionar um `.gitignore` cobrindo `dataset/`, `runs/`, `resultados/`, `models/*.pt`, `*.pt`, `test/*.mp4`, `__pycache__/`; decidir explicitamente qual único arquivo de pesos canônico (se algum) será rastreado via Git LFS

**Lógica de download/conversão do dataset duplicada três vezes:**
- Problema: o download do CrowdHuman + conversão `odgt → YOLO` existe em três cópias independentes que já divergiram
- Arquivos: `scripts/download_and_convert_crowdhuman.py:27-150` (requests + `verify=False`), `treinar_crowdhuman.py:61-116` (huggingface_hub `snapshot_download`), `treinar_crowdhuman_colab.ipynb` célula 4 (cópia da versão do notebook)
- Motivo: evolução notebook → script → pipeline independente sem extração
- Impacto: uma correção de bug em uma cópia não se propaga; as três cópias usam fontes de download diferentes (HTTP direto vs cache do HF hub) e comportamentos de extração diferentes
- Abordagem da correção: extrair um módulo (ex.: `scripts/dataset.py`) com `download_and_convert(...)`, `extract_zip(...)`, `convert_odgt_to_yolo(...)`; fazer os scripts `.py` e o notebook o importarem (notebook: adicionar a raiz do repositório ao `sys.path`)

**Hiperparâmetros de treinamento fixados em três lugares, já inconsistentes:**
- Problema: a configuração de treinamento está embutida em cada ponto de entrada, com valores diferentes
- Arquivos: `scripts/train_body.py:29-43` (`box=8.5, cls=0.8, batch=8, workers=0`) vs `treinar_crowdhuman.py:128-142` (`box=10.0, cls=0.7, batch=auto 8/32`, sem `workers`) vs `treinar_crowdhuman_colab.ipynb` célula 6 (`box=10.0, cls=0.7`)
- Impacto: os resultados não são comparáveis entre execuções; é impossível dizer qual configuração produziu `resultados/best.pt` (ver `runs/detect/train_crowdhuman_body/args.yaml:84-87` — a última execução registrada usou `box=8.5, cls=0.8`, ou seja, `train_body.py`)
- Abordagem da correção: uma única fonte de configuração (um `train_config.yaml` ou módulo de constantes compartilhadas) consumida pelos três pontos de entrada

**`data.yaml` é simultaneamente saída gerada e entrada rastreada:**
- Problema: `treinar_crowdhuman.py:118-122` e a célula 5 do notebook *sobrescrevem* `data.yaml` em tempo de execução, enquanto `scripts/train_body.py:14` e `scripts/validate_body.py:17` *leem* a cópia versionada
- Arquivos: `data.yaml`
- Impacto: ruído de alterações/diffs; qual versão é a autoritativa depende de qual script rodou por último (esta é a causa direta do bug de pipeline quebrado abaixo)
- Abordagem da correção: gerar em `dataset/data.yaml` (dentro do diretório de dataset ignorado pelo git) ou resolver os caminhos programaticamente em tempo de execução em vez de persistir caminhos absolutos

**A inicialização de pesos depende de um diretório fora do repositório:**
- Problema: `treinar_crowdhuman.py:37-45` e a célula 3 do notebook recorrem a `../runs/detect/train-14/weights/best.pt` (uma execução de detecção de rosto em um projeto irmão) e depois ao caminho relativo simples `'yolo26n.pt'` (dependente do CWD)
- Arquivos: `treinar_crowdhuman.py:38,45`; `treinar_crowdhuman_colab.ipynb` célula 3; `scripts/train_body.py:8-12`
- Motivo: o transfer learning começou a partir de um modelo de rosto (`models/base_face_weights.pt`) e a linhagem nunca foi incorporada ao repositório
- Impacto: em qualquer outra máquina, o caminho principal de inicialização está ausente; o fallback relativo `'yolo26n.pt'` depende silenciosamente do diretório atual do shell (o Ultralytics tentará um download pela internet caso não seja encontrado)
- Abordagem da correção: incorporar os pesos de inicialização pretendidos em `models/` (ou baixá-los explicitamente) e resolver todos os fallbacks em relação a `__file__`

## Bugs Conhecidos

**`run_pipeline.py` falha já de primeira (caminho absoluto de dataset desatualizado):**
- Sintomas: o Estágio 2 aborta com um erro de caminho de dataset do Ultralytics após o Estágio 1 concluir com sucesso
- Gatilho: executar `python run_pipeline.py` em um clone novo — o estágio 1 (`scripts/download_and_convert_crowdhuman.py`) baixa para `./dataset/`, então o estágio 2 (`scripts/train_body.py:14`) carrega o `data.yaml` versionado, cujo `path:` aponta para `C:\Users\ferna\Desktop\visao computacional\yolo_crowdhuman_body\dataset` (`data.yaml:1`)
- Causa raiz: `data.yaml` só é regenerado por `treinar_crowdhuman.py`, que `run_pipeline.py` nunca chama
- Contorno: executar manualmente `python treinar_crowdhuman.py` uma vez (ele reescreve `data.yaml`), ou editar `data.yaml:1` para `path: <repo>/dataset`
- Correção: gerar `data.yaml` dentro da etapa de download (`scripts/download_and_convert_crowdhuman.py:152`) para que ele esteja sempre em sincronia com onde os dados realmente foram parar

**`scripts/validate_body.py` não pode rodar nesta máquina (pesos ausentes + CUDA fixo):**
- Sintomas: `FileNotFoundError` de `YOLO(...)` ou um erro de dispositivo CUDA
- Gatilho: `python scripts/validate_body.py` — `runs/detect/train_crowdhuman_body/weights/` existe, mas está **vazio** (sem `best.pt`, sem `results.csv`), então o fallback em `scripts/validate_body.py:9-13` resolve para `C:\Users\Windows\Desktop\models\yolo26n.pt`, que não existe; mesmo que existisse, `scripts/validate_body.py:27` fixa `device=0`
- Causa raiz: os pesos treinados estão apenas em `resultados/best.pt`; a cadeia de fallback assume uma pasta irmã `../models/`; o dispositivo não é detectado
- Contorno: apontar `scripts/validate_body.py:8` para `resultados/best.pt` e mudar `device=0` para `device=0 if torch.cuda.is_available() else 'cpu'`
- Correção: unificar a descoberta de pesos (mesma lógica de lista de candidatos de `main.py:11-19`) e detectar o dispositivo

**O script de download afirma suporte a retomada que não implementa:**
- Sintomas: downloads interrompidos reiniciam do byte 0; código morto fica ao lado da requisição
- Arquivos: `scripts/download_and_convert_crowdhuman.py:28` (o docstring diz "suporte a retomar download"), `scripts/download_and_convert_crowdhuman.py:47-49` (`headers = {}`, `mode = 'wb'`, `initial_pos = 0` — nunca usados, sem cabeçalho `Range`)
- Impacto: baixar novamente os zips do CrowdHuman de várias centenas de MB após uma queda de conexão; docstring enganoso
- Correção: implementar retomada baseada em `Range` com um arquivo temporário `.part` + rename, ou corrigir o docstring

**Erros de download da etapa inteira engolidos; o treinamento então inicia com um dataset vazio:**
- Sintomas: `[Aviso download] ...` é impresso, então o Ultralytics falha depois com um confuso erro de "image not found" / dataset de comprimento zero (ou treina com um punhado de imagens)
- Gatilho: qualquer falha de rede/autenticação durante a etapa de snapshot do HF
- Arquivos: `treinar_crowdhuman.py:62-116` (um único `try/except Exception` envolve o download **e** a conversão; o manipulador em `:115-116` apenas imprime), depois `treinar_crowdhuman.py:128` inicia o treinamento incondicionalmente; mesmo padrão na célula 4 do notebook
- Contorno: verificar a presença de `[OK] Dataset pronto!` antes de confiar em uma execução de treinamento
- Correção: relançar a exceção após registrar no log, ou verificar `len(os.listdir(train_img_dir)) > 0` antes de chamar `model.train(...)`

**`flatten_directory` falha em reexecuções na cópia do `treinar_crowdhuman.py`:**
- Sintomas: `FileExistsError` (Windows) quando `Images/` ainda contém arquivos cujo destino já existe; capturado pelo manipulador genérico acima, truncando silenciosamente o dataset
- Arquivos: `treinar_crowdhuman.py:80-84` (`os.rename` sem verificação de destino) — note que a versão independente em `scripts/download_and_convert_crowdhuman.py:89-93` protege corretamente com `if not os.path.exists(dst)`
- Correção: portar a versão protegida (outro sintoma da lógica triplicada)

**Saída de terminal enganosa no script de download:**
- Sintomas: imprime `Iniciando treinamento automaticamente...` e sai sem iniciar nada
- Arquivo: `scripts/download_and_convert_crowdhuman.py:196-198`
- Correção: remover a mensagem ou realmente encadear para o treinamento (delegando a `run_pipeline.py`)

**Manipulador da webcam vaza em caso de erro no `main.py`:**
- Sintomas: a câmera permanece reivindicada pelo processo após uma exceção (é preciso matar o Python para liberá-la); a janela nunca fecha
- Gatilho: qualquer exceção dentro do loop (ex.: erro de inferência do modelo, janela fechada externamente)
- Arquivos: `main.py:39-85` — `webcam.release()` / `cv2.destroyAllWindows()` em `:84-85` só rodam na saída normal do loop; não há `try/finally`
- Correção: envolver o loop em `try/finally`

**Artefato de peso duplicado:**
- Sintomas: dois arquivos idênticos de 5.4 MB; qual deles é o "atual" é impossível saber pelo nome
- Arquivos: `resultados/best.pt` e `resultados/best (1).pt` (SHA-256 idênticos: `E6C59F44…`)
- Correção: excluir `best (1).pt`; nunca copiar pesos manualmente — promovê-los de `runs/.../weights/` por meio de uma etapa de script

## Considerações de Segurança

**Verificação de certificado TLS desativada para todos os downloads de dataset:**
- Risco: um atacante man-in-the-middle pode substituir as imagens *e* rótulos do CrowdHuman — anotações envenenadas direcionam diretamente o modelo treinado; os payloads dos zips também são controlados pelo atacante
- Arquivos: `scripts/download_and_convert_crowdhuman.py:10` (`urllib3.disable_warnings(...)`), `:36` (`requests.head(..., verify=False)`), `:51` (`requests.get(..., verify=False)`); `treinar_crowdhuman.py:14` (`urllib3.disable_warnings()`)
- Mitigação atual: nenhuma (o comentário em `scripts/download_and_convert_crowdhuman.py:9` cita proxies/certs locais como motivo)
- Recomendações: verificar TLS por padrão e permitir a desativação por meio de uma variável de ambiente (`CROWDHUMAN_INSECURE=1`); se um proxy corporativo for a causa real, instalar a CA do proxy em vez de desativar a verificação globalmente

**Extração de zip sem validação de caminho (zip-slip) em downloads não verificados:**
- Risco: um zip manipulado pode gravar arquivos fora do diretório do dataset (gravação arbitrária de arquivos, incluindo pastas de inicialização / configuração SSH)
- Arquivos: `scripts/download_and_convert_crowdhuman.py:77-78` (`zip_ref.extractall(...)`), `treinar_crowdhuman.py:73-74`, célula 4 do notebook — agravando o problema do `verify=False` acima
- Mitigação atual: os arquivos vêm de um repositório HuggingFace conhecido (mas por meio de TLS não verificado)
- Recomendações: validar os caminhos dos membros (`os.path.realpath` deve permanecer sob o destino) antes da extração, ou usar a filtragem de membros de `zipfile`

**`scripts/setup_colab_ssh.py` amplia a confiança SSH e instala um binário não assinado:**
- Risco: (a) baixa `cloudflared.exe` de `releases/latest` sem fixação de checksum/assinatura (`scripts/setup_colab_ssh.py:10-11`); (b) acrescenta uma regra curinga ao `~/.ssh/config` do usuário — `Host *.trycloudflare.com` com `User root` e um `ProxyCommand` (`scripts/setup_colab_ssh.py:18-24`) — de modo que *qualquer* host que corresponda a esse curinga é contactado como `root` por meio da ferramenta
- Mitigação atual: a entrada de configuração só é gravada se a string de marcação estiver ausente (`scripts/setup_colab_ssh.py:31`); o ProxyCommand ainda requer credenciais de acesso do Cloudflare para autenticar
- Recomendações: fixar a versão do cloudflared + SHA-256; restringir o padrão `Host` ao hostname específico do túnel; documentar no `README.md` que este script altera o `~/.ssh/config`

**Desserialização pickle não confiável dos pesos do modelo:**
- Risco: arquivos `.pt` são pickles do torch; carregar um arquivo de pesos adulterado executa código arbitrário. A proveniência dos pesos não é rastreada (ver Dívida Técnica), e um dos arquivos é literalmente um duplicado com nome de copiar-e-colar
- Arquivos: `resultados/best.pt`, `resultados/best (1).pt`, `models/base_face_weights.pt`, `yolo26n.pt` — carregados em `main.py:25`, `scripts/train_body.py:26`, `scripts/validate_body.py:21`, `treinar_crowdhuman.py:48`
- Mitigação atual: o `torch 2.6.0` usa `weights_only=True` como padrão para `torch.load`, e o Ultralytics respeita isso em versões recentes; o `ultralytics` está **sem versão fixada**, então essa mitigação não é garantida
- Recomendações: fixar `ultralytics`/`torch`, registrar um checksum para cada arquivo de pesos aceito, preferir os pesos oficiais publicados a artefatos copiados manualmente

**Divulgação de caminho/nome de usuário em artefatos de configuração rastreados:**
- Risco: baixo — expõe o nome de usuário do autor original e a estrutura de diretórios (`C:\Users\ferna\...`) a qualquer pessoa com acesso ao repositório
- Arquivos: `data.yaml:1`, `runs/detect/train_crowdhuman_body/args.yaml:3-4,15,116`
- Recomendações: regenerar `data.yaml` por máquina (ver Dívida Técnica); adicionar os artefatos de `runs/` ao `.gitignore`

**Varredura de segredos:** Nenhum arquivo `.env`, chave de API, token ou credencial detectado em lugar nenhum do repositório. Não se aplica além dos itens acima.

## Gargalos de Desempenho

**Dataloader com um único worker durante o treinamento:**
- Problema: `workers=0` força o carregamento/aumento serial de amostras dentro do próprio processo
- Arquivos: `scripts/train_body.py:39`
- Causa: solução de compatibilidade de multiprocessamento no Windows (comentário: `# Compatível com Windows`)
- Caminho de melhoria: usar `workers=2..4` (o Ultralytics trata o spawn no Windows); observe que os outros pontos de entrada (`treinar_crowdhuman.py`, notebook) omitem `workers` completamente e usam o padrão de 8 — o comportamento é inconsistente, não apenas lento

**Download de dataset serial e não retomável:**
- Problema: seis arquivos baixados um de cada vez, blocos de 1 MB, uma requisição `HEAD` por arquivo antes de iniciar
- Arquivos: `scripts/download_and_convert_crowdhuman.py:169-171` (loop), `:56-66` (loop de blocos)
- Causa: streaming com `requests` sem concorrência; sem retomada (ver Bugs Conhecidos)
- Caminho de melhoria: implementar retomada + downloads paralelos opcionais com `concurrent.futures`; pular o `HEAD` quando um manifesto de checksum estiver disponível

**Loop de inferência em tempo real limitado e verboso:**
- Problema: cada quadro é registrado pelo Ultralytics (`verbose=True`), além do desenho por caixa, a um alvo autoimposto de 5 FPS
- Arquivos: `main.py:35-36` (`target_fps = 5`), `main.py:48` (`verbose=True`)
- Causa: a E/S do console e o limite do `cv2.waitKey` dominam; não há pulagem de quadros (`stream=True` não usado) nem exportação HALF/INT8
- Caminho de melhoria: definir `verbose=False`, considerar `model(frame, stream=True)` e exportar para ONNX/TensorRT se for necessária uma taxa de FPS maior

**A impressão de progresso spammeia o terminal:**
- Problema: `int(pct) % 10 == 0` é verdadeiro para *cada* bloco que abrange aquele inteiro, então a linha de porcentagem é reimpressa centenas de vezes por arquivo
- Arquivos: `scripts/download_and_convert_crowdhuman.py:65-66`
- Correção: imprimir apenas quando o percentual inteiro muda (acompanhamento com `last_pct`)

## Áreas Frágeis

**Resolução do caminho do modelo (quatro cadeias de fallback ad hoc diferentes):**
- Arquivos: `main.py:11-19` (lista de candidatos), `scripts/train_body.py:8-12`, `scripts/validate_body.py:8-13`, `treinar_crowdhuman.py:37-45`
- Por que é frágil: cada cadeia aponta para locais diferentes, duas delas vão para **fora** do repositório (`../models/yolo26n.pt` não existe nesta máquina; `../runs/detect/train-14` não existe), uma usa um caminho relativo ao CWD
- Falhas comuns: fallback silencioso para um modelo *base, não treinado* (a validação então reporta um mAP sem significado — `scripts/validate_body.py:13` apenas imprime um aviso), ou uma falha catastrófica
- Modificação segura: não adicionar uma quinta cadeia; consolidar em um único resolvedor (ex.: `resolve_weights()` retornando um caminho + string de proveniência) e fazer o chamador falhar de forma explícita em vez de recorrer a fallback
- Cobertura de testes: nenhuma

**Três cópias divergentes do mesmo pipeline:**
- Arquivos: `scripts/*` (pipeline), `treinar_crowdhuman.py` (tudo-em-um), `treinar_crowdhuman_colab.ipynb` (notebook)
- Por que é frágil: as correções precisam ser aplicadas 3×; elas já discordam sobre hiperparâmetros, `workers`, segurança do `os.rename` e fonte de download
- Falhas comuns: relatos de "funciona no notebook, falha no script"
- Modificação segura: alterar uma cópia apenas depois de verificar as outras duas, ou investir primeiro no refatoramento para módulo compartilhado
- Cobertura de testes: nenhuma

**O diretório de artefatos de treinamento está em um estado parcial e inconsistente:**
- Arquivos: `runs/detect/train_crowdhuman_body/` — contém `args.yaml` + 4 JPGs de resultado, mas `weights/` está vazio e `results.csv` (documentado em `README.md:31`) está ausente
- Por que é frágil: `exist_ok=True` em toda chamada de treinamento (`scripts/train_body.py:42`, `treinar_crowdhuman.py:141`, célula 6 do notebook) sobrescreve a execução anterior no local; o estado atual é o resultado de tal sobrescrita (pesos apagados, gráficos deixados para trás)
- Falhas comuns: perder o modelo anterior ao retreinar; leitores assumindo que `weights/best.pt` existe porque a pasta existe
- Modificação segura: definir `exist_ok=False` (ou `name=` com timestamp) e tratar `runs/` como totalmente descartável/ignorado pelo git
- Cobertura de testes: nenhuma

**O `data.yaml` gerado e `runs/**/args.yaml` são tratados como código-fonte:**
- Arquivos: `data.yaml`, `runs/detect/train_crowdhuman_body/args.yaml`
- Por que é frágil: caminhos absolutos de outra máquina (`C:\Users\ferna\...`); qualquer script que os leia em outro host quebra
- Modificação segura: nunca editá-los à mão — regenerar (`treinar_crowdhuman.py:118-122`) ou adicioná-los ao `.gitignore`
- Cobertura de testes: nenhuma

## Limites de Escala

### Limitação conhecida: Oclusão frontal não detectada (Fase 2)
- **Sintoma:** Pessoa atrás de outra (oclução > 50-70%) não recebe caixa do YOLO → ByteTrack não rastreia → não conta.
- **Causa raiz:** Detector 2D single-view (YOLO) não infere pessoas parciais; não há pose/keypoints nem multi-view.
- **Impacto:** Contagem subestima fluxo em áreas densas; cards de ocupação ficam abaixo do real.
- **Mitigação atual:** Nenhuma (aceita-se a limitação do detector).
- **Caminho realista (fora da Fase 2):**
  1. Modelo maior (`yolov8m/l`) melhora separação marginalmente.
  2. Fine-tune no domínio (vídeo do hotel) ajuda.
  3. **Câmera zenital / top-down** elimina a maioria das oclusões frontais.
  4. **Fase 6 (Multi-câmera):** ângulos complementares cobrem pontos cegos.
  5. Re-ID / feature matching (fora de escopo — LGPD proíbe persistir embeddings).

---

**Treinamento em GPU única / máquina única:**
- Capacidade atual: heurística de batch em `treinar_crowdhuman.py:125` — batch 32 apenas se VRAM > 15 GB, senão batch 8 com `imgsz=640`, 300 epochs, `patience=50`
- Limite: o treino do CrowdHuman tem ~15k imagens; em uma GPU menor a execução leva horas a dias, e `workers=0` (em `scripts/train_body.py:39`) deixa a E/S da CPU como teto
- Sintomas no limite: CUDA OOM (o Ultralytics reduz o batch apenas quando `batch=-1`, não aqui), ou utilização extremamente baixa da GPU devido ao loader com um único worker
- Caminho de escala: usar batch automático (`batch=-1`), habilitar os workers do dataloader, ou mover a execução para o Colab (o notebook é o caminho existente para isso)

**Inferência apenas local:**
- Capacidade atual: 1 webcam, índice fixado em `0` (`main.py:28`), alvo de 5 FPS (`main.py:35`)
- Limite: sem suporte a múltiplas câmeras/streaming; cada quadro é desenhado e exibido sincronamente
- Caminho de escala: parametrizar a fonte (`sys.argv`/configuração), processar vários streams em lote por uma única instância do modelo, recorrer à exportação ONNX/TensorRT

**Orçamento de disco:**
- Capacidade atual: o repositório ocupa atualmente ~29 MB excluindo `.git`; o cache de download do CrowdHuman acrescenta várias centenas de MB (`dataset/downloads_cache/`, `scripts/download_and_convert_crowdhuman.py:14`), e as imagens extraídas, mais ainda
- Limite: espaço livre desconhecido e não verificado; nada limpa o `downloads_cache/`
- Caminho de escala: adicionar `dataset/` ao `.gitignore`, acrescentar uma flag `--clean` que exclui os zips após a extração bem-sucedida

## Dependências em Risco

**`ultralytics` (instalado 8.3.169, sem versão fixada):**
- Risco: o projeto é rotulado como "YOLOv26" em todo lugar (`README.md`, `scripts/train_body.py:18`, `main.py:76`), mas o pacote instalado distribui YAMLs de arquitetura apenas para `v3–v12, v10, rt-detr` — sem config `26/`; `yolo26n.pt` carrega hoje apenas porque o checkpoint de pesos traz sua própria config, e o pacote não está travado por versão
- Impacto: qualquer `pip install -U ultralytics` pode alterar os padrões do treinador, remover a URL dos pesos `yolo26` ou mudar o tratamento do esquema do `data.yaml` — treinamento/validação quebram sem mudança no código
- Plano de migração: fixar `ultralytics==8.3.169` (ou a versão validada) no novo arquivo de requisitos; confirmar explicitamente o suporte a `YOLO26` antes de atualizar

**`opencv-python` 4.12.0.88 + `opencv-python-headless` 5.0.0.93 ambos instalados:**
- Risco: dois pacotes fornecem o mesmo módulo `cv2` em versões principais diferentes; aquele que vier por último no `sys.path` prevalece
- Impacto: `main.py` usa funções de GUI (`cv2.imshow` em `main.py:76`) que **não existem** na build headless; a ordem de importação determina se a demonstração da webcam funciona
- Plano de migração: manter exatamente um — `opencv-python` para este repositório; desinstalar a build headless do ambiente compartilhado (ou isolar o projeto em seu próprio venv, o que também é a correção para o manifesto de dependências ausente)

**Espelho do dataset HuggingFace (`sshao0516/CrowdHuman`):**
- Risco: reupload por terceiros do CrowdHuman; o `snapshot_download` em `treinar_crowdhuman.py:63-67` e a URL base em `scripts/download_and_convert_crowdhuman.py:16` dependem de ele permanecer disponível e inalterado
- Impacto: o estágio 1 do pipeline para de funcionar; não há espelho local nem fallback de checksum
- Plano de migração: armazenar em cache os zips (já é a função de `dataset/downloads_cache/`) e registrar os hashes dos arquivos; manter o download oficial crowdhuman.org documentado no `README.md:43` como fonte alternativa

**Licenciamento do dataset CrowdHuman:**
- Risco: o CrowdHuman é distribuído sob termos de pesquisa/não comercial; nada no repositório registra a aceitação nem o uso pretendido de `resultados/best.pt`
- Impacto: lacuna de conformidade se o modelo for distribuído comercialmente
- Plano de migração: adicionar uma nota ao `README.md` declarando a licença do dataset e o uso pretendido dos pesos treinados

**`requests` / `urllib3` usados apenas com `verify=False`:**
- Risco: o único uso dessas bibliotecas no repositório é a busca com TLS desativado (ver Segurança)
- Plano de migração: se a verificação não puder ser restaurada, considerar se o downloader do `huggingface_hub` (que verifica o TLS) deveria ser o único caminho de download

## Funcionalidades Críticas Ausentes

**Definição de dependências/ambiente:**
- Problema: não há `requirements.txt`/`pyproject.toml` (ver Dívida Técnica)
- Contorno atual: copiar a lista de pacotes de uma máquina funcional ou ler as importações à mão
- Impede: onboarding simples, CI, execuções reproduzíveis no Colab
- Complexidade de implementação: Baixa (um arquivo + uma lista fixada)

**`.gitignore` e política de artefatos:**
- Problema: nada exclui pesos, datasets, runs, nem o arquivo solto `test/gemini_generated_video_8d21d35f.mp4`
- Contorno atual: `git add` manual cuidadoso
- Impede: o primeiro commit seguro; qualquer colaboração futura
- Complexidade de implementação: Baixa

**Etapa de promoção/proveniência do modelo:**
- Problema: nenhum script copia `runs/detect/train_crowdhuman_body/weights/best.pt` → `resultados/best.pt`, então a execução de treinamento, métricas e configuração do peso em produção não são registradas (e `runs/.../weights/` está atualmente vazio)
- Contorno atual: cópia manual (que produziu o duplicado `best (1).pt`)
- Impede: reprodutibilidade, comparação de regressão entre versões do modelo, confiança nos números de validação
- Complexidade de implementação: Baixa–Média (um `promote_weights.py` que também registra o mAP do `results.csv`)

**Argumentos de CLI / configuração:**
- Problema: índice da câmera (`main.py:28`), limiares (`main.py:48`: `conf=0.25, iou=0.60`), dispositivo (`scripts/validate_body.py:27`), epochs/batch/pesos de loss estão todos fixados no código
- Contorno atual: editar o código-fonte
- Impede: rodar contra um arquivo de vídeo, validação apenas na CPU, ajustes sem mudanças no código
- Complexidade de implementação: Baixa (`argparse` por script)

**Barreira de validação antes do treinamento/inferência:**
- Problema: nada verifica se o dataset não está vazio antes de `model.train(...)` (`treinar_crowdhuman.py:128`) nem se os pesos foram treinados (e não são os do COCO base) antes da inferência em `main.py`
- Contorno atual: ler os avisos do console
- Impede: execuções ruins silenciosas (treinar em um diretório vazio; demonstrar um modelo não treinado)
- Complexidade de implementação: Baixa (afirmar contagens/caminhos antes da chamada)

**Registro de logs e acompanhamento de execuções:**
- Problema: apenas `print()` (sem `logging`, sem exportação de CSV/métricas além da própria saída `runs/` do Ultralytics, e `results.csv` está ausente do diretório de execução commitado)
- Contorno atual: rolar a saída do terminal
- Impede: diagnosticar uma execução de treinamento noturna que falhou; comparar experimentos
- Complexidade de implementação: Média (`logging` da stdlib + manter o `results.csv` do Ultralytics em metadados de experimento versionados)

## Lacunas de Cobertura de Testes

**Todo o código-fonte — zero testes automatizados:**
- O que não é testado: tudo; não há framework de testes, nem diretório `tests/`, nem arquivos de teste (`*.test.*` / `*.spec.*` / `test_*.py`) em lugar nenhum
- Arquivos: todos (`main.py`, `run_pipeline.py`, `treinar_crowdhuman.py`, `scripts/*.py`)
- Risco: o conversor de anotações (normalização de coordenadas em `scripts/download_and_convert_crowdhuman.py:136-139`) pode produzir silenciosamente rótulos errados — o modo de falha é um modelo pior, não uma exceção
- Prioridade: Alta para funções puras (conversão, resolução de caminhos), Média nos demais casos
- Dificuldade de teste: a ausência de um manifesto de dependências torna a configuração do ambiente de teste impossível hoje (corrija isso primeiro); o conversor, porém, é trivialmente testável com um fixture `odgt` pequeno e embutido

**Pipeline ponta a ponta (`run_pipeline.py`):**
- O que não é testado: a transição do estágio 1 → estágio 2, a geração do `data.yaml`, a resolução de fallback dos pesos
- Risco: a transição quebrada conhecida acima teria sido entregue sem detecção e recorreria após qualquer refatoração
- Prioridade: Alta
- Dificuldade de teste: precisa de um dataset simulado/pequeno (o download do CrowdHuman é grande demais para CI); um modo `--smoke` com um fixture de 10 imagens tornaria isso viável

**Regressão da qualidade do modelo:**
- O que não é testado: nenhum mAP de linha de base é registrado em lugar algum; `scripts/validate_body.py` nem consegue rodar no estado atual (ver Bugs Conhecidos)
- Risco: um modelo retreinado pior que `resultados/best.pt` é indistinguível de um que é melhor
- Prioridade: Média
- Dificuldade de teste: exige que o dataset de validação esteja presente; armazenar o último mAP conhecido ao lado de cada arquivo de pesos

**Demonstração por webcam (`main.py`):**
- O que não é testado: não há como rodar sem interface (sem entrada de arquivo de vídeo), então só pode ser verificado manualmente com uma câmera
- Risco: regressões na lógica de desenho/FPS só são encontradas por um humano observando a janela
- Prioridade: Baixa
- Dificuldade de teste: adicionar `--source path.mp4` e afirmar que o loop termina + grava um quadro

---

*Auditoria de preocupações: 2026-10-08*
*Atualize conforme os problemas forem corrigidos ou novos forem descobertos*
