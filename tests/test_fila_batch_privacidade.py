"""Privacidade e isolamento da persistência: fila, agregador e batch writer."""

import os

import pytest

from persistencia import batch_writer as bw
from persistencia.agregador import JanelaAgregada
from persistencia.fila import FilaAgregados

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAVES_VETADAS = ['track_id', 'session_id', 'id_rastreio_local', 'embedding', 'rota', 'jornada']

EVENTO_VALIDO = {
    'codigo_zona': 'hall',
    'janela_inicio': '2026-10-28T10:00:00+00:00',
    'janela_fim': '2026-10-28T10:01:00+00:00',
    'ocupacao_media': 3.0,
    'pct_area_media': 12.5,
}


@pytest.mark.parametrize('chave', CHAVES_VETADAS)
def test_fila_rejeita_chave_por_pessoa(chave):
    fila = FilaAgregados()
    with pytest.raises(ValueError):
        fila.put({**EVENTO_VALIDO, chave: 'x'})
    assert fila.qsize() == 0


def test_fila_aceita_evento_agregado():
    fila = FilaAgregados()
    fila.put(EVENTO_VALIDO)
    assert fila.get(timeout=1) == EVENTO_VALIDO


def test_agregador_so_devolve_medias_por_janela():
    janela = JanelaAgregada(janela_segundos=60)
    for ocupacao, pct in [(2, 10.0), (4, 20.0), (6, 30.0)]:
        janela.adicionar('hall', ocupacao, pct)

    eventos = janela.fechar_janela()

    assert len(eventos) == 1
    evento = eventos[0]
    assert evento['codigo_zona'] == 'hall'
    assert evento['ocupacao_media'] == 4.0
    assert evento['pct_area_media'] == 20.0
    for chave in CHAVES_VETADAS:
        assert chave not in evento
    # valores individuais descartados após o fechamento
    assert janela.dados_por_zona == {}


def test_agregador_nao_fecha_antes_da_janela():
    janela = JanelaAgregada(janela_segundos=60)
    assert not janela.deve_fechar(agora=janela.inicio + 59)
    assert janela.deve_fechar(agora=janela.inicio + 60)


@pytest.mark.parametrize('arquivo', ['main.py', 'zona.py'])
def test_hot_path_sem_sql(arquivo):
    with open(os.path.join(RAIZ, arquivo), encoding='utf-8') as f:
        conteudo = f.read()
    for token in ['psycopg2', 'cursor', '.execute(', 'commit(', 'execute_values']:
        assert token not in conteudo, f'{token} no hot-path ({arquivo})'


def test_writer_e_thread_daemon_com_on_conflict():
    assert bw.BatchWriter(FilaAgregados()).daemon is True
    assert 'ON CONFLICT' in bw.SQL_METRICAS
    assert 'metricas_fluxo_zona' in bw.SQL_METRICAS


def test_writer_recusa_lote_com_dado_por_pessoa():
    writer = bw.BatchWriter(FilaAgregados())
    with pytest.raises(ValueError):
        writer.gravar_lote([{**EVENTO_VALIDO, 'track_id': 7}])


class _CursorFalso:
    def __init__(self):
        self.sqls = []
        self._linhas = [('hall', 1)]

    def execute(self, sql, params=None):
        self.sqls.append((sql, params))

    def fetchall(self):
        return self._linhas

    def close(self):
        pass


class _ConnFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commitou = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commitou = True

    def close(self):
        pass


def test_writer_troca_codigo_de_zona_pelo_id_numerico(monkeypatch):
    cursor = _CursorFalso()
    conn = _ConnFalsa(cursor)
    monkeypatch.setattr(bw.psycopg2, 'connect', lambda **_: conn)
    inseridos = {}
    monkeypatch.setattr(bw, 'execute_values', lambda cur, sql, values: inseridos.update(sql=sql, values=values))

    bw.BatchWriter(FilaAgregados()).gravar_lote([EVENTO_VALIDO])

    assert conn.commitou is True
    assert inseridos['values'] == [
        (1, EVENTO_VALIDO['janela_inicio'], EVENTO_VALIDO['janela_fim'], 3.0, 12.5)
    ]
    assert any('INSERT INTO zonas' in sql for sql, _ in cursor.sqls)


def test_writer_nao_propaga_erro_de_banco(monkeypatch):
    def explode(**_):
        raise RuntimeError('banco fora')

    monkeypatch.setattr(bw.psycopg2, 'connect', explode)
    bw.BatchWriter(FilaAgregados()).gravar_lote([EVENTO_VALIDO])  # não deve levantar


@pytest.mark.skipif(os.getenv('DB_TESTE') != '1',
                    reason='defina DB_TESTE=1 (e DB_*) para validar contra PostgreSQL real')
def test_gravacao_real_contra_postgres():
    """Valida o SQL de verdade: aplica o schema e grava o lote com rollback no final."""
    conn = bw.psycopg2.connect(**bw.get_conn_params())
    try:
        with open(os.path.join(RAIZ, 'db', 'schema.sql'), encoding='utf-8') as f:
            cur = conn.cursor()
            cur.execute(f.read())
        conn.commit()
        writer = bw.BatchWriter(FilaAgregados())
        writer.gravar_lote([EVENTO_VALIDO])
        writer.gravar_lote([EVENTO_VALIDO])  # idempotência
        cur.execute(
            'SELECT count(*) FROM metricas_fluxo_zona m JOIN zonas z ON z.id = m.zona_id '
            'WHERE z.codigo_zona = %s', (EVENTO_VALIDO['codigo_zona'],))
        assert cur.fetchone()[0] == 1
        cur.execute('DELETE FROM metricas_fluxo_zona')
        conn.commit()
    finally:
        conn.close()

