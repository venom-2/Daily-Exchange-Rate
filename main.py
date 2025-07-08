from fastapi import FastAPI
from app.routes import exchange_rate
from app.routes import hello

app = FastAPI()

app.include_router(exchange_rate.router)
app.include_router(hello.router)
