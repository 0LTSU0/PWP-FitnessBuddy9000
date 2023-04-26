"""
Pika listener implementation for use with client
"""

import ssl
import json
import queue
import pathlib
import pika

STATS = queue.Queue(1) #allow only one set of stats

def listen_notifications(user, pwd):
    """
    Based on course example
    """
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="193.167.189.95",
                                          port=5672,
                                          virtual_host="ryhma-jll-vhost",
                                          credentials=pika.PlainCredentials(user, pwd),
                                          ssl_options=pika.SSLOptions(context)))

    channel = connection.channel()
    channel.exchange_declare(
        exchange="notifications",
        exchange_type="fanout"
    )
    result = channel.queue_declare(queue="", exclusive=True)
    channel.queue_bind(
        exchange="notifications",
        queue=result.method.queue
    )
    channel.basic_consume(
        queue=result.method.queue,
        on_message_callback=notification_handler,
        auto_ack=True
    )
    print("Start listening...")
    channel.start_consuming()


def notification_handler(channel, method, properties, body):
    """
    Handler for incoming notifications
    """
    print("notification received: ", body)
    global STATS
    STATS.queue.clear()
    STATS.put(json.loads(body))

if __name__ == "__main__":
    filepath = pathlib.Path(__file__).parent.joinpath("pikacredentials.json")
    with open(filepath, "r", encoding="utf-8") as f:
        cred = json.load(f)
        listen_notifications(cred.get("user"), cred.get("password"))
