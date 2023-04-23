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
usr = ""
pwd = ""

def handle_task(channel, method, properties, body):
    print("\nHandling task")
    #wait a few seconds just for fun
    time.sleep(randint(2,4))

    try:
        task = json.loads(body)
        href = API_SERVER + task["@controls"]["fitnessbuddy:add-stats"]["href"]
        print("Body: \n", task, "\n")

        #TEMP test that post works
        #these stats should be calculated from the input json
        new_stats = {
            "date": datetime.isoformat(datetime.now()),
            "user_id": 1,
            "total_exercises": 15,
            "daily_exercises": 0.8,
            "daily_calories_in": 2575.6,
            "daily_calories_out": 2575.6
        }
        #send post request to url given in controls
        with requests.Session() as session:
            print("Sending post request to: ", href)
            resp = session.post(
                href,
                json=new_stats
            )
        
    except (KeyError, json.JSONDecodeError) as e:
        print("ERROR:", e)

    finally:
        # acknowledge the task regardless of outcome
        print("Task handled")
        channel.basic_publish(
            exchange="notifications",
            routing_key="",
            body=json.dumps(new_stats)
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)

def main():
    global channel
    connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="193.167.189.95",
                port=5672,
                virtual_host="ryhma-jll-vhost",
                credentials=pika.PlainCredentials(usr, pwd),
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
    #get credentials from \client directory
    cwd = os.getcwd()
    cwd = cwd.replace("worker", "client")
    credentials_file = str("{}\pikacredentials.json".format(cwd))
    with open(credentials_file) as f:
        cred = json.load(f)
        usr = cred.get("user")
        pwd = cred.get("password")

    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)