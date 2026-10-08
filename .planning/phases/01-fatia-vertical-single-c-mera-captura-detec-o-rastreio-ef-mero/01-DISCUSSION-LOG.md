# Phase 1: Fatia vertical single-câmera (captura, detecção, rastreio efêmero) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-08
**Phase:** 1-fatia-vertical-single-c-mera-captura-detec-o-rastreio-ef-mero
**Areas discussed:** Estrutura do Código

---

## Estrutura do Código

### Seleção de áreas (multiSelect)

| Área | Descrição | Selecionada |
|------|-----------|-------------|
| Estrutura do código | Extrair módulos novos (captura, rastreio) mantendo main.py como entrada | ✓ |
| Fonte de vídeo | Como escolher webcam vs arquivo de vídeo (flag CLI, auto-detectar) | |
| Visualização (overlay) | O que aparece na janela além das caixas (IDs, contagem, FPS, aviso LGPD) | |
| Prova de "nada em disco" | Script automatizado vs inspeção manual (critério de sucesso 2) | |

**User's choice:** Apenas "Estrutura do código"
**Notes:** Áreas de fonte de vídeo, overlay e prova de nada-em-disco ficam a critério do planner/researcher (the agent's Discretion).

---

### Q1 — Como organizar o código da Fase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| Módulos planos na raiz (Recomendado) | Arquivos `captura.py`, `rastreio.py`, `overlay.py` na raiz, importados pelo main.py — sem pacote/__init__.py, seguindo convenção atual de scripts autônomos | ✓ |
| Pacote pipeline/ | Criar `pipeline/` com __init__.py e submódulos — mais organizado para fases futuras, mas quebra convenção de "sem pacotes" | |
| Tudo dentro do main.py | Adicionar como seções do main.py — mantém main() longo atual, mas arquivo cresce rápido | |

**User's choice:** Módulos planos na raiz

---

### Q2 — Em que idioma nomear os módulos novos na raiz?

| Option | Description | Selected |
|--------|-------------|----------|
| Português (Recomendado) | captura.py, rastreio.py, overlay.py — combina com raiz/treinar_crowdhuman.py e domínio pt-BR | ✓ |
| Inglês | capture.py, tracker.py, overlay.py — combina com scripts/ e termos técnicos | |

**User's choice:** Português

---

### Q3 — A Fase 1 deve criar um requirements.txt?

| Option | Description | Selected |
|--------|-------------|----------|
| Criar requirements.txt (Recomendado) | Mínimo (ultralytics, opencv-python, numpy…) — hoje não existe nenhum lock/requirements, risco de reprodutibilidade | ✓ |
| Não criar agora | Manter dependências implícitas nos imports, como hoje | |

**User's choice:** Criar requirements.txt

---

### Q4 — Como os módulos se conectam ao main.py?

| Option | Description | Selected |
|--------|-------------|----------|
| Funções simples (Recomendado) | main.py mantém o while e chama módulos como funções (capturar(), rastrear(), desenhar()) — simples, testável, sem classes | ✓ |
| Classe Pipeline | Classe que encapsula câmera, modelo e tracker — mais organizado, mais pesado para fatia vertical | |
| Você decide | Escolher a melhor abordagem tecnicamente | |

**User's choice:** Funções simples

---

### Q5 — Onde o pipeline deve registrar sua execução?

| Option | Description | Selected |
|--------|-------------|----------|
| Só console (Recomendado) | print com tags [OK]/[Aviso] como o resto do repo — sem arquivo de log, zero risco de log por-pessoa em disco | ✓ |
| Console + arquivo .log | Console + pipeline.log com eventos de execução (sem dados por-pessoa) | |

**User's choice:** Só console

---

## the agent's Discretion

- Assinatura/parâmetros das funções de cada módulo
- Integração do ByteTrack (ex.: `model.track(persist=True)`)
- Formato dos dados entre módulos
- Valores de conf/iou/FPS alvo
- Estratégia de teste manual com vídeo-amostra
- Conteúdo/versões do requirements.txt
- Áreas não selecionadas: fonte de vídeo, overlay, prova de nada-em-disco

## Deferred Ideas

Nenhuma — discussão permaneceu no escopo da fase.
