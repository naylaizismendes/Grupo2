# CHANGELOG — Entrega 5 (Versão Final Pós-Leitura Cruzada)

**Projeto:** SIMUB — Sistema Integrado de Mobilidade e Bilhetagem Urbana  
**Grupo:** 02 (Caso Ônibus — Envelope D)   

## 1. Mapeamento de Mudanças por Objeção

### Respostas ao Grupo 08
* **Objeção 01 (Dual-ledger / Chip):** Adicionado protocolo de `OrdemDeCreditoID` no chip do cartão para impedir dupla gravação de recarga nos ônibus offline (ADR 0005).
* **Objeção 02 (Deduplicação / Fraud Detection):** Formalizada a hierarquia em duas camadas (Camada 1: Par `ID_Cartao:Contador` determinístico no chip vs. Camada 2: Análise cinemática de GPS)[cite: 39].
* **Objeção 03 (Saldo de Confiança):** Formalizado o limite de no máximo 1 tarifa negativa com abate automático na recarga subsequente e inclusão na *denylist* após 48h.
* **Objeção 04 (Telemetria no Core):** Documentado o uso de *thread-pool* dedicado (*bulkhead* interno em memória) para o consumidor Kafka de telemetria sem concorrer com conexões JDBC da bilhetagem.
* **Objeção 05 (Microkernel Tarifário):** Criado o **ADR 0007**, separando parâmetros tarifários (alteráveis via base de dados sem deploy) de plugins de código para algoritmos divergentes.
* **Objeção 06 (Roteador de Células):** Especificada a infraestrutura gerenciada Multi-AZ *stateless* do Roteador com SLA de 99,99%.
* **Objeção 07 (Cold Start no FaaS):** Especificada a concorrência provisionada (*provisioned concurrency*) agendada para o pico matutino (6h00 às 8h30).
* **Objeção 08 (Custo Multi-Tenant das Células):** Documentado o modelo financeiro de repasse de custos em nuvem por célula municipal no contrato de licenciamento.
* **Objeção 09 (Recálculo de Repasse):** Substituído o descarte de projeções pelo versionamento imutável de fechamentos contábeis ($V_1, V_2, \dots$) com relatório automático de ajuste.
* **Objeção 10 (Ajustes no Spike):** Atualizado o script `codigo_spike.py` corrigindo a dedução de saldo, a chave de deduplicação temporal e o reenvio idempotente de lotes.

### Respostas ao Grupo 03
* **Objeção 01 (Disputa de Recursos no Monólito):** Criado o **ADR 0008**, isolando a execução da rotina de Repasse Contábil num *Worker Assíncrono (Job Batch)* com limite estrito de conexões JDBC.
* **Objeção 02 (Snapshots e Event Sourcing):** Clarificado no ADR 0002 que o fechamento é um cálculo *batch* sobre eventos e que *snapshots* funcionam como otimização secundária.
* **Objeção 03 (Fábrica de Integrações):** Clarificada a arquitetura *API-First/Model Canónico* com adaptadores legados em funções FaaS isoladas (ADR 0003).
* **Objeção 04 (Deploy Canary / Big Bang):** Criado o **ADR 0009** (substituindo o ADR 0004), estabelecendo o deploy em ondas progressivas (1, 3, 10, N cidades) com *rollback* automático por célula.
* **Objeção 05 (Autoridade do Saldo):** Reafirmado no ADR 0005 que a conta central na nuvem é a única autoridade definitiva do saldo, atuando o chip como cópia operacional local.

## 2. Resumo de Situação dos ADRs
* **ADR 0001:** Parcialmente substituído pelo ADR 0008
* **ADR 0002:** Aceito com adendo
* **ADR 0003:** Aceito com clarificação
* **ADR 0004:** **Substituído pelo ADR 0009**
* **ADR 0005:** Aceito com adendo
* **ADR 0006:** Aceito
* **ADR 0007 (NOVO):** Adotar Microkernel com Separação de Parâmetros e Regras Tarifárias
* **ADR 0008 (NOVO):** Desacoplar Processamento do Repasse Contábil em Worker Assíncrono
* **ADR 0009 (NOVO):** Implantação em Ondas Progressivas para Mitigação de Blast Radius