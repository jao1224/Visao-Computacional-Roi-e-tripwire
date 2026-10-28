"""Escrita em lote no PostgreSQL — roda em thread própria, fora do loop de vídeo."""

import threading
import time
import uuid
from collections import deque
from queue import Empty

import psycopg2
from psycopg2.extras import execute_values

from db.config import get_conn_params

CHAVES_VETADAS = ('track_id', 'session_id', 'id_rastreio_local', 'embedding', 'rota', 'jornada')

SQL_METRICAS = """
    INSERT INTO metricas_fluxo_zona
        (zona_id, janela_inicio, janela_fim, ocupacao_media, pct_area_media)
    VALUES %s
    ON CONFLICT (zona_id, janela_inicio, janela_fim) DO NOTHING
"""


class BatchWriter(threading.Thread):
    """Consome a fila e grava em lote. Zonas precisam existir no banco (db/seed.py)."""

    def __init__(self, fila_agregados, batch_size=50, flush_interval=5.0, max_pendentes=1000):
        super().__init__(daemon=True)
        self.fila = fila_agregados
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = True
        self._conn = None
        self._pendentes = deque()
        self._max_pendentes = max_pendentes
        self._falhas_seguidas = 0

    def run(self):
        while self.running:
            self._pendentes.extend(self._coletar())
            if self._pendentes:
                self._drenar()
        self._drenar(final=True)

    def _coletar(self):
        """Acumula eventos até batch_size ou flush_interval segundos."""
        lote = []
        limite = time.time() + self.flush_interval
        while len(lote) < self.batch_size and time.time() < limite:
            try:
                lote.append(self.fila.get(timeout=0.5))
                self.fila.task_done()
            except Empty:
                if lote:
                    break
        return lote

    def _drenar(self, final=False):
        """Grava os pendentes; em falha, mantém para retry com backoff e descarta o excedente."""
        while self._pendentes:
            bloco = [self._pendentes.popleft() for _ in range(min(self.batch_size, len(self._pendentes)))]
            try:
                self.gravar_lote(bloco)
                self._falhas_seguidas = 0
            except Exception as erro:
                self._devolver(bloco)
                self._falhas_seguidas += 1
                print(f'[Erro] Lote não gravado ({erro}); {len(self._pendentes)} evento(s) em retry')
                self._evitar_overflow()
                if final:
                    return
                time.sleep(min(30.0, 0.5 * 2 ** (self._falhas_seguidas - 1)))
                return

    def _devolver(self, bloco):
        """Recoloca o bloco no início da fila de pendentes, preservando a ordem."""
        self._pendentes.extendleft(reversed(bloco))

    def _evitar_overflow(self):
        excesso = len(self._pendentes) - self._max_pendentes
        if excesso <= 0:
            return
        for _ in range(excesso):
            self._pendentes.popleft()
        print(f'[Aviso] Fila de retry cheia: {excesso} evento(s) mais antigo(s) descartado(s)')

    def gravar_lote(self, lote):
        """Grava um bloco numa transação. Levanta exceção para o chamador decidir o retry."""
        batch_id = str(uuid.uuid4())
        for ev in lote:
            if any(c in ev for c in CHAVES_VETADAS):
                raise ValueError(f'Lote {batch_id} contém dados por-pessoa')
        cur = self._conexao().cursor()
        try:
            mapa = self._resolver_zonas(cur, {ev['codigo_zona'] for ev in lote})
            desconhecidas = {ev['codigo_zona'] for ev in lote} - mapa.keys()
            if desconhecidas:
                print(f'[Aviso] Lote {batch_id}: zona(s) não cadastrada(s) ignorada(s): {sorted(desconhecidas)}')
            values = [
                (mapa[ev['codigo_zona']], ev['janela_inicio'], ev['janela_fim'],
                 ev['ocupacao_media'], ev['pct_area_media'])
                for ev in lote if ev['codigo_zona'] in mapa
            ]
            if values:
                execute_values(cur, SQL_METRICAS, values)
            self._conn.commit()
            cur.close()
        except Exception:
            # Transação abortada inutiliza a conexão: descartar força reconectar no retry.
            self._descartar_conexao()
            raise

    def _resolver_zonas(self, cur, codigos):
        cur.execute('SELECT codigo_zona, id FROM zonas WHERE codigo_zona = ANY(%s)', (list(codigos),))
        return dict(cur.fetchall())

    def _conexao(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**get_conn_params())
        return self._conn

    def _descartar_conexao(self):
        try:
            self._conn.close()
        except Exception:
            pass
        self._conn = None

    def parar(self):
        self.running = False
