"""Escrita em lote no PostgreSQL — roda em thread própria, fora do loop de vídeo."""

import threading
import time
import uuid
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
    def __init__(self, fila_agregados, batch_size=50, flush_interval=5.0):
        super().__init__(daemon=True)
        self.fila = fila_agregados
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = True

    def run(self):
        while self.running:
            lote = self._coletar()
            if lote:
                self.gravar_lote(lote)

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

    def gravar_lote(self, lote):
        batch_id = str(uuid.uuid4())
        for ev in lote:
            if any(c in ev for c in CHAVES_VETADAS):
                raise ValueError(f'Lote {batch_id} contém dados por-pessoa')
        try:
            conn = psycopg2.connect(**get_conn_params())
            try:
                cur = conn.cursor()
                mapa = self._resolver_zonas(cur, {ev['codigo_zona'] for ev in lote})
                values = [
                    (mapa[ev['codigo_zona']], ev['janela_inicio'], ev['janela_fim'],
                     ev['ocupacao_media'], ev['pct_area_media'])
                    for ev in lote if ev['codigo_zona'] in mapa
                ]
                if values:
                    execute_values(cur, SQL_METRICAS, values)
                conn.commit()
                cur.close()
            finally:
                conn.close()
        except Exception as erro:
            # Thread não pode morrer; janelas perdidas são recalculáveis.
            # shortcut: lote descartado sem retry se o banco estiver fora, criar fila de retry se virar requisito
            print(f'[Erro] Lote {batch_id} não gravado: {erro}')

    def _resolver_zonas(self, cur, codigos):
        """Garante linha em zonas e devolve {codigo_zona: id} (FK exige id numérico)."""
        lista = list(codigos)
        cur.execute(
            'INSERT INTO zonas (codigo_zona, nome) SELECT c, c FROM unnest(%s::text[]) AS c '
            'ON CONFLICT (codigo_zona) DO NOTHING',
            (lista,),
        )
        cur.execute('SELECT codigo_zona, id FROM zonas WHERE codigo_zona = ANY(%s)', (lista,))
        return dict(cur.fetchall())

    def parar(self):
        self.running = False
