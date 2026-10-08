# Detecção de Corpo Inteiro com YOLO e CrowdHuman

Projeto dedicado ao treinamento e inferência de modelos YOLO especializados na **Detecção de Corpo Inteiro (Pedestres / Pessoas)** utilizando o dataset **CrowdHuman**.

Esta pasta é **100% independente** da pasta de detecção de rostos, garantindo total isolamento de pesos, métricas e datasets.

---

## 📁 Estrutura da Pasta

```text
yolo_crowdhuman_body/
│
├── main.py                     --> Teste em tempo real na webcam (detecção de corpo)
├── data.yaml                   --> Configuração do dataset (classe: person)
├── README.md                   --> Este guia passo a passo
│
├── scripts/                    --> Utilitários do pipeline
│   ├── download_and_convert_crowdhuman.py --> Download e conversão do CrowdHuman (.odgt -> YOLO .txt)
│   ├── train_body.py           --> Script de treinamento do YOLOv26 para corpo
│   └── validate_body.py        --> Validação formal no split de teste do CrowdHuman
│
├── dataset/                    --> Pasta de imagens e anotações do CrowdHuman
│   ├── images/ (train / val)
│   └── labels/ (train / val)
│
└── runs/                       --> Pesos e resultados dos treinamentos de corpo
    └── detect/
        └── train_crowdhuman_body/
            ├── weights/best.pt
            └── results.csv
```

---

## 🚀 Como Usar

### Passo 1: Baixar e Converter o Dataset CrowdHuman
Para baixar e converter as anotações automaticamente para o padrão YOLO:
```bash
python scripts/download_and_convert_crowdhuman.py
```
*(Alternativa: Você pode baixar manualmente os arquivos pelo site [crowdhuman.org](https://www.crowdhuman.org/) ou Roboflow Universe).*

---

### Passo 2: Iniciar o Treinamento do Modelo de Corpo
Para iniciar o fine-tuning do YOLOv26 com foco em corpos humanos:
```bash
python scripts/train_body.py
```

* **Resolução (`imgsz`):** `640x640` (Ideal para capturar a anatomia completa da cabeça aos pés).
* **Batch:** `8`
* **Épocas:** `300` com *cosine learning rate decay*.

---

### Passo 3: Avaliar as Métricas do Modelo
```bash
python scripts/validate_body.py
```

---

### Passo 4: Testar na Webcam em Tempo Real
```bash
python main.py
```
*(Pressione **`q`** para encerrar).*
