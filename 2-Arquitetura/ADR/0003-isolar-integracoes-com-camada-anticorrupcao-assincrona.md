# ADR 0003: Isolar Integrações com Camada Anticorrupção Assíncrona

**Status:** aceito

**Contexto:**
O sistema SIMUB interage com sistemas externos heterogêneos: adquirentes bancários, redes de recarga parceiras, totens e sistemas legados de prefeituras. Esses parceiros utilizam formatos proprietários (ex.: arquivos de remessa CNAB, SFTP) e possuem janelas de indisponibilidade imprevisíveis.

**Decisão:**
1. **Arquitetura Hexagonal (Capítulo 7) e Camada Anticorrupção (ACL):** Isolar os serviços externos através de portas e adaptadores. Nenhuma estrutura de dados externa contamina o modelo do domínio interno;
2. **Abordagem API-First e Modelo Canônico:** A aplicação expõe contratos REST/OpenAPI padronizados e Webhooks. Adaptadores para formatos legados específicos rodam isolados em funções Serverless;
3. **Resiliência Assíncrona:** Chamadas externas síncronas levam tempo limite (*timeout*), retentativa e disjuntor (*circuit breaker*). Remessas bancárias e reconciliações noturnas são processadas de forma assíncrona.

**Consequências:**
- *Positivas:* O domínio da bilhetagem fica totalmente protegido contra mudanças de layouts de terceiros ou instabilidade de bancos.
- *Negativas:* Necessidade de manter código de tradução nos adaptadores para cada integração proprietária.
