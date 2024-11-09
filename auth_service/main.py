from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
import pika
import os

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка RabbitMQ
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
channel = connection.channel()
channel.queue_declare(queue='auth_queue')

class AuthRequest(BaseModel):
    username: str
    password: str

fake_db = {
    "testuser": {"username": "testuser", "hashed_password": pwd_context.hash("testpass")}
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@app.post("/login")
async def login(auth_data: AuthRequest):
    user = fake_db.get(auth_data.username)
    if not user or not verify_password(auth_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    # Отправка данных о логине через RabbitMQ
    channel.basic_publish(exchange='', routing_key='auth_queue', body=f"{auth_data.username} logged in")
    return {"message": "Login successful"}
