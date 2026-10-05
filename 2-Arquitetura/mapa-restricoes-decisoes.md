# Mapa de Restrições e Decisões — SIMUB

**Projeto:** SIMUB — Sistema Integrado de Mobilidade e Bilhetagem Urbana  
**Grupo:** 02  
**Caso:** Ônibus — Bilhetagem e Mobilidade Urbana (Caso 1)  
**Envelope:** D — Várias cidades, 25 desenvolvedores, nuvem pública multirregião  
**Data da Revisão:** Outubro de 2026  
**Referência Metodológica:** ABREU, Douglas H. S. *Estilos Arquiteturais de Software: guia de consulta*, 2026.

---

## Introdução
Este documento estabelece o mapeamento bidirecional e rastreável entre as **restrições do Envelope D**, os **requisitos do Caso Ônibus** e as **decisões arquiteturais** adotadas pelo Grupo 02. Cada restrição e requisito é atendido por ao menos uma decisão registrada em ADR e ilustrada nos diagramas C4 (Contexto, Contêineres e Componentes).

---

## Parte A — Restrições do Envelope D (Várias cidades, 25 devs, nuvem pública multirregião)

| # | Restrição do Envelope D | Decisão Arquitetural que a Atende | ADR Sustentador | Diagrama Sustentador |
|---|---|---|---|---|
| **E1** | Operação em várias cidades com isolamento total de falhas (*Blast Radius Zero*) | Adotar **Arquitetura Celular (Capítulo 13)**: cada município opera em uma célula autônoma e isolada na nuvem pública, possuindo seu próprio banco relacional e mensageria. | ADR 0001 | Nível 2 (Contêineres) |
| **E2** | Equipe enxuta de 25 desenvolvedores (sem time dedicado de plataforma) | Adotar **Monólito Modular (Capítulo 6)** dentro de cada célula em vez de dezenas de microsserviços por cidade, contendo o custo de observabilidade e deploy distribuído. | ADR 0001 | Nível 2 (Contêineres) e Nível 3 (Componentes) |
| **E3** | Nuvem pública multirregião com deploy sem paralisação e sem risco global | **Implantação em Ondas Progressivas (*Progressive Rollout*)** em etapas (1, 3, 10, N cidades) com *rollback* automático por célula em caso de erro sintético. | ADR 0009 *(substitui ADR 0004)* | Nível 2 (Contêineres) |
| **E4** | Atendimento a municípios com portes e volumes muito distintos (200k a 3M hab.) | Escalonamento independente por célula e uso de **Serverless / FaaS (Capítulo 12)** com concorrência provisionada no pico para consultas públicas sem custo ocioso no vale. | ADR 0001, ADR 0009 | Nível 2 (Contêineres) |
| **E5** | Heterogeneidade de sistemas legados municipais e adquirentes locais | **Arquitetura Hexagonal (Capítulo 7)** e **Camada Anticorrupção (ACL)** em funções FaaS isoladas, utilizando contrato API-First e Modelo Canônico. | ADR 0003 | Nível 1 (Contexto) e Nível 3 (Componentes) |

---

## Parte B — Requisitos que Apertam do Caso Ônibus

| # | Subdomínio / Requisito que Aperta | Decisão Arquitetural que a Atende | ADR Sustentador | Diagrama Sustentador |
|---|---|---|---|---|
| **C1** | Validação embarcada: resposta na catraca em até 300 ms mesmo offline (até 4h sem 4G) | **Autorização local embarcada**: lista em memória no validador e **Dual-Ledger (Controle de Saldo Híbrido)** com a conta na nuvem como autoridade final. | ADR 0005, ADR 0006 | Nível 2 (Contêineres) |
| **C2** | Fraude de recarga zero e conciliação bancária | Protocolo de **`OrdemDeCreditoID` sequencial** no chip do cartão inteligente e conciliação assíncrona desacoplada via ACL. | ADR 0003, ADR 0005 | Nível 2 (Contêineres) e Nível 3 (Componentes) |
| **C3** | Detecção de clonagem física de cartão e uso concorrente offline | Assinatura HMAC de par **`ID_Cartao:Contador_Sequencial`** no chip para prova determinística no servidor e análise cinemática de GPS secundária. | ADR 0005, ADR 0006 | Nível 3 (Componentes) |
| **C4** | Ingestão contínua de telemetria (80 pos/s a 400 pos/s no pico) sem travar bilhetagem | **Desacoplamento por Kafka/Redpanda** com consumidor em *thread-pool* isolado (*bulkhead*) gravando em banco de séries temporais (*TimescaleDB/Redis*). | ADR 0001 | Nível 2 (Contêineres) e Nível 3 (Componentes) |
| **C5** | Reajustes e decretos tarifários municipais frequentes sem parada do sistema | **Microkernel Tarifário (Capítulo 8)** com separação estrita entre parâmetros cadastrais no banco (sem deploy) e plugins compilados para algoritmos divergentes. | ADR 0007 | Nível 3 (Componentes) |
| **C6** | Repasse mensal recalculável com regras de tarifas vigentes na data da viagem | **Event Sourcing no Financeiro (Capítulo 15)** com tabela relacional *append-only* e versionamento imutável de apurações ($V_1, V_2, \dots$). | ADR 0002 | Nível 3 (Componentes) |
| **C7** | Prevenção de disputa de recursos entre o fechamento do repasse e o rush | **Desacoplamento do Repasse Contábil em *Worker Assíncrono* (Job Batch)** com limite estrito de conexões JDBC e processamento paginado noturno. | ADR 0008 *(substitui escopo do ADR 0001)* | Nível 3 (Componentes) |
| **C8** | Direito ao esquecimento (LGPD) em histórico contábil imutável por 30 dias | **Pseudonimização com Tokens Opacos** no Event Store e *Crypto-Shredding* de identificadores civis sem afetar atributos regulatórios de subsídio. | ADR 0002, ADR 0005 | Nível 3 (Componentes) |

---

## Parte C — Cobertura Reversa dos ADRs (Todos os ADRs Atendem ao Menos uma Restrição)

| ADR | Restrições e Requisitos Atendidos |
|---|---|
| **ADR 0001** — Compor Arquitetura Celular com Monólito Modular e Serverless | E1, E2, E4, C4 |
| **ADR 0002** — Banco por Serviço e Event Sourcing no Repasse Contábil | C6, C8 |
| **ADR 0003** — Isolar Integrações com Camada Anticorrupção Assíncrona | E5, C2 |
| **ADR 0004** — *(Substituído pelo ADR 0009)* | E3 |
| **ADR 0005** — Dual-Ledger e Resolução de Conflitos no Servidor | C1, C2, C3, C8 |
| **ADR 0006** — Validação Offline no Embarcado e Deduplicação no Servidor | C1, C3 |
| **ADR 0007** — Microkernel com Separação de Parâmetros e Regras Tarifárias | C5 |
| **ADR 0008** — Desacoplar Processamento do Repasse Contábil em Worker Assíncrono | C7 |
| **ADR 0009** — Implantação em Ondas Progressivas para Mitigação de Blast Radius | E3, E4 |
