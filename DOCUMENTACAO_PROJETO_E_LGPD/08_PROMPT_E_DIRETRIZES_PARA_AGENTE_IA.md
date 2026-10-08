# 08. PROMPT E DIRETRIZES DE ENGENHARIA PARA AGENTES DE IA

> **⚠ Escopo vigente (2026-10-08):** em caso de conflito, o escopo do `../PLANO_V1_COMPLETO.md` prevalece: **sem face, sem catraca, sem MTMCT/Re-ID, sem `session_traces`/`sessoes`, sem rastreio por silhueta** — apenas detecção de corpo, ByteTrack intra-câmera em RAM e saída agregada. Ver aviso no `README.md` desta pasta.

> **Atenção Agente de IA:**  
> Ao gerar código, propor melhorias, criar testes ou refatorar o sistema deste repositório, você **DEVE seguir estritamente as diretrizes abaixo**.

---

## 1. Regras Mandatórias de Engenharia

1. **Priorize a Performance de Vídeo em Tempo Real:**
   - As inferências de IA devem manter latência $\le 5\text{ ms}$ por frame em GPU.
   - Utilize processamento assíncrono e evite operações bloqueantes de I/O de disco ou banco de dados dentro do loop de captura de vídeo (`cv2.VideoCapture` / RTSP).
2. **Separação Rígida de Responsabilidades:**
   - **Módulo de Visão:** Captura frames, detecta objetos via YOLO e executa tracking local (ByteTrack).
   - **Módulo de Fila:** Agrupa eventos de entrada/saída em memória RAM e dispara batches para o banco de dados.
   - **Módulo de Backend:** FastAPI expõe rotas para dashboards e armazena logs de acesso por 6 meses (Marco Civil).

---

## 2. Regras Rígidas de Privacidade e LGPD (Privacy by Design)

- ❌ **NUNCA proponha salvar fotos de rostos (crops/snapshots) ou extrair vetores biométricos para fins de analytics geral.**
- ✅ **SEMPRE utilize detecção de corpo humano/silhueta (`yolo_crowdhuman_body`) para métricas de contagem, ocupação e tempo de permanência.**
- ❌ **Controle de acesso individual (catracas/portas), face e `session_id`/qualquer identificador associado a um indivíduo: NUNCA implemente.** Proibido para sempre (LGPD art. 11 e art. 12 §2º; decisão do usuário). Não existe schema por-pessoa neste projeto — nem temporário, nem com TTL. Métricas são exclusivamente agregadas.
- ✅ **Logs de API:** Garanta que os endpoints registrem IP, porta e timestamp com rotina de retenção de 180 dias.

---

## 3. Comandos Úteis do Projeto

```bash
# 1. Instalar dependências completas
pip install -r requirements.txt

# 2. Executar detecção facial em tempo real (Webcam)
python yolo-face-detection/main.py

# 3. Executar detecção corporal (CrowdHuman)
python yolo_crowdhuman_body/main.py

# 4. Sincronizar e criar tabelas no PostgreSQL
python yolo-face-detection/DB_postigres.py
```
