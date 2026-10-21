# Relatórios de conformidade e documentação executiva

Esta pasta reúne os documentos de entrega e de auditoria apresentados à gestão de projeto e ao
encarregado (DPO) do hotel.

## Conteúdo

| Documento | Data | Descrição |
|-----------|------|-----------|
| `RELATORIO-CONFORMIDADE-LGPD-v1.0-2026-10-21.pdf` | 21/10/2026 | Relatório técnico-jurídico de conformidade com a LGPD (Lei nº 13.709/2018) e o Marco Civil da Internet (Lei nº 12.965/2014). Cobre: o que já foi implementado (Fases 1 e 2), o que será implementado (Fases 3 a 9), a matriz de conformidade artigo a artigo, as lacunas de conformidade antes de produção e as recomendações ao gestor de projeto. 24 páginas. |

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
| `docs/DOCUMENTACAO_PROJETO_E_LGPD/` | Documentação legal e técnica de origem (docs 01 a 09) |
| `docs/PLANO_V1_COMPLETO.md` | Plano maestro aprovado com as invariantes legais |
| Suíte de testes (`tests/`) | Evidência automatizada das garantias de privacidade (33 testes) |
| `git log` | Evidência de processo: 81 commits atômicos |

## Como regenerar

O relatório é gerado por `scripts/gerar_relatorio_lgpd.py` — ferramenta de documentação, **fora do
pipeline de produção** (não importa nenhum módulo do produto, não lê nem grava mídia).

```bash
python3 -m venv .venv-relatorio
./.venv-relatorio/bin/pip install reportlab
./.venv-relatorio/bin/python scripts/gerar_relatorio_lgpd.py
```

Saída: `docs/relatorios/RELATORIO-CONFORMIDADE-LGPD-v1.0-<AAAA-MM-DD>.pdf`.

> **Nota de privacidade:** o gerador apenas lê arquivos de texto do repositório e escreve um PDF.
> `reportlab` é uma dependência **opcional** de geração de documentação e não consta em
> `requirements.txt` do produto.

## Nota sobre versões

O relatório é um **snapshot**. Ao reexecutar o gerador após novas fases, atualize a data e a versão no
cabeçalho do PDF e o número da versão no rodapé (campo "Versão" da capa). A matriz de conformidade
da seção 6 e as lacunas da seção 7 devem ser reavaliadas a cada avanço de fase.
