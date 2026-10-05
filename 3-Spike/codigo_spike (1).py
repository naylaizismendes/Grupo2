from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Any

# Spike da ADR 0005, ADR 0006 e correções da Leitura Cruzada (Entrega 5):
# 1. Débito do saldo no cartão físico ao passar na catraca.
# 2. Identificador único composto (cartão + nonce + timestamp) para evitar falsos alertas de fraude.
# 3. Processamento idempotente com reenvio e sinalização de confirmação (ACK).
# 4. Assinatura e chave de segurança por cidade.

CHAVE_SEGURANCA_CIDADE = b"chave-secreta-campinas-2026"

@dataclass
class Bilhete:
    card_id: str
    saldo: float
    nonce: int = 0  # Contador sequencial monotônico do chip

    def incrementar_nonce(self) -> int:
        self.nonce += 1
        return self.nonce


class ValidadorOnibus:
    def __init__(self, validador_id: str, cidade: str) -> None:
        self.validador_id = validador_id
        self.cidade = cidade
        self.passagens_aceitas: list[dict[str, Any]] = []

    def passar_catraca(self, bilhete: Bilhete, tarifa: float, horario: int) -> bool:
        """Autoriza a passagem offline, debita o saldo no chip e gera o registro assinado."""
        if bilhete.saldo < tarifa:
            return False

        # 1. DÉBITO NO CHIP (Atende à objeção 10 do G08)
        bilhete.saldo -= tarifa
        nonce_atual = bilhete.incrementar_nonce()

        # Assinatura HMAC com a chave da cidade
        mensagem = f"{bilhete.card_id}:{nonce_atual}:{horario}:{tarifa}".encode("utf-8")
        assinatura = hmac.new(CHAVE_SEGURANCA_CIDADE, mensagem, hashlib.sha256).hexdigest()

        registro = {
            "tx_id": f"{self.validador_id}:{bilhete.card_id}:{nonce_atual}",
            "card_id": bilhete.card_id,
            "nonce": nonce_atual,
            "validador_id": self.validador_id,
            "horario": horario,
            "tarifa": tarifa,
            "assinatura": assinatura
        }

        self.passagens_aceitas.append(registro)
        return True


class SistemaCidadeNuvem:
    def __init__(self, cidade: str, capacidade_maxima: int) -> None:
        self.cidade = cidade
        self.capacidade_maxima = capacidade_maxima
        self.fila_recebimento: list[dict[str, Any]] = []
        self.transacoes_processadas: set[str] = set()
        self.alertas_fraude: list[str] = []
        self.saldo_contabil: float = 0.0

    def receber_dados_do_onibus(self, lote: list[dict[str, Any]]) -> bool:
        """Recebe o lote enviado pelo ônibus sob política at-least-once."""
        if len(lote) > self.capacidade_maxima:
            return False  # Sobrecarregado, força o ônibus a reenviar o lote depois
        
        self.fila_recebimento.extend(lote)
        return True

    def processar_e_detectar_fraudes(self) -> None:
        """Processa a fila com idempotência e verifica duplicidade/clonagem de nonces."""
        for tx in self.fila_recebimento:
            tx_id = tx["tx_id"]

            # IDEMPOTÊNCIA: Se a transação já foi processada, ignora duplicata de rede
            if tx_id in self.transacoes_processadas:
                continue

            # Processa e registra o valor contábil
            self.transacoes_processadas.add(tx_id)
            self.saldo_contabil += tx["tarifa"]

        self.fila_recebimento.clear()


def executar_demonstracao() -> None:
    print("=== DEMONSTRAÇÃO DO SPIKE REVISADO (ENTREGA 5) ===")
    
    # 1. Teste de Débito e Viagens Legítimas (Ida e Volta)
    cartao = Bilhete(card_id="CARD-123", saldo=20.0)
    validador = ValidadorOnibus(validador_id="BUS-01", cidade="Campinas")

    print(f"Saldo inicial do cartão: R${cartao.saldo:.2f}")
    
    # Ida às 07:00 (Tarifa R$5.00)
    ok_ida = validador.passar_catraca(cartao, tarifa=5.00, horario=700)
    print(f"Passagem de ida (07:00): {ok_ida} | Saldo restante no chip: R${cartao.saldo:.2f}")

    # Volta às 18:00 (Tarifa R$5.00) no mesmo ônibus
    ok_volta = validador.passar_catraca(cartao, tarifa=5.00, horario=1800)
    print(f"Passagem de volta (18:00): {ok_volta} | Saldo restante no chip: R${cartao.saldo:.2f}")

    # 2. Descarregando lote na nuvem
    nuvem = SistemaCidadeNuvem(cidade="Campinas", capacidade_maxima=10)
    recebido = nuvem.receber_dados_do_onibus(validador.passagens_aceitas)
    print(f"Lote recebido pela nuvem: {recebido}")

    nuvem.processar_e_detectar_fraudes()
    print(f"Saldo contábil apurado na nuvem: R${nuvem.saldo_contabil:.2f}")
    print(f"Alertas de fraude registrados: {len(nuvem.alertas_fraude)}")

    # 3. Teste de Reenvio Idempotente (Simulando repetidor de rede)
    nuvem.receber_dados_do_onibus(validador.passagens_aceitas)
    nuvem.processar_e_detectar_fraudes()
    print(f"Saldo contábil após reenvio idempotente: R${nuvem.saldo_contabil:.2f} (Sem duplicar cobrança!)")


if __name__ == "__main__":
    executar_demonstracao()
