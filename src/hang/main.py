from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.hang.routes.router import router
from src.hang.schemas.schemas import UserDB, SwipeDB, ConversationDB, MessageDB
from src.hang.database.database import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router)
