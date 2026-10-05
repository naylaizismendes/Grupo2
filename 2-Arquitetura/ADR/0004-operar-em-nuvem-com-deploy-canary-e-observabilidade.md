# ADR 0004: Operar em Nuvem com Deploy Canary e Observabilidade

**Status:** substituído pelo ADR 0009

**Contexto:**
A operação em nuvem pública multirregião sob o Envelope D exige uma estratégia de implantação de atualizações sem paralisação da bilhetagem e com rápida detecção de falhas.

**Decisão Original:**
Implantar atualizações via deploy Canary selecionando uma cidade piloto, mantendo monitoração por 60 minutos e promovendo a versão nova para todas as demais células após aprovação.

**Motivo da Substituição:**
A Leitura Cruzada (Objeções do Grupo 03 e Grupo 08) demonstrou que promover a versão nova para *todas* as cidades restantes de uma só vez equivalia a um "Big Bang diferido". Se um bug dependesse de configurações exclusivas de outros municípios, afetaria todas as células restantes simultaneamente.

**Substituído por:** **ADR 0009 (Implantação em Ondas Progressivas para Mitigação de Blast Radius)**.
