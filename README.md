# Rota Vital · Emissão assíncrona de guias

Experimento individual de mensageria. O hospital publica 20 requisições válidas e uma sem `requisicaoId`. Cada consumidor recebe um pedido por vez, emite a guia no terminal e confirma o processamento com `DeleteMessage`. O pedido inválido fica sem confirmação.

## Como reproduzir

Com Python 3 e Docker, inicie o ElasticMQ em um terminal:

```sh
docker run --rm -p 127.0.0.1:9324:9324 softwaremill/elasticmq-native:1.6.11
```

O caminho usado para gravar as evidências foi o mesmo ElasticMQ 1.6.11, executado com Java 21. Para reproduzir dessa forma, baixe o [JAR do ElasticMQ](https://s3-eu-west-1.amazonaws.com/softwaremill-public/elasticmq-server-1.6.11.jar) e execute `java -jar elasticmq-server-1.6.11.jar`.

Em outro terminal, na pasta deste README:

```sh
python -m pip install boto3==1.44.12
python demo.py 1
python demo.py 2
```

Cada comando cria uma fila padrão exclusiva com visibilidade de 15 segundos, inicia os processos consumidores, publica os pedidos e aguarda 22 segundos para observar a reentrega. Ao terminar, remove a fila daquele ensaio. As credenciais fictícias de `fila.py` servem para o endpoint local. O exemplo emite as guias no log e simula o tempo de processamento.

## Discussão

**1. Por que confirmar depois de processar?** Se o processo cair entre apagar o pedido e emitir a guia, o hospital fica sem a guia e a fila perde a oportunidade de tentar novamente. No log, cada linha `ACK` aparece depois da emissão da guia correspondente e da resposta de sucesso de `DeleteMessage`.

**2. Como os consumidores dividiram o trabalho?** Os resultados medidos estão abaixo. Os processos competem pelos pedidos disponíveis. Em uma fila padrão, a ordem é de melhor esforço. Mesmo quando uma execução segue a sequência de envio, a aplicação precisa aceitar mensagens fora de ordem. [Documentação das filas padrão](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)

**3. Como impedir uma segunda emissão?** Uma queda depois da emissão e antes da confirmação pode provocar uma nova tentativa. Em produção, usaria `requisicaoId` como chave única da guia no banco. A transação insere a guia ou recupera a já existente em caso de conflito. Só depois do commit o consumidor confirma o pedido. Assim, dois consumidores concorrentes também produzem uma única guia persistida.

**4. O que aconteceu com o pedido inválido?** Depois de recebido, ele ficou temporariamente oculto. A validação falhou e o consumidor deixou o recibo sem confirmação. Expirado o prazo, o mesmo ID voltou com o contador incrementado. Uma DLQ isolaria esse pedido após um limite configurado de recebimentos para permitir diagnóstico e correção.

**5. O que muda para o hospital?** Na chamada síncrona, o hospital aguarda a emissão e recebe a guia ou o erro na mesma resposta. Com a fila, ele pode receber um protocolo assim que o pedido é aceito. Os consumidores podem absorver picos e retomar o trabalho após uma interrupção. Em troca, o hospital precisa acompanhar o status, e o sistema precisa correlacionar a guia ao protocolo e lidar com atrasos e duplicatas.

## Resultados observados

| Ensaio | Envios | Guias confirmadas | Reentrega do inválido |
|---|---:|---|---|
| Um consumidor | 21 | 20 pelo PID 2196 | 15,026 s entre as tentativas 1 e 2 |
| Dois consumidores | 21 | 10 pelo PID 31024 e 10 pelo PID 23760 | 15,036 s entre as tentativas 1 e 2 |

No segundo ensaio, o PID 31024 confirmou as requisições ímpares e o PID 23760 confirmou as pares. As confirmações apareceram na ordem R-001 a R-020 nesta execução, mas isso não é garantido: no primeiro ensaio, com um único consumidor, a R-016 foi processada antes da R-015. A divisão pode mudar a cada rodada. O pedido inválido foi recebido duas vezes com o mesmo MessageId e a tentativa incrementada, primeiro pelo PID 31024 e depois pelo PID 23760.

Veja os [eventos com um consumidor](evidencias/ensaio-1.txt) e os [eventos com dois consumidores](evidencias/ensaio-2.txt), saídas reais de `python demo.py 1` e `python demo.py 2` contra o ElasticMQ 1.6.11, e as capturas do [primeiro](evidencias/ensaio-1.png) e do [segundo ensaio](evidencias/ensaio-2.png), tiradas da gravação de tela.

## Vídeo

A [gravação de tela](demonstracao.mp4) (1 min 11 s) captura a janela do terminal durante `python demo.py 1` e `python demo.py 2`: mostra o ElasticMQ no ar, a fila criada com visibility timeout de 15 s, os dois consumidores dividindo as guias e o pedido inválido voltando após o timeout. Os logs e as capturas desta pasta vêm dessa mesma execução.

## Uso de IA

Usei o Codex para conferir o código e organizar a demonstração. A ferramenta também rodou os testes e conferiu nos logs quantas guias cada consumidor confirmou e quanto tempo o pedido inválido levou para voltar à fila.
