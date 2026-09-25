#  Validador de Bilhetes Offline & Nuvem (SaaS Multi-Cidade)

Este projeto é uma **demonstração prática de arquitetura de software** voltada a um sistema de bilhetagem eletrônica para transporte público. O código simula o funcionamento de validadores offline em ônibus e o processamento assíncrono em uma nuvem descentralizada e *multi-tenant*.

---

##  Visão Geral

Em redes de transporte público, os validadores das catracas operam sem conectividade garantida à internet (modo offline). Essa condição exige soluções para três problemas fundamentais:

1. **Autenticação Descentralizada:** Validar a autenticidade do bilhete no próprio ônibus sem consultar um servidor central.
2. **Prevenção de Fraudes (*Replay Attack / Duplo Gasto*):** Evitar reutilização ilícita do mesmo bilhete com mesmo saldo em múltiplos veículos antes da sincronização.
3. **Isolamento de Tenancy (*Cell-based Architecture*):** Impedir que uma sobrecarga ou falha no sistema de uma cidade afete a operação de outras.

O projeto resolve esses cenários combinando **HMAC-SHA256**, **descarregamento assíncrono para detecção de fraudes na nuvem** e **mecanismo de contrapressão (*backpressure*)**.

---

##  O Que Este Código Prova?

* **Validação Criptográfica Offline:** O validador local verifica a integridade do bilhete recalculando a assinatura HMAC em tempo real, sem necessidade de chamadas de API.
* **Detecção Diferida de Fraude:** Caso um mesmo bilhete com o mesmo `nonce` seja passado em dois ônibus offline, o evento é aceito localmente na catraca, mas a fraude é detectada e sinalizada no momento da ingestão de dados na nuvem.
* **Arquitetura Orientada a Células:** O isolamento entre as instâncias das cidades garante resiliência total; falhas em um tenant não se propagam pela rede.
* **Proteção contra Sobrecarga (*Backpressure*):** A nuvem rejeita pacotes de dados que ultrapassam os limites configurados da fila para preservar a estabilidade da aplicação.

---

##  Arquitetura e Conceitos

* **`Bilhete`**: Representa o cartão do usuário. Contém `cartao_id`, `saldo`, `nonce` e o parâmetro `assinatura` gerado via `HMAC-SHA256`.
* **`ValidadorOnibus`**: Componente offline acoplado à catraca. Executa a validação da hash e do saldo local, registrando as viagens em buffer interno.
* **`SistemaCidadeNuvem`**: Serviço backend isolado por tenant. Processa os lotes recebidos e realiza validações em $O(1)$ utilizando um `set` de chaves compostas (`cartao:nonce`).

---

##  Pré-requisitos

* **Python 3.8** ou superior.
* Nenhuma biblioteca de terceiros é necessária (utiliza os módulos nativos `hashlib` e `hmac`).

---

##  Como Executar

# 1. Clone o repositório
git clone https://github.com/naylaizismendes/Grupo2.git

# 2. Entre na pasta do projeto
cd Grupo2

# 3. Execute o código
python codigo_spike.py

