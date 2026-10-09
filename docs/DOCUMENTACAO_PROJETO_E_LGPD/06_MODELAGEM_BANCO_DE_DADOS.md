# 06. MODELAGEM DO BANCO DE DADOS (POSTGRESQL & SCHEMAS)

> **⚠ ADAPTAÇÃO OBRIGATÓRIA (2026-10-08) — SCHEMA PARCIALMENTE SUPERADO.**
> **NÃO implementar** as tabelas `sessoes` e `session_traces` (e nenhuma tabela/coluna por-pessoa: sem track_id, rota, embedding) — persistem trilha individual = perfil comportamental (LGPD art. 12 §2º). Implementar apenas: tabelas de configuração (`cameras`, `zonas`) + métricas agregadas (`metricas_fluxo_zona`, agregados de dwell com histograma, buckets de heatmap). Eventos ENTROU/SAIU: somente zona, direção e timestamp de janela — **sem chave de pessoa**. Fonte do escopo vigente: `PLANO_V1_COMPLETO.md` e `09_PLANO_DE_FASES_V1.md`.

## 1. Modelo Entidade-Relacionamento (MER)

```mermaid
erDiagram
    ZONAS ||--o{ CAMERAS : "aloca"
    ZONAS ||--o{ METRICAS_FLUXO_ZONA : "contabiliza"
    CAMERAS ||--o{ SESSION_TRACES : "captura"
    SESSOES ||--o{ SESSION_TRACES : "compoe_trilha"
    SESSOES ||--o{ EVENTOS_ALERTAS : "desencadeia"

    ZONAS {
        int id PK
        varchar codigo_zona UK
        varchar nome
        varchar tipo_zona
        jsonb coordenadas_poligono
        int capacidade_maxima
        timestamp created_at
    }

    CAMERAS {
        int id PK
        int zone_id FK
        varchar codigo_camera UK
        varchar nome
        varchar rtsp_url
        varchar localizacao
        int fps_alvo
        boolean is_active
        timestamp created_at
    }

    SESSOES {
        uuid session_id PK
        timestamp inicio_sessao
        timestamp fim_sessao
        real duracao_total_seg
        varchar status_sessao
        timestamp expira_em
        timestamp created_at
    }

    SESSION_TRACES {
        bigint id PK
        uuid session_id FK
        int camera_id FK
        int zone_id FK
        int id_rastreio_local
        timestamp entry_timestamp
        timestamp last_seen_timestamp
        timestamp exit_timestamp
        real dwell_time_seconds
        boolean is_active
    }

    METRICAS_FLUXO_ZONA {
        bigint id PK
        int zona_id FK
        timestamp janela_inicio
        timestamp janela_fim
        int total_entradas
        int total_saidas
        real ocupacao_media
        real tempo_medio_permanencia_seg
    }
```

---

## 2. Schema SQL Completo (PostgreSQL)

```sql
-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Zonas do Hotel
CREATE TABLE IF NOT EXISTS zonas (
    id SERIAL PRIMARY KEY,
    codigo_zona VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    tipo_zona VARCHAR(50) DEFAULT 'monitoramento',
    coordenadas_poligono JSONB DEFAULT '[]'::JSONB,
    capacidade_maxima INT DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Câmeras com Mapeamento de Zona
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    zone_id INT REFERENCES zonas(id) ON DELETE SET NULL,
    codigo_camera VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    rtsp_url VARCHAR(255),
    localizacao VARCHAR(100) NOT NULL,
    fps_alvo INT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cameras_zone ON cameras(zone_id);

-- 3. Sessões Globais com Expiração (TTL)
CREATE TABLE IF NOT EXISTS sessoes (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inicio_sessao TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fim_sessao TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    duracao_total_seg REAL DEFAULT 0.0,
    status_sessao VARCHAR(30) DEFAULT 'ativa',
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 day'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sessoes_status ON sessoes(status_sessao, expira_em);

-- 4. Trilha de Permanência por Câmera / Zona
CREATE TABLE IF NOT EXISTS session_traces (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessoes(session_id) ON DELETE CASCADE,
    camera_id INT NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    zone_id INT REFERENCES zonas(id) ON DELETE SET NULL,
    id_rastreio_local INT NOT NULL,
    entry_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    dwell_time_seconds REAL GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (COALESCE(exit_timestamp, last_seen_timestamp) - entry_timestamp))
    ) STORED,
    confianca_media REAL DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_session_camera_active UNIQUE (session_id, camera_id, is_active)
);

-- 5. Métricas Agregadas e Anonimizadas (Conforme LGPD Art. 12)
CREATE TABLE IF NOT EXISTS metricas_fluxo_zona (
    id BIGSERIAL PRIMARY KEY,
    zona_id INT NOT NULL REFERENCES zonas(id) ON DELETE CASCADE,
    janela_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    janela_fim TIMESTAMP WITH TIME ZONE NOT NULL,
    total_entradas INT DEFAULT 0,
    total_saidas INT DEFAULT 0,
    ocupacao_media REAL DEFAULT 0.0,
    tempo_medio_permanencia_seg REAL DEFAULT 0.0,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_metricas_tempo ON metricas_fluxo_zona(zona_id, janela_inicio);
```
