from pathlib import Path


def test_schema_nao_contem_tabelas_ou_colunas_vetadas():
    schema_path = Path("db/schema.sql")
    assert schema_path.exists(), "db/schema.sql deve existir"
    conteudo = schema_path.read_text(encoding="utf-8").lower()

    # Tabelas vetadas
    vetadas_tabelas = ["sessoes", "session_traces"]
    for t in vetadas_tabelas:
        assert f"create table {t}" not in conteudo, f"Tabela vetada encontrada: {t}"

    # Colunas vetadas
    vetadas_cols = ["track_id", "session_id", "id_rastreio_local", "embedding", "rota", "jornada"]
    for c in vetadas_cols:
        assert c not in conteudo, f"Coluna vetada encontrada: {c}"

    # Obrigatórias/planejadas (evitar migrações futuras)
    obrigatorias = ["cameras", "zonas", "metricas_fluxo_zona", "heatmap_densidade_camada", "dwell_agregado_zona"]
    for o in obrigatorias:
        assert o in conteudo, f"Tabela obrigatória/planejada ausente: {o}"
