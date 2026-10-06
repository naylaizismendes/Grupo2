from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

CHAVE_SEGURANCA_CIDADE = b"simub-chave-seguranca-v1"


@dataclass
class Bilhete:
    cartao_id: str
    saldo: float
    nonce: int = 0

    def incrementar_nonce(self) -> int:
        self.nonce += 1
        return self.nonce


class ValidadorOnibus:
    def __init__(self, validador_id: str) -> None:
        self.validador_id = validador_id
        self.nonces_locais: set[tuple[str, int]] = set()
        self.passagens_aceitas: list[dict[str, Any]] = []

    def gerar_assinatura(self, cartao_id: str, saldo: float, nonce: int) -> str:
        mensagem = f"{cartao_id}|{saldo}|{nonce}".encode("utf-8")
        return hmac.new(CHAVE_SEGURANCA_CIDADE, mensagem, hashlib.sha256).hexdigest()

    def passar_catraca(self, bilhete: Bilhete, tarifa: float, horario: int) -> tuple[bool, str]:
        # 1. Verificação de Saldo
        if bilhete.saldo < tarifa:
            return False, "RECUSADO: saldo insuficiente"

        # 2. Débito no Chip e Incremento de Nonce
        bilhete.saldo -= tarifa
        nonce_atual = bilhete.incrementar_nonce()

        # 3. Verificação de Reutilização no mesmo ônibus
        chave_nonce = (bilhete.cartao_id, nonce_atual)
        if chave_nonce in self.nonces_locais:
            return False, "RECUSADO: nonce reutilizado localmente"

        # 4. Assinatura HMAC
        assinatura = self.gerar_assinatura(bilhete.cartao_id, bilhete.saldo, nonce_atual)

        registro = {
            "tx_id": f"{self.validador_id}:{bilhete.cartao_id}:{nonce_atual}",
            "cartao_id": bilhete.cartao_id,
            "nonce": nonce_atual,
            "validador_id": self.validador_id,
            "horario": horario,
            "tarifa": tarifa,
            "assinatura": assinatura,
        }

        self.nonces_locais.add(chave_nonce)
        self.passagens_aceitas.append(registro)
        return True, "APROVADO: viagem autorizada"


class SistemaCidadeNuvem:
    def __init__(self) -> None:
        self.transacoes_processadas: set[str] = set()
        self.nonces_globais: set[tuple[str, int]] = set()
        self.alertas_clonagem: list[str] = []
        self.saldo_contabil: float = 0.0

    def processar_lote_onibus(self, lote: list[dict[str, Any]]) -> list[str]:
        resultados = []
        for tx in lote:
            tx_id = tx["tx_id"]
            cartao_id = tx["cartao_id"]
            nonce = tx["nonce"]
            chave_global = (cartao_id, nonce)

            # A) IDEMPOTÊNCIA: Reenvio de lote por falha de rede (mesmo tx_id)
            if tx_id in self.transacoes_processadas:
                resultados.append(f"IGNORE: Transação {tx_id} já processada anteriormente (idempotente).")
                continue

            # B) DETECÇÃO DE CLONAGEM / DUPLICIDADE ENTRE ÔNIBUS DIFERENTES
            if chave_global in self.nonces_globais:
                alerta = f"ALERTA FRAUDE: Cartão {cartao_id} usou o mesmo nonce {nonce} em ônibus diferente!"
                self.alertas_clonagem.append(alerta)
                resultados.append(f"RECUSADO NA NUVEM: Clonagem detectada no cartão {cartao_id}.")
                continue

            # C) Processamento válido na nuvem
            self.transacoes_processadas.add(tx_id)
            self.nonces_globais.add(chave_global)
            self.saldo_contabil += tx["tarifa"]
            resultados.append(f"SUCESSO NUVEM: Transação {tx_id} consolidada no repasse.")

        return resultados


def executar_spike_completo():
    print("=== SPIKE REVISADO SIMUB - VALIDAÇÃO, CLONAGEM E IDEMPOTÊNCIA ===")
    print()

    # 1. Viagem Legítima (Ônibus 01)
    cartao = Bilhete(cartao_id="CARTAO-001", saldo=20.0)
    onibus_1 = ValidadorOnibus(validador_id="BUS-01")

    ok, msg = onibus_1.passar_catraca(cartao, tarifa=5.0, horario=700)
    print(f"Passagem 1 (Ônibus 1, 07h): {msg} | Saldo Restante: R${cartao.saldo:.2f}")

    # 2. Simulação de Clonagem (Cartão clonado usado no Ônibus 02 com o mesmo Nonce)
    cartao_clonado = Bilhete(cartao_id="CARTAO-001", saldo=20.0, nonce=0)  # Força o mesmo nonce=1
    onibus_2 = ValidadorOnibus(validador_id="BUS-02")

    ok_clone, msg_clone = onibus_2.passar_catraca(cartao_clonado, tarifa=5.0, horario=710)
    print(f"Passagem Clonada (Ônibus 2, 07h10): {msg_clone} | Saldo Restante: R${cartao_clonado.saldo:.2f}")
    print()

    # 3. Consolidação dos lotes na Nuvem (Descarga de dados 4G)
    nuvem = SistemaCidadeNuvem()

    print("--- Processando Lote do Ônibus 01 na Nuvem ---")
    res_nuvem_1 = nuvem.processar_lote_onibus(onibus_1.passagens_aceitas)
    for r in res_nuvem_1:
        print(r)

    print("\n--- Processando Lote do Ônibus 02 na Nuvem (Detecção de Clonagem) ---")
    res_nuvem_2 = nuvem.processar_lote_onibus(onibus_2.passagens_aceitas)
    for r in res_nuvem_2:
        print(r)

    print("\n--- Simulação de Reenvio de Lote por Falha de Rede (Idempotência) ---")
    res_reenvio = nuvem.processar_lote_onibus(onibus_1.passagens_aceitas)
    for r in res_reenvio:
        print(r)

    print("\n=== RESUMO DA OPERAÇÃO NA NUVEM ===")
    print(f"Saldo Financeiro Apurado: R${nuvem.saldo_contabil:.2f}")
    print(f"Alertas de Fraude/Clonagem: {len(nuvem.alertas_clonagem)}")
    for a in nuvem.alertas_clonagem:
        print("  ->", a)


if __name__ == "__main__":
    executar_spike_completo()