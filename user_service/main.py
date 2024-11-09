from fastapi import FastAPI
import pika
import os

app = FastAPI()

# Настройка RabbitMQ для прослушивания очереди
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
channel = connection.channel()
channel.queue_declare(queue='auth_queue')

def callback(ch, method, properties, body):
    print(f"Received message from Auth Service: {body}")

channel.basic_consume(queue='auth_queue', on_message_callback=callback, auto_ack=True)

@app.on_event("startup")
async def startup():
    print("Starting User Service and listening to RabbitMQ messages...")
    channel.start_consuming()
