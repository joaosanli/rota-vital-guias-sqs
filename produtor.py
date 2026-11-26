import json
from fila import cliente


def publicar(url):
    sqs = cliente()
    for i in range(1, 22):
        pedido = {"hospital": "H-Recife"}
        if i <= 20:
            pedido["requisicaoId"] = f"R-{i:03}"
        resposta = sqs.send_message(QueueUrl=url, MessageBody=json.dumps(pedido))
        print("ENVIO", pedido.get("requisicaoId", "invalida"), resposta["MessageId"], flush=True)
