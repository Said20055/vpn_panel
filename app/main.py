# app/main.py
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import engine, Base
from app.domain import models
from app.api import subscription, admin
from app.api.admin import auth_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="VPN Admin Panel")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(subscription.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return RedirectResponse(url="/admin")
