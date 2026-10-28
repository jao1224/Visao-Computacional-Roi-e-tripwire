"""Agregação por janela em RAM — só médias saem daqui, nada por pessoa."""

import time
from datetime import datetime, timezone


class JanelaAgregada:
    def __init__(self, janela_segundos=60):
        self.janela_segundos = janela_segundos
        self.inicio = time.time()
        self.dados_por_zona = {}

    def adicionar(self, codigo_zona, ocupacao, pct_area):
        self.dados_por_zona.setdefault(codigo_zona, ([], []))
        self.dados_por_zona[codigo_zona][0].append(ocupacao)
        self.dados_por_zona[codigo_zona][1].append(pct_area)

    def deve_fechar(self, agora=None):
        agora = time.time() if agora is None else agora
        return (agora - self.inicio) >= self.janela_segundos

    def fechar_janela(self):
        """Fecha a janela, descarta os valores individuais e devolve um evento por zona."""
        agora = time.time()
        janela_inicio = datetime.fromtimestamp(self.inicio, tz=timezone.utc)
        janela_fim = datetime.fromtimestamp(agora, tz=timezone.utc)
        eventos = []
        for codigo_zona, (ocupacoes, pct_areas) in self.dados_por_zona.items():
            if not ocupacoes:
                continue
            eventos.append({
                'codigo_zona': codigo_zona,
                'janela_inicio': janela_inicio,
                'janela_fim': janela_fim,
                'ocupacao_media': round(sum(ocupacoes) / len(ocupacoes), 3),
                'pct_area_media': round(sum(pct_areas) / len(pct_areas), 3) if pct_areas else 0.0,
            })
        self.inicio = agora
        self.dados_por_zona = {}
        return eventos
