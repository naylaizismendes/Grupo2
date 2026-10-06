# Spike — ADR 0005, ADR 0006 e Deduplicação / Validação Embarcada

## O que este programa prova

Este spike valida em código funcional os conceitos definidos nas ADRs do SIMUB após as revisões da Leitura Cruzada (Entrega 5):

1. **Débito no Chip do Cartão:** A catraca subtrai o valor da tarifa diretamente do saldo local do cartão inteligente ao autorizar o embarque offline.
2. **Identificador Monotônico por Nonce:** Cada uso do cartão incrementa um contador sequencial no chip (`nonce`), gerando uma assinatura HMAC válida e única.
3. **Viagens Legítimas em Horários Distintos:** Permite viagens repetidas do mesmo cartão no mesmo veículo (ex.: ida às 07h e volta às 18h) sem gerar falsos alertas de fraude.
4. **Idempotência no Processamento em Lote:** O reenvio do lote de validações por falhas de rede (politica *at-least-once*) é tratado no servidor sem duplicar os lançamentos contábeis.

## Como executar

Requisito: **Python 3.12+**.

Execute no terminal:

```bash
python3 codigo_spike.py
```

A saída esperada está registrada no arquivo `saida-esperada.txt`.
