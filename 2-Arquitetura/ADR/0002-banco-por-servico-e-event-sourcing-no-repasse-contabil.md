# ADR 0002: Banco por Serviço e Event Sourcing no Repasse Contábil

**Status:** aceito (com adendo de versionamento de apurações)

**Contexto:**
O repasse financeiro entre operadoras de ônibus e prefeituras exige auditabilidade matemática total e capacidade de reprocessamento contábil retroativo diante de mudanças de regras tarifárias ou contestações em até 30 dias. Sobrescrever registros transacionais destrói a trilha contábil exigida pelos órgãos reguladores.

**Decisão:**
1. **Banco por Célula/Módulo:** Cada célula possui seu banco de dados isolado, sem acesso direto entre diferentes municípios;
2. **Event Sourcing no Financeiro (Capítulo 15):** O subdomínio de *Repasse Contábil* armazena as transações exclusivamente como um fluxo imutável de eventos (`ViagemValidada`, `RecargaEfetuada`) numa tabela relacional *append-only*;
3. **CQRS para Leitura (Capítulo 14):** Relatórios de fechamento e extratos das concessionárias são gerados por projeções de leitura derivadas do reprocessamento dos eventos.

**Adendo Pós-Leitura Cruzada (Entrega 5):**
Cada fechamento contábil gerado é armazenado de forma imutável e versionada ($V_1, V_2, \dots$). Quando uma regra retroativa for aplicada, o reprocessamento gera a versão $V_2$ e um relatório de ajuste de diferenças (crédito/débito) em vez de sobrescrever a versão anterior.

**Consequências:**
- *Positivas:* Trilha de auditoria infalível e reprodução exata do estado contábil em qualquer data pregressa.
- *Negativas:* O armazenamento de eventos cresce continuamente e exige estratégias de consolidação (snapshots) para manter o desempenho de leitura.
