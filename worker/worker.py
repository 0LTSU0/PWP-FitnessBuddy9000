"""
Original worker from course material
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-4-implementing-hypermedia-clients/
"""
import os
import sys
from random import randint
import time
import json
import ssl
from datetime import datetime
from collections import OrderedDict
import pika
import requests

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

API_SERVER = "http://localhost:5000"

CHANNEL = None
USR = ""
PWD = ""

def log_error(message):
    """
    Logs errors
    """
    CHANNEL.basic_publish(
        exchange="logs",
        routing_key="",
        body=json.dumps({
            "timestamp": datetime.now().isoformat(),
            "content": message
        })
    )

def handle_task(channel, method, properties, body):
    """
    Handles task by parsing message and sends the response back
    to given url.
    """
    print("\nHandling task")
    #wait a few seconds just for fun
    time.sleep(randint(2,4))

    try:
        task = json.loads(body)
        href = API_SERVER + task["@controls"]["fitnessbuddy:add-stats"]["href"]
        print("Body: \n", task, "\n")
        daily_exercise, avg_calories_in, avg_calories_out = compute_stats(task)
        #calculate new stats
        new_stats = {
            "date": datetime.isoformat(datetime.now()),
            "user_id": task["user"]["id"],
            "total_exercises": len(task["exercises"]),
            "daily_exercises": daily_exercise,
            "daily_calories_in": avg_calories_in,
            "daily_calories_out": avg_calories_out
        }
        #send post request to url given in controls
        with requests.Session() as session:
            print(f"Sending post request to: {href}")
            resp = session.post(
                href,
                json=new_stats
            )
            if resp.status_code != 204:
                # log error 
                log_error("Unable to send result")

        channel.basic_publish(
            exchange="notifications",
            routing_key="",
            body=json.dumps(new_stats)
        )
        
    except (KeyError, json.JSONDecodeError) as error:
        print("ERROR:", error)

    finally:
        # acknowledge the task regardless of outcome
        print("Task handled")
        channel.basic_ack(delivery_tag=method.delivery_tag)

def compute_stats(body):
    """
    Computes daily averages.
    Returns average number of daily exercises, calories_in, and calories_out
    """
    measurement_date_counts = OrderedDict()
    sum_of_calories_in = 0
    sum_of_calories_out = 0

    creaton_date  = datetime.fromisoformat(body["user"]["user_creation_date"])
    current_date = datetime.today()
    difference = current_date - creaton_date

    for i in range(len(body["measurements"])):
        try:
            in_date_format_measurement = datetime.fromisoformat(body["measurements"][i]["date"])
            measurement_date_counts[in_date_format_measurement.date()] += 1
        except KeyError:
            measurement_date_counts[in_date_format_measurement.date()] = 1
        
        sum_of_calories_in += body["measurements"][i]["calories_in"]
        sum_of_calories_out += body["measurements"][i]["calories_out"]
    
    length = len(body["exercises"])

    try:
        avg_exercise = length / difference.days
    except ZeroDivisionError:
        avg_exercise = 0
    try:
        avg_calories_in = sum_of_calories_in / len(body["measurements"])
    except ZeroDivisionError:
        avg_calories_in = 0
    try:
        avg_calories_out = sum_of_calories_out / len(body["measurements"])
    except ZeroDivisionError:
        avg_calories_out = 0
    
    return round(avg_exercise, 2), round(avg_calories_in, 2), round(avg_calories_out, 2)

def main():
    """
    Consumes stats queue
    """
    global CHANNEL  # noqa: W0603
    connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="193.167.189.95",
                port=5672,
                virtual_host="ryhma-jll-vhost",
                credentials=pika.PlainCredentials(USR, PWD),
                ssl_options=pika.SSLOptions(context)
            )
        )
    CHANNEL = connection.channel()
    CHANNEL.exchange_declare(
        exchange="notifications",
        exchange_type="fanout"
    )
    CHANNEL.exchange_declare(
        exchange="logs",
        exchange_type="fanout"
    )
    #empty old queue
    CHANNEL.queue_delete(queue='stats')
    #make new one
    CHANNEL.queue_declare(queue="stats")
    CHANNEL.basic_consume(queue="stats", on_message_callback=handle_task)
    print("Service started")
    CHANNEL.start_consuming()
    
if __name__ == "__main__":
    #get credentials from \client directory
    cwd = os.getcwd()
    cwd = cwd.replace("worker", "client")
    CREDENTIALS_FILE = str(fr"{cwd}\pikacredentials.json")
    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        cred = json.load(f)
        USR = cred.get("user")
        PWD = cred.get("password")

    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
