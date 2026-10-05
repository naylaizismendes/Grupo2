# Documento de Arquitetura de Software — SIMUB (Sistema Integrado de Mobilidade e Bilhetagem Urbana)
 
**Grupo:** 02  
**Caso:** Ônibus — Bilhetagem e Mobilidade Urbana (Caso 1)  
**Envelope:** D — Várias cidades, 25 desenvolvedores, nuvem pública multirregião  
**Entrega:** 5 — Versão Final Pós-Leitura Cruzada  
**Data da Revisão:** Outubro de 2026  

---

## 1. Identificação e Escopo

O sistema SIMUB é uma plataforma *SaaS multi-tenant* projetada para gerenciar a operação de bilhetagem eletrônica, controle de frotas, recargas e repasse contábil de transporte público em múltiplos municípios independentes.

O **Envelope D** impõe restrições severas de operação e dimensionamento:
- **Operação Multi-Cliente:** O sistema é vendido para municípios de portes diversos (de 200 mil a 3 milhões de habitantes).
- **Contenção do Raio de Impacto (*Blast Radius Zero*):** Uma falha crítica de software, sobrecarga de tráfego ou corrupção de dados na operação de uma cidade **nunca** pode afetar a operação de outra cidade cliente.
- **Equipe Enxuta:** A equipe é composta por **25 desenvolvedores**, sem time dedicado de infraestrutura/SRE.
- **Ambiente:** Nuvem pública multirregião.

A arquitetura adota a **Arquitetura Celular (Capítulo 13)** combinada com **Monólito Modular (Capítulo 6)** por célula e **Serverless (Capítulo 12)** para consultas públicas.

---

## 2. Visão Geral da Composição de Estilos

| Estilo | Onde vale (fronteira) | Onde termina | ADR |
|---|---|---|---|
| **Arquitetura Celular** (cap. 13) | Borda do sistema e segregação por município cliente (*tenant*) | Não entra no interior do domínio da célula | 0001 |
| **Monólito Modular** (cap. 6) | Núcleo de processamento (*Core*) de cada célula municipal | Não se estende às consultas públicas de alta escala | 0001 |
| **Serverless / FaaS** (cap. 12) | Serviço de consultas públicas de itinerários e previsões | Não é usado em rotas transacionais de bilhetagem | 0001, 0009 |
| **Microkernel** (cap. 8) | Motor de tarifação e conciliação de regras municipais | Não afeta a camada de persistência relacional | 0007 |
| **Worker Assíncrono** | Execução do fechamento mensal de repasse contábil em lote | Não afeta as chamadas transacionais de bordo | 0008 |
| **Event Sourcing** (cap. 15) | Tabela *append-only* do subdomínio de repasse contábil | Não entra no cadastro nominativo de cartões | 0002 |
| **Hexagonal / ACL** (cap. 7) | Isolamento de integrações com bancos, adquirentes e legados | Não contamina os modelos de domínio internos | 0003 |

---

## 3. Diagramas da Arquitetura (C4 Model)

### 3.1 Nível 1 — Contexto
![Nível 1 — Contexto](c4-contexto.png)
*Figura 1: Diagrama de Contexto (Nível 1 C4). O SIMUB conecta passageiros, motoristas e auditores municipais a adquirentes e sistemas estatais.*

### 3.2 Nível 2 — Contêineres (Arquitetura Celular)
![Nível 2 — Contêineres](c4-conteineres.png)
*Figura 2: Diagrama de Contêineres (Nível 2 C4). O Roteador de Células isola o tráfego de cada município em instâncias independentes (Blast Radius Zero).*

### 3.3 Nível 3 — Componentes do Core da Célula
![Nível 3 — Componentes](c4-componentes.png)
*Figura 3: Diagrama de Componentes (Nível 3 C4). Estrutura interna do Monólito Modular da Célula, com o Microkernel Tarifário e conectores desacoplados.*

---

## 4. As Cinco Respostas Obrigatórias do Caso

### 4.1 Como o validador aceita a passagem sem rede, e como o sistema descobre depois que a mesma passagem foi usada em dois ônibus?
**Resposta:**  
1. O validador embarcado decide localmente em **até 300 ms** contra uma *denylist* mantida em memória no dispositivo.
2. Cada validação gera um registro assinado com o par `(ID_Cartao, Contador_Sequencial)` e o saldo é debitado diretamente do chip do cartão (ADR 0005, ADR 0006).
3. Ao reconectar via 4G (até 4h depois), os lotes são enviados ao servidor. A deduplicação é idempotente por `tx_id`.
4. Se o mesmo cartão for clonado e usado em dois ônibus offline, o servidor identifica a duplicidade do `Contador_Sequencial` e gera o bloqueio do cartão e a retenção do repasse no fechamento.

### 4.2 Como o saldo do cartão fica consistente entre recarga no aplicativo e uso no ônibus, com atraso de sincronização?
**Resposta:**  
1. A conta central na nuvem é a **única autoridade definitiva do saldo** (Dual-Ledger, ADR 0005).
2. As recargas no app geram ordens numéricas sequenciais (`OrdemDeCreditoID`).
3. Ao encostar na catraca, o validador lê o `UltimoCreditoAplicadoID` no chip do cartão e aplica o crédito pendente apenas se o ID for superior, impedindo dupla aplicação em validadores offline.
4. Para contingência de saldo zerado, o validador admite **1 tarifa negativa (saldo de confiança)**, abatida obrigatoriamente no próximo carregamento.

### 4.3 Como a telemetria escala no pico sem derrubar o restante do sistema?
**Resposta:**  
1. A ingestão de telemetria é recebida pelo *Roteador de Células* e enviada ao tópico Kafka da célula.
2. O consumidor de telemetria roda no *Core* da célula em um ***thread-pool* isolado (*bulkhead*)**, gravando exclusivamente em base de séries temporais (*TimescaleDB/Redis*).
3. Essa ingestão não consome o *pool* JDBC do banco relacional de bilhetagem, garantindo que picos de 400 posições/s não afetem as recargas nem o repasse (ADR 0001).

### 4.4 Como o repasse mensal é recalculado se uma regra de tarifa mudou no meio do mês?
**Resposta:**  
1. O fechamento é executado em lote por um ***Worker Assíncrono* isolado** (ADR 0008) fora do horário de pico.
2. O motor utiliza o **Microkernel Tarifário** (ADR 0007): parâmetros de valores e datas de vigência ficam na base relacional e não exigem deploy de código.
3. Ao recalcular o mês com vigência retroativa, os eventos de viagem no *Event Store* (ADR 0002) são reprocessados[cite: 31, 39]. O resultado gera uma nova versão imutável do documento de apuração ($V_2$) e emite um relatório automático de ajuste contábil (débito/crédito) sem apagar o faturamento anterior ($V_1$).

### 4.5 Como o histórico de viagens de uma pessoa é apagado quando ela pede, sem quebrar a conciliação financeira?
**Resposta:**  
1. O *Event Store* mantém os registros de viagem com **tokens opacos pseudonimizados**.
2. Os dados civis do titular ficam isolados na tabela de cadastro nominativo.
3. Ao receber o pedido da LGPD, executa-se o *crypto-shredding* da chave do titular[cite: 34]. O cidadão torna-se inidentificável, mas os atributos regulatórios de subsídio (ex.: "Beneficiário Estudante") e os valores financeiros permanecem matematicamente intactos no *Event Store* para auditoria pública (ADR 0002, ADR 0005).

---

## 5. Rastreabilidade de Restrições e Decisões

Consulte o arquivo [`mapa-restricoes-decisoes.md`](mapa-restricoes-decisoes.md) para a matriz completa entre restrições do Envelope D, requisitos do caso, ADRs e diagramas C4.

---

## 6. Registros de Decisões de Arquitetura (ADRs)

Os ADRs da solução estão versionados individualmente na pasta [`ADR/`](ADR/)
- **ADR 0001:** Compor Arquitetura Celular com Monólito Modular e Serverless *(Parcialmente substituído pelo ADR 0008)*
- **ADR 0002:** Banco por Serviço e Event Sourcing no Repasse Contábil *(Aceito com adendo)*
- **ADR 0003:** Isolar Integrações com Camada Anticorrupção Assíncrona *(Aceito)*
- **ADR 0004:** Operar em Nuvem com Deploy Canary *(Substituído pelo ADR 0009)*
- **ADR 0005:** Dual-Ledger e Resolução de Conflitos no Servidor *(Aceito com adendo)*
- **ADR 0006:** Validação Offline no Embarcado e Deduplicação no Servidor *(Aceito)*
- **ADR 0007 (NOVO):** Adotar Microkernel com Separação de Parâmetros e Regras Tarifárias *(Aceito)*
- **ADR 0008 (NOVO):** Desacoplar Processamento do Repasse Contábil em Worker Assíncrono *(Aceito)*
- **ADR 0009 (NOVO):** Implantação em Ondas Progressivas para Mitigação de Blast Radius *(Aceito)*