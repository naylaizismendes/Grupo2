# ADR 0005: Dual-Ledger e Resolução de Conflitos no Servidor

**Status:** aceito (com adendos de controle)

**Contexto:**
A validação embarcada nos ônibus deve responder em até 300 ms mesmo quando o veículo opera em zonas cegas de rede 4G (até 4 horas desconectado). O passageiro pode efetuar recargas no aplicativo enquanto o ônibus está desconectado.

**Decisão:**
1. **Controle de Saldo Híbrido (Dual-Ledger):** O cartão físico armazena o saldo num setor seguro cifrado para autorização offline rápida. A conta central na nuvem é a **única autoridade definitiva do saldo**;
2. **Deduplicação por Contador Monotônico:** Cada validação offline assina o par `(ID_Cartao, Contador_Sequencial)` e o armazena em fila persistente no validador;
3. **Reconciliação no Servidor:** Ao reconectar, o validador descarrega os lotes. O servidor aplica os débitos de forma idempotente e atualiza o saldo autoritário central.

**Adendos Pós-Leitura Cruzada (Entrega 5):**
- *Prevenção de Dupla Recarga:* As ordens de recarga possuem um `OrdemDeCreditoID` sequencial. O validador grava no chip o `UltimoCreditoAplicadoID` e só aplica a recarga se o ID for superior;
- *Saldo de Confiança:* Restrito ao teto de **1 tarifa negativa** (saldo máximo de $-1 	imes 	ext{Tarifa Base}$). O débito é automaticamente abatido na recarga seguinte.

**Consequências:**
- *Positivas:* Embarque imediato em 300 ms sem dependência de rede 4G; proteção contra fraudes de recarga e clonagem física.
- *Negativas:* Existência de janela de consistência eventual entre o saldo no chip e a conta central durante a desconexão.
