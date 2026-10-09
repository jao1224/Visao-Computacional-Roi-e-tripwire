# 07. PARECER JURÍDICO-TÉCNICO: LGPD & MARCO CIVIL DA INTERNET

## 1. Síntese do Diagnóstico de Risco e Multas

| Operação Avaliada | Status Legal | Risco Regulatório | Multa Potencial Máxima |
| :--- | :---: | :---: | :--- |
| **Detecção em Memória RAM (main.py)** | **CONFORME** | Quase Nulo (< 5%) | Improvável |
| **Vigilância Biométrica Sem Consentimento** | **INFRAÇÃO GRAVE** | Crítico (85% - 95%) | Até R$ 50 Milhões (ou 2% do faturamento da empresa) |
| **Analytics com Detecção de Corpo (CrowdHuman)** | **100% CONFORME** | Quase Nulo (< 5%) | R$ 0 (Isento de passivo de dados sensíveis) |
| **Controle de Acesso com Exclusão no Checkout** | **100% CONFORME** | Baixo (< 15%) | R$ 0 (Amparado em contrato e consentimento no check-in) |

---

## 2. Análise dos Artigos Críticos da LGPD (Lei nº 13.709/2018)

1. **Art. 5º, II e Art. 11 (Dados Biométricos Sensíveis):**
   - Vetores/Embeddings faciais são dados sensíveis.
   - **NÃO EXISTE BASE LEGAL DE LEGÍTIMO INTERESSE PARA BIOMETRIA.** Para fins de analytics de fluxo em lojas/hotéis, o tratamento de rostos sem consentimento é expressamente **ilegal**.
2. **Art. 6º, III (Princípio da Minimização e Necessidade):**
   - Para contar quantas pessoas estão na recepção ou no restaurante, **não é necessário extrair a face nem identificar a pessoa**. O uso de detecção de silhueta (corpo inteiro) atende 100% à finalidade sem violar a lei.
3. **Art. 12, §2º (Formação de Perfil Comportamental):**
   - Reconstruir a rota de um indivíduo desconhecido entre câmeras cria um perfil de hábitos, exigindo amparo legal estrito.
4. **Art. 14 (Proteção de Crianças e Adolescentes):**
   - Câmeras em áreas de piscina e lazer capturam menores. Tratar biometria de crianças sem consentimento parental específico gera risco de autuação máxima pela ANPD.
5. **Art. 16 e 18 (Retenção e Direitos do Titular):**
   - É obrigatório implementar mecanismos automáticos de eliminação (`TTL` de checkout) e endpoints para exclusão de dados a pedido do cliente.

---

## 3. Marco Civil da Internet (Lei nº 12.965/2014)

1. **Art. 15 (Guarda de Registros de Acesso a Aplicações):**
   - O backend web / FastAPI **deve guardar os logs de acesso telemático (IP, porta lógica, data e hora) por 6 (seis) meses sob sigilo**.
2. **Distinção Essencial:**
   - O Marco Civil *obriga a retenção de logs de conexão*, mas **NÃO autoriza a retenção de imagens, vídeos ou dados biométricos** de pessoas.

---

## 4. Tabela de Temporalidade Técnica e Retenção de Dados (Data Retention)

| Tipo de Dado | Onde Fica Armazenado | Tempo Máximo de Guarda | Mecanismo de Expiração / Purge |
| :--- | :--- | :--- | :--- |
| **Frames Brutos de Câmera** | Memória RAM | **0 segundos** (Volátil) | Descartado imediatamente após a inferência. |
| **Buffer do Tracker (ByteTrack)** | Memória RAM | **$\le$ 15 segundos** | Liberado quando o objeto sai do enquadramento. |
| **Snapshots de Faces** | Storage / Disco | **24 a 48 horas** (Apenas se houver RIPD de segurança) | Purge cron diário no storage. |
| **Embeddings Faciais de Hóspedes** | Banco de Dados | **Até o Checkout** | Trigger acionado pelo sistema da recepção (PMS). |
| **Logs de Acesso à API** | Servidor de Logs | **Exatamente 6 meses** | Rotina mensal de arquivamento/expurgo (Marco Civil Art. 15). |
| **Métricas de Fluxo por Zona** | Tabela `metricas_fluxo_zona` | **Permanente / Histórico** | Dado anonimizado (LGPD Art. 12) para relatórios de BI. |
