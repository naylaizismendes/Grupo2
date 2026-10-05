# ADR 0009: Implantação em Ondas Progressivas para Mitigação de Blast Radius

**Status:** aceito — substitui integralmente o ADR 0004

**Contexto:**
O ADR 0004 estabelecia a estratégia de deploy Canary com uma única cidade piloto e a promoção automática para todas as demais células municipais restantes após 60 minutos. A Leitura Cruzada (Grupo 03 e Grupo 08) demonstrou que essa estratégia constituía um "Big Bang diferido", pois um defeito no código que só se manifestasse sob regras tarifárias ou volumes específicos de outros municípios atingiria todas as cidades restantes de forma simultânea.

**Decisão:**
Substituir a estratégia de etapa única por um modelo de **Implantação em Ondas Progressivas (*Progressive Rollout*)**:
1. **Ondas de Tamanho Crescente:** O deploy de uma nova versão da plataforma é fatiado em etapas sucessivas:
   - *Onda 1 (Piloto):* 1 cidade de porte médio sob monitoramento sintético por 30 minutos;
   - *Onda 2 (Diversidade de Configuração):* 3 cidades com modelos de regras tarifárias e integrações distintas;
   - *Onda 3 (Escala Intermediária):* 10 cidades do portfólio;
   - *Onda 4 (Conclusão):* Restante das células municipais;
2. **Corte Automático (*Rollback*):** A esteira monitora automaticamente as métricas de saúde da célula (taxa de erros $HTTP\ 5xx > 0.1\%$ ou latência $p99 > 500	ext{ ms}$). Caso uma métrica seja violada em qualquer onda, a promoção é interrompida imediatamente e a versão anterior é restaurada nas células afetadas (*rollback* isolado).

**Consequências:**
- *Positivas:* Garante que qualquer falha não detectada fique contida numa fração reduzida da base de clientes (preservando o princípio de *Blast Radius Zero* do Envelope D).
- *Negativas:* Aumenta o tempo total necessário para a conclusão do ciclo completo de implantação de uma nova versão em todas as cidades.
