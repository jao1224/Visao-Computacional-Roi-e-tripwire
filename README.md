# YOLO + LGPD — Visão Computacional para Hotelaria

**Identificação do projeto:** `YOLO + LGPD`  
Detecção de **corpo/silhueta** com YOLO (CrowdHuman) para analytics de fluxo — **zero biometria**, em conformidade com a LGPD.

Sistema que transforma câmeras do hotel em sensores de negócio: contagem, ocupação e (nas próximas fases) permanência por zona. Frames não são gravados; IDs do ByteTrack existem só em RAM.

---

## Recorte LGPD (obrigatório)

- Só detecção de corpo — sem face, Re-ID, embedding ou identificação nominal
- Frames voláteis: inferência em memória, sem `imwrite` / gravação de vídeo de pessoas
- Saída apenas agregada (contagens); nenhum `track_id` persistido
- Dependência `opencv-python` (não `opencv-contrib-python`, para não puxar `cv2.face`)

Documentação legal e de produto: `docs/DOCUMENTACAO_PROJETO_E_LGPD/`.

---

## Estrutura

```text
yolo-lgpd/
├── main.py                 --> Webcam / vídeo: captura → rastreio → overlay
├── captura.py
├── rastreio.py             --> YOLO + ByteTrack efêmero (classe 0 = corpo)
├── overlay.py              --> Caixas e HUD in-place, sem escrita em disco
├── config/data.yaml        --> Dataset (classe: person)
├── models/                 --> Pesos base (yolo26n.pt)
├── resultados/best.pt      --> Detector de corpo treinado
├── scripts/                --> Download CrowdHuman, treino, validação, pipeline
├── tests/                  --> Privacidade, integração e contratos dos módulos
└── docs/                   --> LGPD, arquitetura, plano v1
```

---

## Como usar

### Inferência em tempo real (webcam)

```bash
python main.py
```

Fonte alternativa: `python main.py 1` (índice da câmera) ou `python main.py caminho/do/video.mp4`.  
Pressione **`q`** para encerrar.

### Testes

```bash
python -m pytest tests/ -q
```

### Treinar / validar o detector de corpo

```bash
python scripts/download_and_convert_crowdhuman.py
python scripts/train_body.py
python scripts/validate_body.py
```

* **Resolução (`imgsz`):** `640x640`
* **Batch:** `8`
* **Épocas:** `300` com *cosine learning rate decay*
