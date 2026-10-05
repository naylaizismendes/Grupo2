# ADR 0006: Validar Offline no Embarcado e Deduplicar a Passagem no Servidor

**Status:** aceito

**Contexto:**
Com 1.200 validadores operando simultaneamente, picos de embarque no horário do rush (120 validações/s) não podem depender de chamadas síncronas de rede ao servidor central para autorizar a catraca.

**Decisão:**
1. **Decisão Local Embarcada:** O validador consulta uma lista local de cartões bloqueados (*denylist*) mantida em memória e autoriza o passageiro em até 300 ms;
2. **Deduplicação no Servidor:** O validador grava as passagens aceitas numa fila local assinada. Ao reconectar, envia o lote ao *Serviço de Validação* da célula;
3. **Idempotência:** O servidor utiliza o identificador único da transação `(ValidadorID, CartaoID, Nonce, Timestamp)` para descartar retransmissões de rede sem rejeitar o lote de viagens legítimas.

**Consequências:**
- *Positivas:* Alta disponibilidade da catraca no ônibus; imunidade a oscilações da rede 4G urbana.
- *Negativas:* Riscos de uso indevido durante a janela offline contidos pelos limites da lista local e política do sistema.
