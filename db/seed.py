"""Sincroniza cameras/zonas do config/zonas.yaml com o banco. Uso: python -m db.seed"""

import json
import os

import psycopg2
import yaml

from db.config import get_conn_params

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SQL_CAMERA = """
    INSERT INTO cameras (codigo_camera, nome, localizacao)
    VALUES (%s, %s, %s)
    ON CONFLICT (codigo_camera) DO UPDATE
        SET nome = EXCLUDED.nome, localizacao = EXCLUDED.localizacao
"""

SQL_ZONA = """
    INSERT INTO zonas (codigo_zona, nome, tipo_zona, coordenadas_poligono, capacidade_maxima)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (codigo_zona) DO UPDATE
        SET nome = EXCLUDED.nome,
            tipo_zona = EXCLUDED.tipo_zona,
            coordenadas_poligono = EXCLUDED.coordenadas_poligono,
            capacidade_maxima = EXCLUDED.capacidade_maxima
"""


def linhas_de_config(caminho=None):
    """Lê o YAML e devolve (cameras, zonas) prontos para o upsert."""
    if caminho is None:
        caminho = os.path.join(base_dir, 'config', 'zonas.yaml')
    with open(caminho, 'r', encoding='utf-8') as arquivo:
        dados = yaml.safe_load(arquivo) or {}

    cameras, zonas = [], []
    for codigo_camera, camera in dados.items():
        if not isinstance(camera, dict):
            continue
        capacidade = camera.get('capacidade')
        if isinstance(capacidade, bool) or not isinstance(capacidade, int) or capacidade <= 0:
            capacidade = 100
        cameras.append((codigo_camera, codigo_camera, codigo_camera))
        for zona in camera.get('zonas') or []:
            if not isinstance(zona, dict) or not zona.get('id'):
                continue
            poligono = zona.get('roi_pontos') or zona.get('pontos') or []
            zonas.append((
                str(zona['id']),
                str(zona['id']),
                str(zona.get('tipo', 'roi')),
                json.dumps(poligono),
                capacidade,
            ))
    return cameras, zonas


def main(caminho=None):
    cameras, zonas = linhas_de_config(caminho)
    conn = psycopg2.connect(**get_conn_params())
    try:
        cur = conn.cursor()
        for linha in cameras:
            cur.execute(SQL_CAMERA, linha)
        for linha in zonas:
            cur.execute(SQL_ZONA, linha)
        conn.commit()
        cur.close()
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        print('[Erro] Tabelas ausentes — aplique o schema antes: psql "$DB_URL" -f db/schema.sql')
        return
    finally:
        conn.close()
    print(f'[OK] {len(cameras)} câmera(s) e {len(zonas)} zona(s) sincronizadas')


if __name__ == '__main__':
    main()
