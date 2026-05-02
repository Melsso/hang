from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.hang.helpers.routes import router

app = FastAPI()
app.include_router(router)

