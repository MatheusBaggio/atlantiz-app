from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="Atlantiz-API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# função que calcula
def calcular(total_itens):
    return round(total_itens * 1.07, 2)

@app.post("/orcamento")
def orcamento(dados: dict):
    itens = dados["itens"]
    total = sum(i["Total"] for i in itens)
    return {"cliente": dados["cliente"], "total": calcular(total)}