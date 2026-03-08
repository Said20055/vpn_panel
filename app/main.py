# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.core.database import engine, Base
from app.domain import models
from app.api import subscription, admin # <-- импортируем admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="VPN Admin Panel")

# Подключаем роутеры
app.include_router(subscription.router)
app.include_router(admin.router) # <-- подключаем роутер админки

@app.get("/")
def root():
    # При заходе на корень сайта, сразу перенаправляем в админку
    return RedirectResponse(url="/admin")