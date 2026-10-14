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
├── main.py                 --> Orquestração: captura → rastreio → zonas → overlay
├── captura.py              --> Fonte (webcam/arquivo/RTSP) + capture_ts
├── rastreio.py             --> YOLO + ByteTrack efêmero (classe 0 = corpo)
├── overlay.py              --> Caixas, HUD, tripwires, ROIs, contadores in-place
├── zona.py                 --> Ocupação ROI (tripwire bidirecional opcional) + reset/reconciliação
├── config/
│   ├── data.yaml           --> Dataset (classe: person)
│   └── zonas.yaml          --> Zonas por camera_id (tripwire + ROI + capacidade)
├── models/                 --> Pesos base (yolo26n.pt)
├── resultados/best.pt      --> Detector de corpo treinado (CrowdHuman)
├── scripts/                --> Download CrowdHuman, treino, validação, pipeline
├── tests/                  --> Privacidade, integração, zonas, contratos
└── docs/                   --> LGPD, arquitetura, plano v1
```

---

## Funcionalidades (Fase 1 + 2)

| Módulo | O que faz |
|--------|-----------|
| **Detecção + Rastreio** | YOLO corpo + ByteTrack em RAM, IDs efêmeros |
| **Tripwire (opcional)** | Linha bidirecional (ENTROU/SAIU) com debounce 3 frames + hysteresis 15px — suporte mantido, desabilitado no padrão atual |
| **Ocupação ROI** | Recontagem geométrica frame-a-frame (bottom-center no polígono) |
| **Resets** | Meia-noite local OU vazio > 10 min → zera contadores + limpa `crossed` |
| **Reconciliação** | Reabertura de fonte limpa `track_states` inteiro |
| **Overlay** | Tripwires (verde/vermelho), ROIs (azul alpha 0.2), cards IN/OUT/OCUP |
| **Privacidade** | Zero escrita em disco, zero biometria, auditoria automatizada |

---

## Como usar

### Inferência em tempo real (webcam ou vídeo)

```bash
python main.py                    # webcam padrão (índice 0)
python main.py 1                  # índice da câmera
python main.py caminho/video.mp4  # arquivo de vídeo
```

Pressione **`q`** para encerrar.

**Configuração de zonas:** edite `config/zonas.yaml` (camera_0, ROI y=200..480, capacidade 50). O formato tripwire também é suportado, caso deseje adicioná-lo.

### Testes

```bash
python -m pytest tests/ -q        # suite completa (35 testes)
python -m pytest tests/test_zona.py -q   # 13 testes de zonas
```

### Visualizar zonas (sem rodar vídeo)

```bash
python entender_zonas.py          # gera zonas_visualizacao.png
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
