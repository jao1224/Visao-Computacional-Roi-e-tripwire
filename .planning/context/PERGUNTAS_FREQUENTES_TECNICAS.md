# Perguntas Frequentes Técnicas — permanência e ByteTrack sob a LGPD

> Respostas curtas às duas dúvidas que mais aparecem na revisão do projeto.
> **O que vale hoje:** [`../REQUIREMENTS.md`](../REQUIREMENTS.md) · [`../ROADMAP.md`](../ROADMAP.md) ·
> parecer completo em [`PARECER_LGPD_E_MARCO_CIVIL.md`](PARECER_LGPD_E_MARCO_CIVIL.md) e
> [`../research/COMPLIANCE-LGPD-MARCO-CIVIL.md`](../research/COMPLIANCE-LGPD-MARCO-CIVIL.md).

---

## 1. Como o tempo de permanência é salvo

1. **RAM:** trilha entra na zona → `t_entrada` anotado em memória; sai → `duração = saída − entrada`. Trilha e timestamp morrem ali.
2. **Banco:** só o agregado por zona × janela de 1 min:

   | zona | janela | n_permanências | soma_segundos | média | histograma |
   |---|---|---|---|---|---|
   | Recepção | 14:02–14:03 | 9 | 4 320 | 8m00s | 0–2min: 4 · 2–5min: 3 · 5–15min: 2 |

3. **Nunca gravado:** "pessoa X ficou 12 min às 14h03" — essa linha não existe em lugar nenhum (banco, log, backup).
4. **Resultado:** a linha agregada é anônima irreversível (art. 12 caput) → a LGPD não se aplica ao conteúdo persistido.

> Schema correspondente: [`MODELAGEM_BANCO_DE_DADOS.md`](MODELAGEM_BANCO_DE_DADOS.md) §2.2
> (`dwell_agregado_zona`).

---

## 2. Como o ByteTrack se adequa à LGPD

- Durante a inferência, sim, há tratamento de dado pessoal (art. 5º I) → base legal = **art. 7º VII** (proteção da vida) + **art. 7º IX** (interesse legítimo, com LIA formal na Fase 9); consentimento não é usado (não é livre em monitoramento contínuo).
- ByteTrack é autorizado pelo princípio da **necessidade (art. 6º III)**: sem ele, a mesma pessoa é contada 2–3 vezes — ele é o mínimo indispensável para a finalidade "contar certo".
- Ele toca **só** posição de caixas + número temporário (sem rosto, biometria ou silhueta persistente), vive **segundos em RAM**, e sua saída são **agregados**.
- **Teste legal simples:** se, ao a pessoa sair do quadro, não sobra *nada* gravado dela, estamos na lei. Se sobra qualquer coisa rastreável → art. 12 §2º (infração) → é exatamente o que a auditoria da Fase 9 (PRV-01) varre por grep.

---

## 3. Por que isso é aceitável, em uma frase

> O que se persiste é **anônimo irreversível** (art. 12 caput). O que existe só durante a inferência é
> **efêmero, mínimo e necessário** (art. 6º III). Não existe uma terceira categoria neste sistema —
> e a auditoria automatizada (`tests/test_privacidade.py`) falha o build se uma aparecer.

---

_Extraído de `docs/PLANO_V1_COMPLETO.md` §5–§6 na consolidação de 2026-10-21._
