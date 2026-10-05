# ADR 0008: Desacoplar Processamento do Repasse Contábil em Worker Assíncrono

**Status:** aceito — substitui parcialmente o escopo de execução do ADR 0001

**Contexto:**
O ADR 0001 definiu a adoção de um Monólito Modular para concentrar validação, recargas e repasse financeiro dentro do processo da célula municipal. Conforme apontado na Leitura Cruzada (Grupo 03), a execução do fechamento mensal de repasse — que reprocessa em lote o fluxo de eventos de viagens do mês — dentro do mesmo processo das transações em tempo real pode gerar contenção de CPU, memória e disputa no pool de conexões JDBC durante picos de recarga.

**Decisão:**
Desacoplar a execução do subdomínio de *Repasse e Conciliação Contábil* do processo transacional da bilhetagem:
1. **Mesma Base de Código, Processos Isolados:** O código do módulo de repasse permanece no mesmo repositório do Monólito Modular, mas passa a ser empacotado para subir num container **Worker Assíncrono (Job Batch)** separado no nível do sistema operacional;
2. **Controle de Concorrência JDBC:** O container do *Worker de Repasse* executa com limite estrito de conexões ao banco relacional (`max_connections=5`) e processa os eventos em lotes paginados, sendo agendado preferencialmente para janelas de baixo tráfego (madrugada);
3. **Isolamento de Impacto:** Falhas de memória ou picos de carga durante a conciliação mensal no *Worker* não afetam a disponibilidade das APIs de recarga nem a sincronização dos ônibus.

**Consequências:**
- *Positivas:* Elimina a disputa de recursos transacionais entre o fechamento mensal e a operação de bilhetagem em tempo real.
- *Negativas:* Adiciona mais uma unidade de implantação (*Worker*) para ser orquestrada na infraestrutura da célula.
