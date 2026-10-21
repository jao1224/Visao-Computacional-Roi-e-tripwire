# 01. VISÃO GERAL E REQUISITOS DE NEGÓCIO DO HOTEL

> **⚠ Escopo vigente:** sem face, sem catraca/controle de acesso, sem MTMCT — apenas analytics de fluxo (contagem, ocupação, dwell, heatmap agregado). Ver `../REQUIREMENTS.md` §Out of Scope, `../ROADMAP.md` e o aviso no `README.md` desta pasta.

## 1. Contexto e Problema de Negócio
Hotéis e resorts enfrentam dificuldades para dimensionar equipes operacionais, evitar filas em restaurantes/recepção, garantir segurança e entender como os hóspedes usufruem das instalações (piscinas, academias, lounges).

O sistema de visão computacional foi concebido para transformar câmeras de segurança convencionais (CFTV/DVR) em **sensores inteligentes de inteligência de negócios e segurança operacional**.

---

## 2. Objetivos Principais

### A. Gestão de Ocupação & Fluxo (Analytics)
- **Contagem por Zona:** Medir entradas e saídas em tempo real por área física.
- **Tempo de Permanência (Dwell Time):** Calcular o tempo médio de espera ou consumo por ambiente (ex: tempo na fila do check-in vs. tempo no restaurante).
- **Mapas de Calor (Heatmaps):** Identificar horários de pico e áreas subutilizadas.
- **Previsão de Demanda:** Subsidiar escalas de funcionários (garçons, atendentes, limpeza) com base nos dados de tráfego.

### B. Controle de Acesso & Segurança — 🚫 FORA DO ESCOPO (superado em 2026-10-08)
> **NÃO implementar nenhuma linha desta seção.** Controle de acesso e biometria = proibidos para sempre (LGPD art. 11; decisão do usuário). Esta seção permanece apenas como registro do que foi imaginado no início do projeto. Escopo vigente = apenas a seção A (analytics de fluxo).
- ~~**Monitoramento de Áreas Restritas:** Notificar a segurança caso pessoas acessem locais proibidos fora de horário.~~ *(fora do escopo v1 — ver `../REQUIREMENTS.md` §Out of Scope)*

---

## 3. Requisitos Funcionais do Sistema

1. **Ingestão Multi-Câmera:** Processar múltiplos streams de vídeo simultâneos (RTSP de DVRs Intelbras, Hikvision, Dahua).
2. ~~**Rastreamento Sem Fricção:** Rastrear indivíduos ao longo do estabelecimento~~ → **Contagem sem duplicação (corrigido 2026-10-08):** não duplicar contagens **dentro da mesma câmera** (ByteTrack efêmero, RAM, intra-câmera). **Rastrear indivíduos "ao longo do estabelecimento" é proibido** — nenhuma associação entre câmeras (LGPD art. 12 §2º).
3. **Dashboards Gerenciais em Tempo Real:** Interface web intuitiva exibindo taxa de ocupação instantânea e gráficos de tendência.
4. **Respeito Integral à Privacidade:** Não armazenar biometria de clientes não cadastrados e garantir conformidade com a LGPD e Marco Civil.
