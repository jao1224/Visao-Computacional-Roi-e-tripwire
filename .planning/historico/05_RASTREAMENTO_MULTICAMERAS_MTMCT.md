# 05. RASTREAMENTO MULTI-CÂMERAS (MTMCT) E RE-IDENTIFICAÇÃO

> **⚠ DOCUMENTO SUPERADO (2026-10-08) — NÃO IMPLEMENTAR.**
> MTMCT, Re-ID, fusão de trilhas e qualquer associação entre câmeras estão **FORA DO ESCOPO PARA SEMPRE** (LGPD art. 12 §2º — reconstruir rotas = perfil comportamental; ordem explícita do usuário: "câmera 2 nunca pode reconhecer alguém da câmera 1, nem por silhueta"). Este documento permanece apenas como referência histórica/research. O rastreamento permitido é **intra-câmera, em RAM, segundos** (ByteTrack), nunca persistido. Fonte do escopo vigente: `../REQUIREMENTS.md` (requisitos canônicos) e `../ROADMAP.md` (fases canônicas).

## 1. O Desafio do Rastreamento Multi-Câmeras (MTMCT)
Em um hotel com dezenas de câmeras, um hóspede entra pela porta principal (Cam 1), faz check-in no balcão (Cam 2), pega o elevador no 1º andar (Cam 4) e vai ao seu quarto (Cam 5).

O **MTMCT (Multi-Target Multi-Camera Tracking)** é o subsistema responsável por correlacionar que essas 4 aparições pertencem à **mesma jornada (session_id)**, sem gerar 4 contagens isoladas e incorretas.

---

## 2. Pipeline de Rastreamento em 3 Fases

```mermaid
flowchart LR
    subgraph Fase1["Fase 1: Rastreamento Local"]
        DET["YOLO Detection"] --> SORT["ByteTrack / Kalman Filter"]
        SORT --> LOCAL_ID["ID Local da Câmera (track_id)"]
    end

    subgraph Fase2["Fase 2: Extração de Features"]
        LOCAL_ID --> HOG["Descritores de Aparência / Cor"]
        LOCAL_ID --> REID_FEAT["Vetor de Re-ID Efêmero (Sem Face)"]
    end

    subgraph Fase3["Fase 3: Fusão Global"]
        REID_FEAT --> MATCHER["Topological & Feature Matcher"]
        MATCHER --> GLOBAL_SESS["Session ID Global Unificado"]
    end

    style Fase1 fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style Fase2 fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff
    style Fase3 fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff
```

---

## 3. Mecanismos de Associação e Lógica Espaço-Temporal

Para evitar falsas associações entre câmeras, o sistema combina:
1. **Restrição Topológica (Espaço-Tempo):** Uma pessoa que acabou de ser vista saindo da recepção não pode aparecer 2 segundos depois na piscina (distância física inviável).
2. **Similaridade de Aparência:** Comparação por distância cosseno entre vetores visuais de vestimenta/cores.
3. **Timeout de Desconexão (TTL em RAM):** Se o indivíduo não for visto em nenhuma câmera adjacente após 15 minutos, a sessão é finalizada e o buffer de memória é liberado.
