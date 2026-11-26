import argparse
import multiprocessing as mp
import time
import uuid

from consumidor import consumir
from fila import cliente
from produtor import publicar


def executar(n):
    sqs = cliente()
    nome = f"guias-{n}-{uuid.uuid4().hex[:8]}"
    url = sqs.create_queue(QueueName=nome, Attributes={"VisibilityTimeout": "15"})["QueueUrl"]
    atributos = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["VisibilityTimeout"])
    print("FILA", url, atributos["Attributes"], flush=True)
    parar = mp.Event()
    processos = []
    try:
        for _ in range(n):
            pronto = mp.Event()
            processo = mp.Process(target=consumir, args=(url, parar, pronto))
            processo.start()
            processos.append(processo)
            if not pronto.wait(20):
                raise RuntimeError("Consumidor indisponível")
        publicar(url)
        time.sleep(22)
    finally:
        parar.set()
        for processo in processos:
            processo.join()
        sqs.delete_queue(QueueUrl=url)
    if any(p.exitcode for p in processos):
        raise RuntimeError("Erro durante o consumo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("consumidores", type=int, choices=[1, 2])
    executar(parser.parse_args().consumidores)
