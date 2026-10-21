# 08. PROMPT E DIRETRIZES DE ENGENHARIA PARA AGENTES DE IA

> **⚠ Escopo vigente (2026-10-21):** em caso de conflito, o escopo do `../PLANO_V1_COMPLETO.md` prevalece: **sem face, sem catraca, sem MTMCT/Re-ID, sem `session_traces`/`sessoes`, sem rastreio por silhueta** — apenas detecção de corpo, ByteTrack intra-câmera em RAM e saída agregada. Ver aviso no `README.md` desta pasta.
>
> Documento normativo vivo. Última atualização: **2026-10-21**.

> **Atenção Agente de IA:**
> Ao gerar código, propor melhorias, criar testes ou refatorar o sistema deste repositório, você **DEVE seguir estritamente as diretrizes abaixo**.

---

## 1. Regras Mandatórias de Engenharia

1. **Priorize a Performance de Vídeo em Tempo Real:**
   - As inferências de IA devem manter latência $\le 5\text{ ms}$ por frame em GPU.
   - Utilize processamento assíncrono e evite operações bloqueantes de I/O de disco ou banco de dados dentro do loop de captura de vídeo (`cv2.VideoCapture` / RTSP).
2. **Separação Rígida de Responsabilidades:**
   - **Módulo de Visão:** captura frames, detecta objetos via YOLO e executa tracking local (ByteTrack).
   - **Módulo de Zonas:** calcula ocupação por ROI e interseção de área — recarrega `config/zonas.yaml`, **sem I/O no loop** além da leitura única no arranque.
   - **Módulo de Fila (futuro):** agrupa eventos agregados de ocupação em memória RAM e dispara batches para o banco de dados.
   - **Módulo de Backend (futuro):** FastAPI expõe rotas para dashboards e armazena logs de acesso por 6 meses (Marco Civil).
3. **Escopo funcional atual — ROI/ocupação por área:**
   - O foco do produto é **ocupação por zona ROI** (número de pessoas e % de área ocupada), com **interseção de área** `Área(Objeto) ∩ Área(ROI)`.
   - O **tripwire bidirecional está desativado** (código comentado em `zona.py`, `overlay.py` e `main.py`). Não o reative sem pedido explícito do usuário.
4. **Idioma e convenções:** código, funções, mensagens e docstrings em **português (pt-BR)**; nomes de arquivo em `snake_case`; dependências **pinadas** com `==` em `requirements.txt`.

---

## 2. Regras Rígidas de Privacidade e LGPD (Privacy by Design)

- ❌ **NUNCA proponha salvar fotos de rostos (crops/snapshots) ou extrair vetores biométricos para fins de analytics geral.**
- ❌ **NUNCA sugira gravar frames, imagens ou vídeo em disco** — nem em logs, backups, dumps de erro ou "para depurar". O frame é volátil.
- ❌ **NUNCA proponha rastreamento entre câmeras (MTMCT/Re-ID), por ID, por silhueta ou por aparência.** Cada câmera tem seu próprio tracker; a comparação entre câmeras é infração do art. 12 §2º.
- ❌ **NUNCA persista** `track_id`, `session_id`, trilha, rota, jornada, embedding, heatmap por indivíduo, ou qualquer linha por pessoa — nem "só para testes".
- ✅ **SEMPRE utilize detecção de corpo humano/silhueta** (`yolo_crowdhuman_body`) para métricas de contagem, ocupação e tempo de permanência.
- ❌ **Controle de acesso individual (catracas/portas), face e `session_id`/qualquer identificador associado a um indivíduo: NUNCA implemente.** Proibido para sempre (LGPD art. 11 e art. 12 §2º; decisão do usuário). Não existe schema por-pessoa neste projeto — nem temporário, nem com TTL. Métricas são exclusivamente agregadas.
- ✅ **Logs de API:** endpoints registram IP, data/hora e ação, com rotina de retenção de **6 meses** sob sigilo (Marco Civil art. 15).
- ✅ **Auditoria automatizada:** `tests/test_privacidade.py` falha se houver face, biometria ou escrita em disco — **não desabilite esses testes**.

---

## 3. Comandos Úteis do Projeto

```bash
# 0. Ambiente (venv do repositório — usar sempre este interpretador)
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements-dev.txt

# 1. Rodar o pipeline (webcam índice 0, outra câmera, ou arquivo de vídeo)
./.venv/bin/python main.py
./.venv/bin/python main.py 1
./.venv/bin/python main.py caminho/video.mp4

# 2. Suíte de testes (33 testes)
./.venv/bin/python -m pytest

# 3. Demarcar ROI interativamente (utilitário de DESENVOLVIMENTO — fora do pipeline)
./.venv/bin/python scripts/demarcar_zona.py 0 --camera camera_0 --zona hall

# 4. Visualizar as zonas do YAML sem rodar vídeo
./.venv/bin/python entender_zonas.py

# 5. Treinar / validar o detector de corpo
./.venv/bin/python scripts/download_and_convert_crowdhuman.py
./.venv/bin/python scripts/train_body.py
./.venv/bin/python scripts/validate_body.py
```

> ❌ **Não existem** `yolo-face-detection/`, `yolo-crowdhuman_body/` nem `DB_postgres.py` neste repositório — comandos que os mencionem estão **obsoletos**.

---

## 4. Onde o agente deve olhar primeiro

| Necesidade | Arquivo |
|---|---|
| Escopo e plano vigente | `docs/PLANO_V1_COMPLETO.md` |
| Fases detalhadas e status | `docs/DOCUMENTACAO_PROJETO_E_LGPD/09_PLANO_DE_FASES_V1.md` |
| Roadmap e rastreabilidade | `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` |
| Mapa do código | `.planning/codebase/` |
| Verificação legal (11 condições vinculantes) | `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` |
| Relatório para a gestão | `docs/relatorios/` |
