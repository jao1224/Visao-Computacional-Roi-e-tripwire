# Convenções de Código

**Atualizado em:** 2026-10-21 · **Estado real do repositório** (Fases 1 e 2 concluídas)

---

## 1. Idioma

- **Código, nomes, mensagens de console, docstrings e comentários: português do Brasil.**
- Funções em **verbo + substantivo**, com prefixo que indica a natureza da operação:
  - `captura.py` → `abrir_fonte`, `capturar`
  - `rastreio.py` → `carregar_modelo`, `rastrear`, `extrair_caixas`
  - `zona.py` → `carregar_zonas`, `atualizar_ocupacao`, `reconciliar_fonte`, `podar_track_states`, `calcular_intersecao_area_roi`, `_normalizar_zona`, `_pontos_validos`, `_area_roi`, `_bottom_center`, `_lado`, `_dist_ponto_segmento`
  - `overlay.py` → `desenhar_caixas`, `desenhar_rois`, `desenhar_contadores`, `desenhar_hud`
  - `main.py` → `resolver_fonte`, `resolver_modelo`, `main`
- Arquivos em `snake_case` (`captura.py`, `rastreio.py`, `entender_zonas.py`).
- Helpers privados usam prefixo `_` (`_normalizar_zona`, `_pontos_validos`).

## 2. Docstrings

- Presentes em **toda função pública**, em português, uma linha, terminadas com ponto.
- Exemplo: `"""Extrai as caixas como (id, xyxy, conf) com guard para id ausente."""`
- Comentários de código explicam **o porquê**, não o quê.

## 3. Tipagem e contratos

- Sem anotações de tipo no estilo PEP 484 — os contratos são documentados na docstring.
- **`rastreio.extrair_caixas` devolve tuplas `(id, (x1, y1, x2, y2), conf)`** — `id` inteiro, `xyxy` lista de 4 floats, `conf` float. `[]` quando `boxes.id` é `None` (guard obrigatório: nem todo frame tem ID).
- `captura.capturar` devolve `(frame, capture_ts)` ou `(None, None)`.
- `zona.carregar_zonas` devolve `[]` (e imprime aviso) quando o YAML não existe, a câmera não está no YAML ou a `capacidade` é inválida — **nunca levanta exceção** para entrada inválida de configuração.
- `zona._normalizar_zona` devolve `(dict_normalizado, None)` ou `(None, mensagem_de_erro)`.

## 4. Configuração

- YAML lido **sempre** com `yaml.safe_load` (nunca `yaml.load`).
- `config/zonas.yaml` — indexado por `camera_id`; cada câmera tem `capacidade` e a lista `zonas` (cada zona: `id`, `tipo`, `pontos`, e `roi_pontos` opcional).
- `tipo` aceita `'roi'` (polígono, ≥ 3 pontos) ou `'tripwire'` (segmento, ≥ 2 pontos + `direcao` em `entrada`/`saida`) — o tipo `tripwire` permanece aceito pelo validador, mas não é usado na configuração atual.
- Coordenadas em **pixels do frame**, `[x, y]`.

## 5. Privacidade no código (regras duras)

- **Nunca** `cv2.imwrite`, `VideoWriter`, `tofile`, `savefig` de frame, nem `pickle.dump` de estado.
- **Nunca** persistir `id` do track, `session_id`, trilha, rota, embedding ou vetor de aparência.
- **Nunca** comparar saídas de câmeras diferentes (nenhum Re-ID/MTMCT).
- **Nunca** adicionar dependência que traga `cv2.face` (`opencv-contrib-python` está proibido).
- Feature nova precisa continuar com saída **agregada** e estado **em RAM**.

## 6. Dependências

- `requirements.txt` com **pins exatos** (`==`): `ultralytics==8.4.121`, `opencv-python==5.0.0.93`, `numpy==2.5.2`, `lap==0.5.13`, `pyyaml==6.0.3`.
- `requirements-dev.txt` inclui `-r requirements.txt` + `pytest>=8.0`.
- Dependências de **documentação** (ex.: `reportlab`, usada só pelo gerador do relatório PDF) **não** entram no `requirements.txt` do produto — ficam em venv isolado fora do repositório.

## 7. Commits e versionamento

- **Conventional Commits**, em português, com escopo quando aplicável:
  `feat(overlay):`, `fix(main):`, `docs(plano):`, `test(zona):`, `refactor(main/zona):`, `chore(config):`.
- **Um commit por mudança coerente** (atômico); documentação/plano antes da implementação.
- Branch de trabalho: `feat/intersecao-area-roi`.

## 8. Testes

- Localização: `tests/`, nomenclatura `test_<módulo>.py`.
- Fixtures compartilhadas em `tests/conftest.py`.
- Comando canônico: `./.venv/bin/python -m pytest` (**nunca** o `pytest` do sistema — falta dependência).
- Testes que dependem de modelo ou vídeo ausentes devem **pular explicitamente** (`pytest.skip`), não falhar.

## 9. Ferramentas de desenvolvimento (fora do pipeline)

- `scripts/` — utilitários, **não** importados pelo runtime do produto.
- `scripts/demarcar_zona.py` grava **apenas coordenadas** em `config/zonas.yaml` (texto). Nada de imagem.
- `scripts/gerar_relatorio_lgpd.py` é gerador de **documentação** (PDF): não importa módulos do produto e não lê/grava mídia.
