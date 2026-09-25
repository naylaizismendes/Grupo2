import hashlib
import hmac

# Chave de segurança usada para assinar o bilhete
CHAVE_SEGURANCA = b"senha-do-validador"


# Classe do bilhete
class Bilhete:

    def __init__(self, cartao_id: str, saldo: int, nonce: str):
        self.cartao_id = cartao_id
        self.saldo = saldo
        self.nonce = nonce
        self.assinatura = self.gerar_assinatura()

    def gerar_assinatura(self) -> str:
        # Cria uma hash segura para provar que o bilhete não é falso
        dados = f"{self.cartao_id}:{self.saldo}:{self.nonce}".encode("utf-8")
        return hmac.new(CHAVE_SEGURANCA, dados, hashlib.sha256).hexdigest()


# Validador do ônibus (OFFLINE) 
class ValidadorOnibus:

    def __init__(self, id_bus: str, cidade: str):
        self.id_bus = id_bus
        self.cidade = cidade
        self.passagens_aceitas = []

    def Passar_catraca(self, bilhete: Bilhete, valor_tarifa: int, horario: int):
        # Valida a assinatura de segurança offline
        if bilhete.gerar_assinatura() != bilhete.assinatura:
            print(f"[{self.id_bus}] BILHETE FALSO RECUSADO!")
            return False

        if bilhete.saldo < valor_tarifa:
            print(f"[{self.id_bus}] SALDO INSUFICIENTE!")
            return False

        # Guarda a viagem no validador para enviar depois
        registro = {
            "cidade": self.cidade,
            "bus": self.id_bus,
            "cartao": bilhete.cartao_id,
            "nonce": bilhete.nonce,
            "horario": horario,
        }
        self.passagens_aceitas.append(registro)
        return True


# Sistema da cidade na nuvem (célula da cidade) 
class SistemaCidadeNuvem:

    def __init__(self, nome_cidade: str, limite_fila: int):
        self.nome_cidade = nome_cidade
        self.limite_fila = limite_fila
        self.fila_recebimento = []
        self.usos_registrados = set()

    def receber_dados_do_onibus(self, dados_onibus: list):
        # Proteção de contrapressão: se a fila estourar, rejeita para não derrubar o sistema
        if len(self.fila_recebimento) + len(dados_onibus) > self.limite_fila:
            print(f" -> [Nuvem {self.nome_cidade}] SOBRECARGA! Dados rejeitados para proteger a cidade.")
            return False

        self.fila_recebimento.extend(dados_onibus)
        return True

    def processar_e_detectar_fraudes(self):
        print(f"\n--- Processando dados na nuvem de {self.nome_cidade} ---")
        while self.fila_recebimento:
            viagem = self.fila_recebimento.pop(0)
            chave_uso = f"{viagem['cartao']}:{viagem['nonce']}"

            # Verifica se o mesmo bilhete foi usado em dois ônibus diferentes offline
            if chave_uso in self.usos_registrados:
                print(f" ! ALERTA DE FRAUDE: Cartão {viagem['cartao']} foi usado 2 vezes no mesmo ciclo!")
            else:
                self.usos_registrados.add(chave_uso)
                print(f" OK: Viagem do cartão {viagem['cartao']} no ônibus {viagem['bus']} aprovada e contabilizada.")


# Execução do teste 
def rodar_demonstracao():
    print("=== TESTE DE ARQUITETURA (CASO ÔNIBUS - SAAS MULTI-CIDADE) ===")

    # Criando as cidades (células isoladas)
    nuvem_campinas = SistemaCidadeNuvem(nome_cidade="Campinas", limite_fila=10)
    nuvem_sumare = SistemaCidadeNuvem(nome_cidade="Sumaré", limite_fila=1)  # Limite pequeno para testar o estouro

    # Criando 1 bilhete com R$ 20,00 de saldo
    meu_cartao = Bilhete(cartao_id="CARD-123", saldo=2000, nonce="TICKET-001")

    # Criando dois ônibus de Campinas
    onibus1 = ValidadorOnibus(id_bus="BUS-01", cidade="Campinas")
    onibus2 = ValidadorOnibus(id_bus="BUS-02", cidade="Campinas")

    # SIMULAÇÃO 1: O passageiro passa o mesmo cartão nos dois ônibus em modo offline
    print("\n1. Passando a catraca no Ônibus 01...")
    onibus1.Passar_catraca(meu_cartao, valor_tarifa=500, horario=1000)

    print("2. Passando o mesmo cartão no Ônibus 02 (Tentativa de Fraude)...")
    onibus2.Passar_catraca(meu_cartao, valor_tarifa=500, horario=1010)

    # SIMULAÇÃO 2: Os ônibus chegam na garagem e descarregam os dados na nuvem de Campinas
    nuvem_campinas.receber_dados_do_onibus(onibus1.passagens_aceitas)
    nuvem_campinas.receber_dados_do_onibus(onibus2.passagens_aceitas)

    # A nuvem de Campinas processa e pega a fraude
    nuvem_campinas.processar_e_detectar_fraudes()

    # SIMULAÇÃO 3: Testando o Isolamento de Cidades (Envelope D)
    print("\n--- Testando se a sobrecarga de uma cidade afeta a outra ---")
    dados_demais = [
        {"cartao": "C1", "nonce": "N1"},
        {"cartao": "C2", "nonce": "N2"},
    ]
    # Sumaré vai estourar o limite e rejeitar
    nuvem_sumare.receber_dados_do_onibus(dados_demais)

    # Verificando se Campinas continua funcionando normalmente mesmo com Sumaré falhando
    print(f"Status da nuvem de Campinas: {len(nuvem_campinas.fila_recebimento)} pendências. (Funciona perfeitamente!)")
    print("\n=== TESTE CONCLUÍDO ===")


if __name__ == "__main__":
    rodar_demonstracao()






=== TESTE DE ARQUITETURA (CASO ÔNIBUS - SAAS MULTI-CIDADE) ===

1. Passando a catraca no Ônibus 01...
2. Passando o mesmo cartão no Ônibus 02 (Tentativa de Fraude)...

--- Processando dados na nuvem de Campinas ---
OK: Viagem do cartão CARD-123 no ônibus BUS-01 aprovada e contabilizada.
! ALERTA DE FRAUDE: Cartão CARD-123 foi usado 2 vezes no mesmo ciclo!

--- Testando se a sobrecarga de uma cidade afeta a outra ---
-> [Nuvem Sumaré] SOBRECARGA! Dados rejeitados para proteger a cidade.
Status da nuvem de Campinas: 0 pendências. (Funciona perfeitamente!)

=== TESTE CONCLUÍDO ===

