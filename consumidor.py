import json
import os
import time
from fila import cliente


def consumir(url, parar, pronto):
    sqs = cliente()
    pronto.set()
    while not parar.is_set():
        lote = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1, WaitTimeSeconds=1,
                                   AttributeNames=["ApproximateReceiveCount"])
        for msg in lote.get("Messages", []):
            pedido = json.loads(msg["Body"])
            tentativa = msg["Attributes"]["ApproximateReceiveCount"]
            prefixo = f"{time.time():.3f} PID={os.getpid()}"
            if "requisicaoId" not in pedido:
                print(prefixo, "FALHA sem requisicaoId", msg["MessageId"], "tentativa", tentativa, flush=True)
                continue
            time.sleep(0.12)
            guia = "G-" + pedido["requisicaoId"]
            print(prefixo, "GUIA", guia, pedido["hospital"], flush=True)
            sqs.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
            print(f"{time.time():.3f} PID={os.getpid()}", "ACK", guia, flush=True)
