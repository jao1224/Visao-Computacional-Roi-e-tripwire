---
id: SEED-261015-demarcador-zonas-roi
status: dormant
planted: 2026-10-15
planted_during: v1.0 / Fase 2 refinamentos
trigger_when: "utilitário local de desenvolvimento; preparação para Fase 5 (Dashboard CRUD de zonas)"
scope: small
tags: [dev-tool, calibration, roi, opencv, visual]
---

# SEED-261015-demarcador-zonas-roi: Demarcador Interativo de Zonas ROI por Clique

## Contexto & Motivação
A definição atual de zonas ROI em `config/zonas.yaml` exige digitação manual de coordenadas `(x, y)` em pixels (`[[x1, y1], [x2, y2], ...]`), o que é contraproducente e sujeito a erros em câmeras e ambientes reais.

O usuário necessita de um demarcador visual simples e interativo para traçar polígonos sobre o frame da câmera/webcam/vídeo com cliques do mouse, gerando ou atualizando a configuração sem edição manual de números.

## Restrições & Isolamento
- **Não deve subir para o pipeline principal do produto:** Deve residir como script utilitário de suporte local (`scripts/demarcar_zona.py`), sem alterar a inferência limpa do `main.py` nem afetar a conformidade de testes ou build de produção.
- **Formato compatível:** Deve salvar as coordenadas respeitando estritamente o schema exigido por `zona.carregar_zonas` em `config/zonas.yaml`.

## Design do Utilitário (`scripts/demarcar_zona.py`)
1. **Entrada de vídeo:** Suporta índice de webcam (padrão `0`) ou caminho de vídeo/stream.
2. **Interação com OpenCV (`cv2.setMouseCallback`):**
   - **Clique com Botão Esquerdo:** Adiciona vértice ao polígono do ROI e desenha linhas temporárias.
   - **Clique e Arraste nos círculos verdes:** Reposiciona/edita qualquer vértice existente sem recomeçar.
   - **Tecla 'a':** Alinhamento automático ortogonal (endireita retas horizontais/verticais).
   - **Tecla 'r':** Converte os pontos marcados em um retângulo perfeito (bounding box).
   - **Tecla 'u':** Desfaz o último ponto inserido.
   - **Tecla 'c':** Limpa pontos e recomeça a demarcação.
   - **Tecla 's':** Fecha o polígono e salva diretamente em `config/zonas.yaml` preservando a estrutura de câmera e capacidade.
   - **Tecla 'q' ou ESC:** Sai sem salvar.
   - **Cabeçalho HUD:** Painel superior persistente com a legenda de todos os atalhos e status visual.
3. **Privacidade (LGPD):** O script não grava fotos, vídeos nem frames em disco — grava apenas o arquivo de texto `config/zonas.yaml`.
