import queue
import uuid


class FilaAgregados:
    def __init__(self, maxsize=10000):
        self.fila = queue.Queue(maxsize=maxsize)

    def put(self, evento_agregado):
        # Garantir que não venha com dados por-pessoa
        chaves_vetadas = {'track_id', 'session_id', 'id_rastreio_local', 'embedding', 'rota', 'jornada'}
        if any(c in evento_agregado for c in chaves_vetadas):
            raise ValueError("Evento não pode conter dados por-pessoa")
        self.fila.put(evento_agregado)

    def get(self, timeout=None):
        return self.fila.get(timeout=timeout)

    def task_done(self):
        self.fila.task_done()

    def qsize(self):
        return self.fila.qsize()

    def novo_batch_id(self):
        return str(uuid.uuid4())
