# ADR 0001: Compor Arquitetura Celular com Monólito Modular e Serverless

**Status:** aceito — parcialmente substituído pelo ADR 0008

**Contexto:**
O sistema SIMUB precisa atender múltiplos municípios sob o Envelope D (várias cidades, 25 desenvolvedores, nuvem pública multirregião). As cidades possuem cargas e volumes distintos, e uma falha na operação de um município não pode afetar os demais. Além disso, a equipe reduzida de 25 desenvolvedores impede a gestão de dezenas de microsserviços distribuídos independentes por cidade.

**Decisão:**
Adotar a **Arquitetura Celular (Capítulo 13)** combinada com **Monólito Modular (Capítulo 6)** e **Serverless (Capítulo 12)**:
1. **Isolamento por Célula:** Cada município cliente é implantado em uma célula isolada na nuvem pública, contendo seu próprio banco de dados relacional e infraestrutura gerenciada;
2. **Monólito Modular Interno:** As operações do núcleo de bilhetagem (validação, recargas, cadastro e liquidação) são mantidas dentro de um Monólito Modular por célula, divididas em módulos com limites de domínio claros;
3. **Serverless para Consultas:** Consultas públicas de passageiros (horários e itinerários) utilizam funções Serverless escaláveis alimentadas por projeções em cache (Redis).

**Alternativas consideradas:**
- *Microsserviços Distribuídos:* Descartada por gerar um custo operacional de infraestrutura e observabilidade insustentável para 25 desenvolvedores.
- *Monólito Global Compartilhado (Multi-Tenant em Banco Único):* Descartada por violar a contenção de raio de impacto (*blast radius*).

**Consequências:**
- *Positivas:* Falhas em uma cidade ficam 100% contidas na sua célula; facilidade de manutenção do código do monólito pela equipe.
- *Negativas:* Replicação de custos fixos de infraestrutura por célula municipal; necessidade de orquestração de deploys multi-célula.
