# Histórico — documentos superados

> Esta pasta guarda **registros históricos** de escopos que o projeto **descartou de forma
> definitiva**. Nada aqui deve ser implementado, copiado ou usado como referência de projeto.
> Os banners `SUPERADO` no topo de cada documento são intencionais e permanent.

> **⚠ O que vale hoje:**
> - O que cada fase é e seu estado: [`../ROADMAP.md`](../ROADMAP.md) · [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · [`../STATE.md`](../STATE.md)
> - Contexto vivo (negócio, arquitetura, plantas, banco, parecer, diretrizes): [`../context/`](../context/)

---

## 📦 Arquivos

| Arquivo | Assunto | Motivo do descarte | Base legal |
| :--- | :--- | :--- | :--- |
| [`04_MODELOS_IA_FACE_VS_BODY.md`](04_MODELOS_IA_FACE_VS_BODY.md) | Comparativo YOLO Face (WiderFace) × YOLO Body (CrowdHuman). | O escopo do projeto passou a ser **apenas detecção de corpo**. Face/reconhecimento/biometria são **fora do escopo para sempre**. | LGPD art. 11 (dado sensível sem base legal para analytics) + decisão do usuário (2026-10-08) |
| [`05_RASTREAMENTO_MULTICAMERAS_MTMCT.md`](05_RASTREAMENTO_MULTICAMERAS_MTMCT.md) | Arquitetura de MTMCT / Re-ID / fusão de trilhas entre câmeras. | Reconstruir a rota de um indivíduo = **perfil comportamental**. Cada câmera tem seu próprio tracker; "câmera 2 nunca pode reconhecer alguém da câmera 1, nem por silhueta". | LGPD art. 12 §2º + ordem explícita do usuário |

---

## Por que manter em vez de apagar

1. **Auditabilidade** — o parecer regulatório e as decisões do projeto citam esses documentos como
   base da análise de risco; o rastro precisa continuar verificável.
2. **Rastreabilidade da mudança de escopo** — quem ler o repositório precisa ver *o que* foi
   descartado e *por quê*, não apenas o que sobrou.
3. **Prevenção de recaída** — o padrão "voltar a implementar MTMCT porque o documento antigo
   ainda existe" é exatamente o que estes arquivos registram.

> **Reinstalação proibida:** qualquer proposta de reativar face, biometria, MTMCT/Re-ID,
> `sessoes`/`session_traces`, track_id persistido, embeddings, rota/jornada, heatmap por
> indivíduo ou gravação de vídeo é **incompatível** com o escopo vigente e deve ser recusada.
