from fastapi import FastAPI, HTTPException, UploadFile, File
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

# ---------- FUNÇÕES AUXILIARES ----------
def calcular(total_itens):
    return round(total_itens * 1.07, 2)

CSV_PATH = "/app/meus_precos.csv"

def ler_csv_precos():
    if not os.path.exists(CSV_PATH):
        return []
    return pd.read_csv(CSV_PATH).to_dict(orient="records")

def salvar_csv_precos(dados):
    df = pd.DataFrame(dados)
    df.to_csv(CSV_PATH, index=False)

# ---------- ENDPOINTS ----------
@app.post("/orcamento")
def orcamento(dados: dict):
    itens = dados["itens"]
    total = sum(i["Total"] for i in itens)
    return {"cliente": dados["cliente"], "total": calcular(total)}

@app.get("/precos")
def get_precos():
    """Devolve lista de produtos cadastrados"""
    return ler_csv_precos()

@app.post("/precos")
def post_precos(prod: dict):
    """Cadastra novo produto"""
    dados = ler_csv_precos()
    # remove duplicado pelo nome
    dados = [d for d in dados if d["Nome"] != prod["Nome"]]
    dados.append(prod)
    salvar_csv_precos(dados)
    return {"ok": True}

# ---------- UPLOAD DE ARQUIVOS (opcional, mantido) ----------
@app.post("/upload/camisetas")
def upload_camisetas(file: UploadFile = File(...)):
    with open("/app/tabela_camisetas.csv", "wb") as f:
        f.write(file.file.read())
    return {"ok": True}

@app.post("/upload/precos")
def upload_precos(file: UploadFile = File(...)):
    with open(CSV_PATH, "wb") as f:
        f.write(file.file.read())
    return {"ok": True}