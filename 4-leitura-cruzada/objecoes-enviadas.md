# Introdução

O Grupo 02 avaliou as decisões do Grupo 06 confrontando a sua arqcuitetura com as restrições inegociáveis do Envelope E: operação fiscalizada pelo poder público e Tribunal de Contas, equipa de 15 programadores e 1 responsável por conformidade, em nuvem pública, com trilha de auditoria completa e LGPD.
Apresentam-se 7 objeções técnicas fundamentadas, estruturadas estritamente nas três partes regulamentares:
1. A decisão ou trecho atacado (com indicação exata de ficheiro e secção);
2. O argumento técnico e de envelope (por que a decisão não se sustenta ou que custo/risco foi ignorado);
3. O que o grupo revisor teria feito no lugar.

## Objeção 01: Contradição física entre autocarro offline por até 4 horas e consulta síncrona ao "dono do dado" para autorizar embarque

**Decisão / Trecho atacado:** Ficheiro 2-arquitetura/documento-arquitetura.md, Secção 7.2 ("Como o saldo do cartão fica consistente entre recarga no aplicativo e uso no ônibus, com atraso de sincronização?"), item 5 do mecanismo; e Ficheiro 2-arquitetura/adr/0002-dar-a-cada-servico-o-proprio-banco-e-usar-event-sourcing-no-financeiro.md, Decisão.

**Argumento:** Na Secção 7.2, item 5, afirma-se textualmente que: "Onde a leitura precisa ser exata na hora — o saldo usado para autorizar o próximo uso — consulta-se o dono do dado, nunca uma projeção atrasada". O "dono do dado" indicado é o Serviço de Cartões e Recarga, residente na nuvem pública. Contudo, a premissa do dimensionamento C1 e a Sceção 1.2 estabelecem que o ônibus opera sob 4G intermitente e mantém-se até 4 horas sem rede. Caso o validador tenha que consultar o "dono do dado" na nuvem no momento do embarque, o torniquete bloqueará por timeout na primeira sombra de sinal móvel, negando frontalmente a premissa C1 de liberar o passageiro em até 300 ms offline. Caso o validador autorizar com base em cópia local, a frase da Sceção 7.2 é falsa e implode a garantia declarada de que "o saldo só vive no Serviço de Cartões e Recarga". O projeto não modelou como a autorização offline ocorre sem consultar a nuvem. 

**O que teríamos feito no lugar:** Teríamos adotado o modelo de saldo em chip (dual-ledger com crédito diferido): O cartão guarda o saldo permanentemente em um setor seguro e cifrado. A catraca retira o valor do cartão em menos de 50 milissegundos, sem precisar acessar a nuvem. Quando o usuário recarrega na aplicação móvel, o sistema gera ordens de crédito que ficam pendentes. Depois, essas ordens são enviadas para a frota e armazenadas no chip do cartão na primeira validação online do usuário. Assim, a conta central fica sincronizada por meio de lotes e de uma saga compensatória assíncrona. 

## Objeção 02: Descarte indevido do Microkernel e rigidez frente a decretos tarifários frequentes sob fiscalização

**Decisão / Trecho atacado:** Ficheiro 1-matriz/matriz.md, linha 8 (Microkernel); e Ficheiro 2-arquitetura/documento-arquitetura.md, Secção 4 ("Nível 3 — componentes do Núcleo Financeiro").

**Argumento:** Na matriz de estilos, o grupo descartou o Microkernel com a justificação: "É indicado quando há muitas extensões/plugins, o que não é uma necessidade central do sistema (Seção 8.6)". No Envelope E, a operação é supervisionada por órgãos gestores públicos e consórcios municipais. As regras de subsídio por passageiro, as matrizes de integração horária, as gratuidades e a repartição entre viações não são fixas. Elas são alteradas com frequência por meio de decretos municipais e portarias regulamentares, às vezes com efeito retroativo temporário ou aplicadas apenas em feriados ou períodos eleitorais. Sem o Microkernel (Abreu, 2026, Capítulo 8), cada nova fórmula estabelecida pelo regulador obriga a equipe a modificar e reimplementar a aplicação do Núcleo Financeiro. Isso exige que todo o motor contábil seja retestado, o que introduz um risco crítico de regressão nos cálculos de meses anteriores e compromete a estabilidade exigida pelo Tribunal de Contas (Seção 8.1 e 8.6). 

**O que teríamos feito no lugar:** Teríamos implementado o estilo Microkernel (Capítulo 8) dentro do Núcleo Financeiro. O motor contábil central seria estável e publicaria a interface IRegraTarifaria. Cada decreto municipal e cada regra de subsidiação seriam plugins isolados, versionados e delimitados por data de vigência. No recálculo retroativo exigido pelo requisito C7, o orquestrador invocaria dinamicamente o plugin correspondente à data da viagem, sem alterar nenhuma linha do código de liquidação contábil. 

## Objeção 03: Quebra da auditabilidade pública de gratuidades pela destruição indiscriminada de chaves (Crypto-shredding do ADR 0005)

**Decisão / Trecho atacado:** Ficheiro 2-arquitetura/adr/0005-conciliar-auditoria-imutavel-e-esquecimento-lgpd-por-crypto-shredding.md, Decisão; Ficheiro 2-arquitetura/documento-arquitetura.md, Secção 7.5; e Ficheiro 3-spike/exemplo.py, linhas 112 a 136.

**Argumento:** O ADR 0005 e o spike da Entrega 3 resolvem a LGPD ao cifrar o bloco pessoal com chave individual no KeyStore e destruí-la no pedido de esquecimento. No Caso 1, 25% dos passageiros usam gratuidades ou descontos subsidiados, como estudantes, idosos e pessoas com deficiência. No Envelope E, a prefeitura e o Tribunal de Contas pagam às operadoras com base nas gratuidades registradas e fazem auditorias regularmente para verificar se os passageiros tinham direito ao subsídio na data do evento. O spike do grupo (exemplo.py, linha 112) cifra os dados do passageiro de forma completa, como cifrar(nome, chave). Ao destruir a chave, o sistema apaga de forma irreversível a identidade e o status de elegibilidade social do passageiro. Durante uma inspeção do Tribunal de Contas sobre subsídios anteriores, a operadora não conseguirá provar se a viagem gratuita foi feita por alguém que realmente tinha direito ou se foi resultado de uma fraude interna, o que pode levar à anulação do subsídio e a multas financeiras. 

**O que teríamos feito no lugar:** Teríamos dividido os dados em três níveis de conformidade: 

- Identificadores civis pessoais  como nome, CPF, foto e contato estariam no esquema de identidade, protegidos por destruição criptográfica para seguir a LGPD; 
- Atributos regulatórios de direito público, como tipo de benefício — idoso ou estudante —, número do cartão social, entidade emissora e cota mensal, ficariam em claro e seriam pseudonimizados por meio de um identificador opaco no evento contábil; 
- Dados da viagem e da linha mantidos em claro.

Dessa forma, ao eliminar a chave, o cidadão não seria identificável segundo a LGPD, mas a operadora e o auditor ainda teriam provas documentais concretas de que o subsídio foi dado a uma pessoa com benefício ativo. 

## Objeção 04: Sobrecarga operacional de 7 microsserviços para uma equipa de 15 programadores e 1 responsável por conformidade

**Decisão / Trecho atacado:** Ficheiro 2-arquitetura/adr/0001-compor-microsservicos-por-subdominio-com-espinha-de-eventos.md; Ficheiro 2-arquitetura/documento-arquitetura.md, Secção 2 e Tabela da Secção 6.

**Argumento:** O grupo adotou Microsserviços divididos em 7 unidades implantáveis (Validação, Cartões e Recarga, Telemetria, Informação ao Passageiro, Núcleo Financeiro, Integração e Conformidade e Gateway de API). Na Secção 6 do DAS, o grupo descreve Secção 6 do DAS como “tensão honesta”, reconhecendo que Fowler recomenda monolito primeiro e que literatura contraindica microsserviços para equipas pequenas (Abreu, 2026, Seção 9.6). No Envelope E, exigência E3 exige nuvem pública com trilha de auditoria completa e correlacionada. Sustentar 7 serviços independentes com bancos isolados, esteiras de CI/CD próprias, contratos de rede versionados, tracing distribuído em cada chamada assíncrona, disjuntores e gestão de sagas compensatórias consome um pedágio de infraestrutura desproporcional (Seção 9.7). Para 15 programadores e apenas 1 responsável por conformidade, sobrecarga de operar topologia distribuída reduz produtividade da equipa e aumenta risco de falhas de segurança e não-conformidade em auditorias do regulador. 

**O que teríamos feito no lugar:** Teríamos adotado um Monólito Modular (Capítulo 6) que seria adotado com fronteiras verificadas estaticamente para o núcleo de negócio (Validação, Cartões e Repasse). Monólito Modular executaria todo o núcleo de negócio em um único processo, usando transações atómicas locais. Os esquemas lógicos permaneceriam separados no PostgreSQL. Somente as unidades distribuídas seriam responsáveis por ingestão de telemetria e por consultas públicas de passageiros, porque essas atividades sofrem cargas extremas e sazonais. A eliminação da complexidade de transações distribuídas libertaria a equipa de 15 pessoas, permitindo que a equipa atenda às rigorosas normas de auditoria. 

## Objeção 05: Telemetria tratada como publicação direta no barramento sem duto formal de contrapressão para suporte a autos de infração

**Decisão / Trecho atacado:** Ficheiro 2-arquitetura/documento-arquitetura.md, Secção 7.3 ("Como a telemetria escala no pico sem derrubar o restante do sistema?"); e Ficheiro 2-arquitetura/mapa-restricoes-decisoes.md, requisito C5.

**Argumento:** O grupo sustenta que a telemetria escala apenas com "um Serviço de Telemetria que recebe as posições GPS e publica PosicaoRecebida no barramento — e nada mais" e que "o barramento funciona como amortecedor". No Envelope E, a telemetria de 1.200 autocarros (80 a 400 posições por segundo) não é apenas um serviço para os passageiros. A telemetria do Envelope E é a prova que a prefeitura usa para registrar e multar concessionárias quando os ônibus não partem, atrasam ou desviam de rota. Tratar a ingestão de dados como se fosse uma publicação sem controle ignora custos importantes. Sem um canal de processamento como o modelo Pipes and Filters, a telemetria do Envelope E perde sinais de GPS refletidos em desfiladeiros urbanos, não interpola os dados que chegam depois de túneis e não aplica contrapressão nas bordas do fluxo, como descrito nas Seções 16.2 e 16.7. Quando conexões saturam e pacotes são descartados, a consola de fiscalização mostra veículos que não existem, e isso leva a multas injustas e a disputas jurídicas entre operadoras e o município. 

**O que teríamos feito no lugar:** Teríamos implementado o estilo Pipes and Filters (Capítulo 16) na ingestão de telemetria. Neste cenário, o fluxo de GPS seria submetido a filtros de validação geoespacial, limpeza de ruídos e reconciliação temporal com a grelha horária oficial da concessão. Somente as posições depuradas chegariam ao sumidouro de auditoria fiscal e às projeções de monitorização. Isso garantiria a validade jurídica dos relatórios de fiscalização. 

## Objeção 06: Tratamento de duplicidade de passagens como simples "suspeita" sem mecanismo automático de estorno contábil

**Decisão / Trecho atacado:** Ficheiro 2-arquitetura/documento-arquitetura.md, Secção 7.1, item 6 do mecanismo; e Ficheiro 2-arquitetura/adr/0006-validar-offline-no-embarcado-e-deduplicar-a-passagem-no-servidor.md, Consequências Negativas.

**Argumento:** No item 6 da Secção 7.1, afirma-se que quando o mesmo cartão é validado em dois autocarros distintos, "o segundo uso é marcado como suspeita, com os dois fatos preservados em ordem como prova — nunca sobrescritos". Contudo, o documento e o ADR 0006 não explicam como essa “suspeita” será resolvida financeiramente no encerramento contábil. Em contratos de concessão sob o Envelope E, os consórcios de transporte competem por receita e a câmara de compensação municipal divide o montante. Se dois autocarros de operadoras rivais aceitarem o mesmo cartão fraudado em modo offline, qual operadora será remunerada? A prefeitura pagará subsídio em duplicado pela mesma passagem? Deixar a colisão como “suspeita” em aberto transfere o risco de fraude para os cofres públicos e viola a premissa de “fraude de recarga zero e conciliação com o banco” (requisito C4). 

**O que teríamos feito no lugar:** Teríamos modelado uma regra algorítmica de análise espaço-temporal no motor de liquidação: o sistema compararia a distância entre as duas validações e o intervalo de tempo t. Se detectasse uma velocidade improvável para um deslocamento urbano — por exemplo, superior a 80 km/h —, o motor geraria imediatamente um evento contábil compensatório de glosa. Nesse caso, ele liquidaria a primeira viagem como legítima, reteria o pagamento da segunda viagem, que seria considerada duplicada, e enviaria automaticamente o ID do cartão para a denylist de toda a frota no próximo ciclo de sincronização. 

## Objeção 07: Omissão de funções de aptidão executáveis no pipeline para fiscalização contínua de conformidade e arquitetura

**Decisão / Trecho atacado:** Ficheiro 2-arquitetura/documento-arquitetura.md (ausência de secção de governança e funções de aptidão); e Ficheiro 2-arquitetura/adr/0004-operar-em-nuvem-com-trilha-de-auditoria-e-observabilidade-obrigatorias.md.

**Argumento:** O Grupo 06 criou uma arquitetura complexa, com bancos separados por serviço, um barramento assíncrono e criptografia para seguir a LGPD. Porém, o projeto não incluiu nenhuma função de aptidão automatizada na integração contínua para garantir que essas regras fossem seguidas (Abreu, 2026, Seções 4.8 e 19.6). O Envelope E diz que a equipe tem apenas um responsável por conformidade para acompanhar 15 programadores. Sem testes estáticos de arquitetura que interrompam o build automaticamente, é muito difícil que essa única pessoa garanta que: 

- Nenhum programador tenha adicionado consultas entre bancos que quebrem o isolamento de dados; 
- Nenhuma alteração no Núcleo Financeiro tenha ignorado a criptografia do KeyStore antes de gravar no event store; 
- O validador não tenha incluído chamadas de rede que bloqueiem o fluxo de 300 ms. .

A falta de funções de aptidão faz com que a deriva arquitetural aconteça na primeira entrega sob pressão de prazo, prejudicando a certificação da auditoria regulatória. 

**O que teríamos feito no lugar:** Teríamos formalizado e implementado funções de aptidão obrigatórias na esteira de CI (conforme demonstrado no Capítulo 4 e 6 do livro):

- Teste automatizado com analisador estático, como o import-linter ou o ArchUnit, reprovando código que acesse dados relacionais do módulo financeiro sem passar pela camada de proteção do titular; 
- Teste de integridade que impede a compilação de chamadas remotas síncronas dentro do módulo embarcado de validação; 
- Verificador de imutabilidade que garante que a tabela do event store não tenha operações de UPDATE ou DELETE mapeadas no ORM. 

## Conclusão

O projeto do Grupo 06 é consistente na escolha de Event Sourcing e no conceito de crypto-shredding. Todavia, falhou em aspectos estruturais do Envelope E: montou uma malha de microsserviços pesada demais para 15 programadores, descartou o Microkernel necessário para os decretos tarifários, assumiu uma contradição física ao exigir leitura do "dono do dado" em autocarros offline e destruiu dados necessários para a auditoria de gratuidades públicas.

