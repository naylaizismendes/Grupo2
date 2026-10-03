## ADR 0001 — Adotar arquitetura celular combinada com monolito modular e serverless
### 1 - O trecho

ADR 0001, campo Decisão, item 2: "Monolito Modular dentro de cada célula para concentrar validação, recargas e repasse financeiro em um único processo com módulos isolados e banco relacional por esquemas". Trecho do arquivo `2-Arquitetura/Documento de Arquitetura de Software - SIMUB.pdf`, seção 3, página 10.

### 2 - O argumento

A divisão em células faz sentido para impedir que uma cidade afete a outra. A dúvida é como o repasse vai funcionar junto das recargas e da validação no mesmo processo. Na resposta à pergunta 4, página 16, o grupo diz que vai reprocessar todas as viagens do mês para recalcular o repasse. Se isso acontecer durante um pico de recargas ou enquanto os ônibus enviam viagens acumuladas, essas tarefas podem disputar memória, processamento e acesso ao banco.

O ADR não explica como essa disputa será controlada. Separar os módulos organiza o código, mas eles continuam usando os recursos do mesmo processo. Isso pesa no Envelope D, que atende cidades de tamanhos diferentes: uma cidade maior pode precisar aumentar toda a aplicação só para dar conta do fechamento mensal. O Serverless atende às consultas dos passageiros, então não resolve esse problema. A catraca continua funcionando offline, mas as recargas e a sincronização podem ficar mais lentas.

### 3 - A saída

Manter as células e o monolito modular, mas executar o repasse em um processo separado, usando as mesmas regras do projeto. Assim, seria possível aumentar a capacidade do repasse sem aumentar toda a aplicação. Como o banco ainda seria compartilhado, o cálculo deveria trabalhar com lotes menores e um limite de conexões.

Antes de definir esses limites, testar o fechamento junto de um pico de recargas e envio de viagens. Haveria mais um processo para a equipe cuidar, mas sem precisar dividir todo o sistema em microsserviços para os 25 desenvolvedores manterem.


## ADR 0002 — Isolar modelo de escrita por eventos e pseudonimização de dados pessoais
### 1 - O trecho

ADR 0002: "Event Sourcing no Repasse Contábil: o subdomínio financeiro armazena as transações de viagem e recargas exclusivamente como um fluxo imutável de eventos (ViagemValidada, RecargaEfetuada) em tabela relacional append-only."

### 2 - O argumento

O Envelope D limita a equipe a 25 desenvolvedores para atender vários municípios. A decisão de usar Event Sourcing no Repasse Contábil é coerente com a necessidade de manter uma trilha auditável e recalcular tarifas, mas transforma o fluxo de eventos na fonte dos fatos financeiros do subdomínio.
O próprio ADR reconhece o lado negativo dessa escolha: a necessidade de manter rotinas de snapshots para otimizar a reprodução dos eventos. Para um time pequeno, esse custo pode se multiplicar a cada novo município, especialmente com o versionamento de eventos, a atualização de esquemas e a operação dessas rotinas em cada célula.
Como o repasse é um processo mensal e as alterações de tarifa exigem o reprocessamento do período afetado, questionamos se os snapshots devem ser um requisito operacional para cada fechamento, ou se o cálculo pode ser executado em lote diretamente sobre os eventos imutáveis e pseudonimizados.

### 3 - A saída

Manter a tabela relacional append-only para guardar os fatos imutáveis e pseudonimizados (viagens e recargas), preservando o uso de tokens opacos e o mecanismo de desvinculação previsto no ADR. No fechamento mensal, processar em lote apenas o período necessário e gravar o resultado do repasse em um Ledger Contábil Imutável, também append-only, atrelado à versão da regra de tarifa vigente na época.
Se uma tarifa mudar no passado, o sistema reprocessará em lote apenas os eventos e as regras daquele período. A diferença calculada será gravada como um novo lançamento de ajuste, sem apagar o histórico nem alterar os identificadores pseudonimizados. A exclusão cadastral e a destruição da chave de decifra continuarão ocorrendo por desvinculação e crypto-shredding, sem modificar os registros contábeis.
Isso preserva imutabilidade, auditoria, rastreabilidade e conformidade com a LGPD. Os snapshots deixam de ser um requisito para a correção do fechamento mensal e passam a ser apenas uma otimização opcional para acelerar a reprodução dos eventos. Dessa forma, reduzimos a complexidade de sustentação para os 25 desenvolvedores sem substituir a decisão de manter os fatos financeiros como eventos imutáveis.


## ADR 0003 — Isolar integrações bancárias e sistemas legados com camada anticorrupção
### 1 - O trecho

ADR 0003, campo Decisão: "Isolar os serviços externos por meio da Arquitetura Hexagonal (Ports and Adapters) configurando Camadas Anticorrupção (ACL) explícitas nas bordas. Nenhuma estrutura externa contamina o domínio interno. Falhas externas serão amortecidas por Circuit Breakers e filas de reprocessamento (Dead Letter Queues), enquanto remessas bancárias noturnas serão orquestradas por adaptadores assíncronos desacoplados das regras de validação." E, no campo Alternativas consideradas: "Barramento Corporativo Central (ESB/SOA): Descartada por criar um ponto único de falha institucional e acoplar a lógica de integração no meio de transporte (violando a diretriz de smart endpoints)."

### 2 - O argumento

A decisão de isolar integrações por meio de Camadas Anticorrupção (ACL) e adaptadores específicos nas bordas protege o domínio, mas traz a responsabilidade de traduzir layouts proprietários e protocolos legados (como SFTP noturno) para dentro do repositório da aplicação. O Envelope D limita a equipe a 25 desenvolvedores para sustentar uma plataforma vendida para múltiplos municípios. Cada nova prefeitura ou consórcio adicionado à carteira trará seus próprios sistemas legados e regras de compensação.

Ao internalizar o desenvolvimento e a manutenção desses adaptadores e de suas respectivas filas de reprocessamento (Dead Letter Queues), a equipe de 25 engenheiros corre o risco de se tornar uma "fábrica de integrações". O custo de sustentar dezenas de conectores paralelos, monitorando falhas em sistemas de terceiros de cada cidade, sobrecarregará o time e dificultará a evolução do *core* do produto. A decisão rejeita um ESB por ser um ponto único de falha, mas ignora soluções modernas de integração fora do código da aplicação que não ferem a diretriz de *smart endpoints*.

### 3 - A saída

Em vez de construir e manter adaptadores específicos nas bordas da própria aplicação, adotar uma abordagem *API First* com um modelo canônico estrito. A plataforma expõe APIs REST e Webhooks padronizados, além de fornecer formatos de arquivo padrão para exportação.

A responsabilidade de traduzir esse formato canônico para os leiautes proprietários das prefeituras ou comunicar via SFTP noturno seria delegada para um Middleware de Integração externo (como Apache Camel, ferramentas iPaaS ou até scripts *serverless* independentes). Esse componente agiria como um tradutor fora da aplicação principal, operado preferencialmente por parceiros de implantação local. Dessa forma, a aplicação principal permanece imune às especificidades de cada cliente, garantindo que a equipe de 25 desenvolvedores foque exclusivamente na evolução da bilhetagem, viabilizando a venda do produto para novas cidades sem inchar a base de código.

## ADR 0004
### 1 - O trecho

ADR 0004, campo Decisão: "As atualizações ocorrerão obrigatoriamente por implantação em ondas (Canary por Célula): uma cidade piloto recebe a versão nova, permanece sob monitoração sintética por 60 minutos e apenas então a versão é promovida para as demais células." E, no campo Alternativas consideradas: "Cluster Kubernetes unificado com Service Mesh complexo: descartada por demandar esforço contínuo de sustentação que consumiria metade do time de 25 desenvolvedores."

### 2 - O argumento

A ADR rejeita a "Atualização simultânea global (Big Bang)" por violar a contenção de raio de impacto do Envelope D, mas a decisão escrita promove a versão nova para todas as cidades restantes de uma vez só, depois de validar em uma única cidade piloto. Isso é Big Bang para cada cidade que não é a piloto: se o defeito só aparece sob uma condição que a piloto não tinha (carga, fuso horário, ou um plugin de regra tarifária específico de outro município, previsto no Microkernel da própria arquitetura), ele atinge todas as demais células ao mesmo tempo, exatamente o cenário que a alternativa descartada deveria evitar. O livro-referência do próprio grupo, no ADR de exemplo do capítulo de arquitetura celular, resolve isso com implantação em ondas de uma célula por vez, com trinta minutos de observação entre cada uma, não piloto-depois-todo-o-resto. Além disso, o ADR descarta a malha de serviços pelo custo de sustentação, mas não estima o custo de construir e manter, do zero, um motor de canary multi-tenant com monitoração sintética por célula e corte automático em 60 minutos, sem qualquer procedimento manual. Sem essa conta, não dá pra saber se a alternativa escolhida é de fato mais barata do que a rejeitada.

### 3 - A saída

Implantar em ondas sucessivas de tamanho crescente (por exemplo, 1 cidade, depois 3, depois 10, depois o restante), cada onda com sua própria janela de observação sintética, avançando para a próxima só se a anterior passar, o que mantém o raio de impacto de uma implantação defeituosa contido em uma fração pequena da base a cada vez. A primeira onda deve incluir cidades com plugins tarifários distintos entre si, não uma única cidade fixa, para cobrir a diversidade de configuração antes de promover para o restante. Para não repetir o custo de sustentação que a malha de serviços teria, usar uma ferramenta de entrega progressiva já existente para orquestrar as ondas, em vez de construir esse motor internamente.

## ADR 0005 
### 1 - O trecho

ADR 0005: "Controle de Saldo Híbrido (Dual-ledger): O cartão físico armazena seu saldo em setor seguro cifrado. Ao validar offline, o dispositivo debita o saldo local do cartão, gera uma transação assinada com contador sequencial monotônico e armazena o evento em fila persistente local."

E: "Reconciliação e Resolução de Conflitos no Servidor: Ao recuperar o sinal 4G, o validador descarrega as transações em lote."

### 2 - O argumento

A decisão de permitir operação offline é coerente com o requisito de funcionamento por até quatro horas sem 4G e com o limite de 300 ms para a liberação da catraca. Porém, o modelo Dual-ledger cria duas representações de saldo que podem divergir: o saldo físico armazenado no cartão e o saldo mantido no sistema central.

Essa divergência fica mais evidente quando uma recarga é realizada pelo aplicativo enquanto o ônibus está offline. O próprio documento afirma que a recarga é registrada imediatamente na conta central e que, caso o ônibus ainda não tenha recebido essa informação, pode utilizar o saldo físico residual ou até uma modalidade de "saldo de confiança".

O problema é que o ADR não define de forma suficientemente explícita qual saldo é a fonte autoritária após a reconciliação, nem estabelece uma regra clara para conflitos entre créditos centrais, débitos offline e o saldo armazenado fisicamente no cartão. Com vários validadores desconectados simultaneamente, essa indefinição pode aumentar a complexidade da reconciliação e produzir estados divergentes.

Além disso, detectar posteriormente usos incompatíveis e bloquear o cartão na próxima sincronização reduz o impacto futuro da fraude, mas não resolve por si só qual operação financeira deve prevalecer quando os registros conflitantes forem conciliados.

### 3 - A saída

Manter a autonomia offline do validador, mas estabelecer explicitamente o saldo central da célula como fonte autoritária após a sincronização. O saldo presente no cartão deve funcionar como uma representação local para permitir a validação durante períodos sem conectividade, e não como uma segunda fonte definitiva de verdade.

Cada operação offline deve possuir identificador único, contador monotônico e assinatura, como já proposto pelo ADR. Quando a conexão retornar, o servidor recebe essas operações de forma idempotente, verifica a sequência dos eventos e reconcilia os débitos offline com as recargas registradas no sistema central.

Em caso de conflito, o servidor mantém o histórico das operações recebidas, calcula o saldo autoritário resultante e gera os ajustes necessários. O cartão recebe o estado reconciliado em uma sincronização posterior.

Dessa forma, preserva-se a principal vantagem do ADR 0005 — permitir validações rápidas mesmo durante quatro horas sem 4G — mas fica explícito quem possui a autoridade sobre o saldo depois da reconciliação, reduzindo ambiguidades no modelo Dual-ledger e facilitando o tratamento de divergências e fraudes.
