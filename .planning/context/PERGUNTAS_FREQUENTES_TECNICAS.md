# Perguntas Frequentes Técnicas — permanência e ByteTrack sob a LGPD

> Respostas curtas às dúvidas mais frequentes na revisão do projeto.
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

## 3. Como é feito o cálculo de ocupação por zona?

O cálculo é feito em **duas camadas complementares** em `zona.py` (`atualizar_ocupacao()` + `calcular_intersecao_area_roi()`).

### 3.1 Contagem de pessoas (`estado[zona_id]['ocupacao']`) — por ponto/âncora

1. **Âncora:** Usa o **centro-inferior da bounding box** (`_bottom_center(xyxy) = ((x1+x2)/2.0, y2)`) como aproximação do **pé no chão**. Em perspectiva, isso é mais fiel ao contato real com o chão do que usar o centro da caixa inteira.
2. **Teste geométrico:** Para cada pessoa, testa se a âncora está dentro ou na borda do polígono com `cv2.pointPolygonTest(roi, ponto, False) >= 0`. Primeiro tenta o **pé**; se não bater, tenta o **centro geométrico** da bbox. Há ainda um *fallback* para pessoas cortadas pela borda inferior da imagem (verifica cantos superiores da bbox).
3. **Contagem e clamp:** `bruta` = número de pessoas que passaram no teste. Depois aplica-se `est_z['ocupacao'] = max(0, min(bruta, capacidade))`, onde `capacidade` vem de `config/zonas.yaml`. É um valor **inteiro** e cada *track* conta no máximo 1 vez por frame.

### 3.2 Ocupação por área (`estado[zona_id]['pct_area']`) — por interseção pixel-a-pixel

O objetivo é responder: *"Que porcentagem do polígono do ROI está coberta pela área ocupada pelas pessoas?"* 

1. **Máscara do ROI:** Cria uma matriz do mesmo tamanho do frame (`np.zeros`) e preenche o polígono com `cv2.fillPoly(roi_mask, [roi_pts], 1)`. `area_roi_px` = total de pixels do ROI.
2. **Máscara das pessoas:** Por padrão (`modo='base'`), **não** usa a bbox inteira. Usa apenas o **terço inferior** da bounding box (`y_base = y2 - int(altura_box * 0.35)`) preenchido com `cv2.rectangle(pessoas_mask, (x1, y_base), (x2, y2), 1, -1)`. Isso aproxima melhor a "área de apoio no chão" e reduz superestimação por perspectiva/pose. Se `modo != 'base'`, usa a **bbox inteira**.
3. **Interseção:** `intersecao = np.logical_and(pessoas_mask, roi_mask).astype(np.uint8)`. `pct_area = 100.0 * (area_ocupada_px / area_roi_px)`.

**Diferença prática:** `ocupacao` = "quantas pessoas" (baseado em ponto/âncora). `pct_area` = "quanto espaço está coberto" (baseado em máscaras pixel-a-pixel). Eles podem divergir (ex.: 2 pessoas juntas podem dar `ocupacao=2` e `pct_area` próximo de 90%).

---

## 4. O que acontece se o polígono da zona mudar?

**Não existe cache da geometria.** Tanto `cv2.pointPolygonTest` quanto `cv2.fillPoly` usam os pontos recebidos **a cada frame**.

| Cenário | Comportamento |
| --- | --- |
| **Alterar `config/zonas.yaml` no disco enquanto o programa roda** | **Sem efeito imediato.** `carregar_zonas()` só é chamado na inicialização. `atualizar_ocupacao()` não relê o arquivo. |
| **Recarregar e repassar nova lista `zonas` para `atualizar_ocupacao()`** | **Passa a valer no próximo frame.** Se `main.py` chamar `carregar_zonas()` novamente e passar a lista atualizada, a nova geometria será usada imediatamente. |
| **Mutar o dict/lista em memória (`zonas[0]['pontos'] = [...]`)** | **Passa a valer no próximo frame.** Os objetos são lidos diretamente, sem cópia congelada. |
| **Manter o mesmo `zona_id` mas mudar a forma** | Os contadores (`ocupacao`, `entradas`, `saidas`, `pct_area`) **permanecem** em `estado[zid]`. A definição "dentro/fora" muda na hora e pode gerar saltos bruscos de contagem. |
| **Trocar o `zona_id`** | Tratado como **zona completamente nova**. Os contadores começam do zero e não herdam histórico da zona anterior. |
| **Mudar resolução da câmera** | Os pontos estão em **coordenadas de pixel** da imagem atual. Se a resolução mudar sem ajustar os pontos no YAML, o cálculo ficará distorcido. |

> **Regra prática:** A geometria é avaliada *on-the-fly*. O que persiste entre frames são apenas os **contadores** em `estado[zid]`, nunca a forma antiga do polígono.

---

## 5. Por que isso é aceitável, em uma frase

> O que se persiste é **anônimo irreversível** (art. 12 caput). O que existe só durante a inferência é
> **efêmero, mínimo e necessário** (art. 6º III). Não existe uma terceira categoria neste sistema —
> e a auditoria automatizada (`tests/test_privacidade.py`) falha o build se uma aparecer.

---

_Extraído de `docs/PLANO_V1_COMPLETO.md` §5–§6 na consolidação de 2026-10-21._
