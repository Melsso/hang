from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.hang.routes.router import router
from src.hang.database.database import engine
from src.hang.schemas.schemas import Base
from src.hang.helpers.exceptions import register_exception_handlers

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="src/hang/static"), name="static")

register_exception_handlers(app)