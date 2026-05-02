from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.hang.routes.router import router

app = FastAPI()
app.include_router(router)

