# Pontos de Atenção para a Equipe

> Lista curta de coisas que costumam travar o projeto se esquecidas. Complementa — não substitui —
> os critérios de sucesso de cada fase, que são canônicos em [`../ROADMAP.md`](../ROADMAP.md).

| # | Ponto | Por quê importa |
|---|---|---|
| 1 | **RTSP real só na Fase 6** — enquanto não há DVRs, desenvolve-se com webcam, vídeos-amostra e MediaMTX (servidor RTSP local de teste). | Evita bloqueio esperando infraestrutura que o hotel ainda não tem. |
| 2 | **Validação em hotel real fica para depois** dos streams reais (a Fase 8 documenta a limitação). | Impede de vender uma acurácia que ainda não foi medida em campo. |
| 3 | **A Fase 9 é gate:** nada vai a produção sem auditoria de código + RIPD/LIA/ROPA + aviso + encarregado + plano de incidente. | Obrigação legal inegociável (art. 5º XVII, art. 10 §3, art. 37, art. 41, art. 48). |
| 4 | **Proibido para sempre** (não é "para depois"): face, MTMCT/Re-ID (inclusive por silhueta), `session_traces`/`sessoes`, embeddings, trilha individual, gravação de vídeo. | LGPD art. 11 e art. 12 §2º — ver [`../historico/`](../historico/) para o registro do descarte. |
| 5 | **Stack real (implementada hoje):** Python 3.14.4 (venv `.venv/`) · `ultralytics==8.4.121` (YOLO + ByteTrack) · `opencv-python==5.0.0.93` · `numpy==2.5.2` · `lap==0.5.13` · `pyyaml==6.0.3` · `pytest>=8.0` (dev). | Fonte: `requirements.txt` / `requirements-dev.txt`; mapa detalhado em [`../codebase/STACK.md`](../codebase/STACK.md). |
| 6 | **Stack-alvo (Fases 3–7, planejada — não implementada):** PyAV (ingestão RTSP — OpenCV corrompe frames RTSP após 15–35 s) · MediaMTX (RTSP local de teste) · PostgreSQL 18 + `asyncpg` · FastAPI + WebSocket · React + Vite + ECharts · docker-compose. | Nada disso está instalado: usar exatamente o que está em `requirements.txt` até a fase correspondente. |
| 7 | **Relatório de conformidade para a gestão:** PDF em `docs/relatorios/` (gerado por `scripts/gerar_relatorio_lgpd.py`, dependência opcional `reportlab` fora do `requirements.txt` do produto). | É o entregável formal para a gestão e para o encarregado. |

---

_Extraído de `docs/PLANO_V1_COMPLETO.md` §8 na consolidação de 2026-10-21._
