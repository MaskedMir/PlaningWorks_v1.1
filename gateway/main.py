from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

@app.post("/auth/login")
async def login(username: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://auth_service:8001/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail=response.json())
