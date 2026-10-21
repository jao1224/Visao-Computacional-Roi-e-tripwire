# Relatórios de conformidade e documentação executiva

Esta pasta reúne os documentos de entrega e de auditoria apresentados à gestão de projeto e ao
encarregado (DPO) do hotel.

## Conteúdo

| Documento | Data | Descrição |
|-----------|------|-----------|
| **`RELATORIO-CONFORMIDADE-LGPD-v1.2-2026-10-21.pdf`** | 21/10/2026 | **Versão vigente.** Relatório técnico-jurídico de conformidade com a LGPD (Lei nº 13.709/2018) e o Marco Civil da Internet (Lei nº 12.965/2014). Cobre: o que já foi implementado (Fases 1 e 2), o que será implementado (Fases 3 a 9), a matriz de conformidade artigo a artigo, as lacunas de conformidade antes de produção e as recomendações ao gestor de projeto. **26 páginas.** Diferença para a v1.1: todos os caminhos de documentação apontam para o planejamento canônico (`.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/context/`, `.planning/historico/`) e a "nota de consistência documental" descreve a consolidação da documentação em um único planejamento. |
| `RELATORIO-CONFORMIDADE-LGPD-v1.1-2026-10-21.pdf` | 21/10/2026 | Versão anterior, mantida como registro histórico. 26 páginas. Diferença para a v1.2: citava os caminhos antigos de `docs/` (`docs/PLANO_V1_COMPLETO.md` e `docs/DOCUMENTACAO_PROJETO_E_LGPD/`), que foram dissolvidos na consolidação de 2026-10-21. |
| `RELATORIO-CONFORMIDADE-LGPD-v1.0-2026-10-21.pdf` | 21/10/2026 | Versão anterior, mantida como registro histórico. 24 páginas. Diferença para a v1.1: nova seção **5.7 — "Como o sistema garante a não-identificação na prática"** (ciclo de vida de uma pessoa no enquadramento, exemplo concreto do que a Fase 7 persiste sobre um dwell, e o teste legal do ByteTrack), stack-alvo no Anexo E e contagem de commits agora apurada no momento da geração. |

## Fontes do relatório

Todo o conteúdo do PDF é derivado de artefatos versionados no repositório — nenhuma afirmação é
declarativa sem evidência:

| Fonte | Uso no relatório |
|-------|-------------------|
| `.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md` | Verificação legal artigo a artigo (base das seções 2 e 6) |
| `.planning/REQUIREMENTS.md` | Escopo v1 (27 requisitos), rastreabilidade e exclusões explícitas |
| `.planning/ROADMAP.md` | Fases 1 a 9, metas, dependências e critérios de sucesso |
| `.planning/phases/01-*/`, `.planning/phases/02-*/` | Planos, resumos e contrato de validação das fases concluídas |
| `.planning/STATE.md` | Estado do projeto e progresso |
| `.planning/debug/` | Diagnóstico e plano de correção do filtro visual por ROI |
| `.planning/codebase/` | Mapa do código: arquitetura, stack, estrutura, testes, riscos, convenções |
| `.planning/context/` | Contexto do projeto: negócio, arquitetura, plantas/câmeras, modelagem do banco, parecer LGPD e diretrizes |
| `.planning/research/README.md` | Índice da pesquisa datada de 2026-10-08: o que nela é válido e o que está superado |
| `.planning/historico/` | Escopos superados (face-vs-body, MTMCT), com o motivo do descarte e a base legal |
| Suíte de testes (`tests/`) | Evidência automatizada das garantias de privacidade (33 testes) |
| `git log` | Evidência de processo: commits atômicos (contagem apurada na geração) |

> **Nota de contagem (v1.1):** a partir da v1.1 o número de commits citado no PDF é lido
> diretamente do repositório no momento da geração (`git rev-list --count HEAD`), eliminando a
> defasagem entre o snapshot e a publicação. Na v1.0 o número era fixo (81) e refletia o
> repositório imediatamente antes da publicação do próprio relatório. Os demais indicadores
> (33 testes, 608 linhas de código de produto, 2 de 9 fases, 6 de 27 requisitos) refletem o
> estado do código e não mudam.

## Como regenerar

O relatório é gerado por `scripts/gerar_relatorio_lgpd.py` — ferramenta de documentação, **fora do
pipeline de produção** (não importa nenhum módulo do produto, não lê nem grava mídia).

```bash
python3 -m venv .venv-relatorio
./.venv-relatorio/bin/pip install reportlab
./.venv-relatorio/bin/python scripts/gerar_relatorio_lgpd.py
```

Saída: `docs/relatorios/RELATORIO-CONFORMIDADE-LGPD-v<versão>-<AAAA-MM-DD>.pdf`.

> **Nota de privacidade:** o gerador apenas lê arquivos de texto do repositório e escreve um PDF.
> `reportlab` é uma dependência **opcional** de geração de documentação e não consta em
> `requirements.txt` do produto.

## Nota sobre versões

O relatório é um **snapshot**. Ao reexecutar o gerador após novas fases:

1. Atualize `VERSAO` e o campo "Versão" da capa em `scripts/gerar_relatorio_lgpd.py`.
2. Renumere as tabelas adicionadas (as legendas "Tabela N" são sequenciais e referenciadas no texto).
3. Reavalie a matriz de conformidade da seção 6 e as lacunas da seção 7 a cada avanço de fase.
4. Publique o PDF nesta pasta e acrescente a linha correspondente à tabela "Conteúdo" acima.
