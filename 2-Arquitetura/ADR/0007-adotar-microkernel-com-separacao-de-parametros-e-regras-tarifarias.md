# ADR 0007: Adotar Microkernel com Separação de Parâmetros e Regras Tarifárias

**Status:** aceito

**Contexto:**
O sistema SIMUB opera sob o Envelope D, atendendo múltiplos municípios com legislações e políticas tarifárias independentes. Reajustes de valores de tarifas, percentuais de subsídio e faixas de integração ocorrem por decretos municipais frequentes. Alterar o código da aplicação a cada mudança de centavos na tarifa sujeitaria simples reajustes administrativos aos ciclos de deploy em ondas.

**Decisão:**
Adotar o estilo **Microkernel (Capítulo 8)** no *Núcleo Financeiro*, aplicando a separação entre parâmetros e algoritmos:
1. **Tabelas de Parâmetros Tarifários (Sem Deploy):** Valores de tarifas, percentuais de desconto e janelas de integração temporal passam a ser geridos como **dados versionados na base de dados da célula municipal**, alteráveis via Portal do Gestor em tempo de execução;
2. **Plugins de Algoritmos (Microkernel):** O motor do Microkernel expõe o contrato `IRegraTarifaria`. Plugins de código compilado são utilizados exclusivamente quando um município adota um modelo de cálculo de estrutura lógica divergente (ex.: tarifação por zonas geográficas vs. tarifação por integração temporal contínua).

**Consequências:**
- *Positivas:* Alterações administrativas de tarifas entram em vigor instantaneamente na data configurada sem exigir deploy de código.
- *Negativas:* Exige a manutenção de esquemas rigorosos de versionamento de parâmetros por cidade.
