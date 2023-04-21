import math
import os
import sys
from random import randint
import time
import json
import pika
import requests
from datetime import datetime
import ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

API_SERVER = "http://localhost:5000"

channel = None

def handle_task(channel, method, properties, body):
    print("\nHandling task")
    #wait a few seconds just for fun
    time.sleep(randint(3,6))

    try:
        task = json.loads(body)
        print("Exercises: ", task["exercises"])
        print("Measurements: ", task["measurements"])
    except (KeyError, json.JSONDecodeError) as e:
        print("ERROR:", e)

    finally:
        # acknowledge the task regardless of outcome
        print("Task handled")
        channel.basic_ack(delivery_tag=method.delivery_tag)

def main():
    global channel
    connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="193.167.189.95",
                port=5672,
                virtual_host="ryhma-jll-vhost",
                credentials=pika.PlainCredentials("ryhma-jll", "6iWuvvYAF1R88k4WP43tmnqTPzqAWVaPu3OMRdkqb4k"),
                ssl_options=pika.SSLOptions(context)
            )
        )
    channel = connection.channel()
    channel.exchange_declare(
        exchange="notifications",
        exchange_type="fanout"
    )
    channel.exchange_declare(
        exchange="logs",
        exchange_type="fanout"
    )
    #empty old queue
    channel.queue_delete(queue='stats')
    #make new one
    channel.queue_declare(queue="stats")
    channel.basic_consume(queue="stats", on_message_callback=handle_task)
    print("Service started")
    channel.start_consuming()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)