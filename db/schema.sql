-- Schema restrito para Fase 3 (Persistência PostgreSQL - fila + escrita em lote)
-- Somente configuração e métricas agregadas. SEM dados por-pessoa.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Câmeras
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    zone_id INT,
    codigo_camera VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    rtsp_url VARCHAR(255),
    localizacao VARCHAR(100) NOT NULL,
    fps_alvo INT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Zonas (ROI)
CREATE TABLE IF NOT EXISTS zonas (
    id SERIAL PRIMARY KEY,
    codigo_zona VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    tipo_zona VARCHAR(50) DEFAULT 'monitoramento',
    coordenadas_poligono JSONB DEFAULT '[]'::JSONB,
    capacidade_maxima INT DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Adicionar FK após criação
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_cameras_zone'
    ) THEN
        ALTER TABLE cameras ADD CONSTRAINT fk_cameras_zone FOREIGN KEY (zone_id) REFERENCES zonas(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_cameras_zone ON cameras(zone_id);

-- 3. Métricas agregadas por zona e janela (APENAS agregados)
CREATE TABLE IF NOT EXISTS metricas_fluxo_zona (
    id BIGSERIAL PRIMARY KEY,
    zona_id INT NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    janela_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    janela_fim TIMESTAMP WITH TIME ZONE NOT NULL,
    ocupacao_media REAL DEFAULT 0.0,
    pct_area_media REAL DEFAULT 0.0,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_metricas_zona_janela UNIQUE (zona_id, janela_inicio, janela_fim)
);

CREATE INDEX IF NOT EXISTS idx_metricas_tempo ON metricas_fluxo_zona(zona_id, janela_inicio);

-- 4. Heatmap de densidade agregado (célula x janela) — posições efêmeras somadas
-- NUNCA linha por pessoa. Apenas contadores agregados por grade_x/grade_y.
CREATE TABLE IF NOT EXISTS heatmap_densidade_camada (
    id BIGSERIAL PRIMARY KEY,
    camera_id INT NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    janela_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    janela_fim TIMESTAMP WITH TIME ZONE NOT NULL,
    grade_x INT NOT NULL,
    grade_y INT NOT NULL,
    contador INT NOT NULL DEFAULT 0,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_heatmap_camera_janela_celula UNIQUE (camera_id, janela_inicio, janela_fim, grade_x, grade_y)
);

CREATE INDEX IF NOT EXISTS idx_heatmap_janela ON heatmap_densidade_camada(camera_id, janela_inicio);

-- 5. Dwell agregado por zona x janela (NUNCA linha por pessoa)
CREATE TABLE IF NOT EXISTS dwell_agregado_zona (
    id BIGSERIAL PRIMARY KEY,
    zona_id INT NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    janela_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    janela_fim TIMESTAMP WITH TIME ZONE NOT NULL,
    n_permanencias INT NOT NULL DEFAULT 0,
    soma_segundos BIGINT NOT NULL DEFAULT 0,
    min_segundos INT,
    max_segundos INT,
    histograma JSONB DEFAULT '{"0-2min": 0, "2-5min": 0, "5-15min": 0, "15+min": 0}'::JSONB,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dwell_zona_janela UNIQUE (zona_id, janela_inicio, janela_fim)
);

CREATE INDEX IF NOT EXISTS idx_dwell_janela ON dwell_agregado_zona(zona_id, janela_inicio);
