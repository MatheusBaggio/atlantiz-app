from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import pandas as pd
import os
import io
from fpdf import FPDF

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

def limpar_moeda(valor):
    if pd.isna(valor):
        return 0.0
    s = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def buscar_preco_malha(malha: str, qtd: int) -> float:
    csv_path = "/app/tabela_camisetas.csv"
    if not os.path.exists(csv_path):
        return 0.0
    try:
        df = pd.read_csv(csv_path, sep=';', skiprows=37, encoding='utf-8')
        df = df.head(10).rename(columns={df.columns[0]: 'Produto'})
        faixas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 26, 50]
        alvo = max([f for f in faixas if f <= qtd], default=1)
        linha = df[df['Produto'].astype(str).str.strip() == malha.strip()]
        if linha.empty:
            return 0.0
        valor_bruto = str(linha[str(alvo)].values[0])
        valor_limp = valor_bruto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(valor_limp)
    except Exception as e:
        print("Erro ao ler tabela:", e)
        return 0.0

# ---------- LEITURA / GRAVAÇÃO DE CSV DE PRODUTOS ----------
CSV_PRECOS = "/app/meus_precos.csv"

def ler_csv_precos():
    if not os.path.exists(CSV_PRECOS):
        return []
    df = pd.read_csv(CSV_PRECOS)
    return df.to_dict(orient="records")

def salvar_csv_precos(dados):
    df = pd.DataFrame(dados)
    df.to_csv(CSV_PRECOS, index=False)

# ---------- MODELOS ----------
class CamisetaItem(BaseModel):
    Produto: str
    Qtd: int
    Custo_Estampa: float

class PDF(FPDF):
    def header(self):
        if os.path.exists("/app/topo.png"):
            self.image("/app/topo.png", 0, 0, 210)
        self.set_font("Arial", "B", 26)
        self.set_text_color(255, 102, 0)
        self.cell(0, 45, "ORÇAMENTO", ln=True, align="L")
        self.ln(8)

    def footer(self):
        if os.path.exists("/app/rodape.png"):
            self.image("/app/rodape.png", 0, 278, 210)

# ---------- ENDPOINTS ----------
@app.post("/orcamento/camisetas")
def orcamento_camisetas(dados: dict):
    itens = [CamisetaItem(**i) for i in dados["itens"]]
    qtd_total = sum(i.Qtd for i in itens)
    novo_carrinho = []
    for item in itens:
        base = buscar_preco_malha(item.Produto, qtd_total)
        unit = (base + 5.0 + item.Custo_Estampa) * 1.07
        total = unit * item.Qtd
        novo_carrinho.append({
            "Produto": item.Produto,
            "Qtd": item.Qtd,
            "Unitario": round(unit, 2),
            "Total": round(total, 2),
            "Categoria": "Vestuario"
        })
    total_geral = sum(i["Total"] for i in novo_carrinho)
    return {"cliente": dados["cliente"], "itens": novo_carrinho, "total": round(total_geral, 2)}

@app.post("/orcamento")
def orcamento_outros(dados: dict):
    # para produtos terceiros (sem malha)
    total = sum(i["Total"] for i in dados["itens"])
    return {"cliente": dados["cliente"], "total": calcular(total)}

@app.get("/precos")
def get_precos():
    return ler_csv_precos()

@app.post("/precos")
def post_precos(prod: dict):
    dados = ler_csv_precos()
    dados = [d for d in dados if d["Nome"] != prod["Nome"]]
    dados.append(prod)
    salvar_csv_precos(dados)
    return {"ok": True}

@app.post("/pdf")
def gerar_pdf(dados: dict):
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"CLIENTE: {dados['cliente'].upper()}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"DATA DE EMISSÃO: {pd.Timestamp.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(8)

    # Tabela
    pdf.set_fill_color(245, 245, 245)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, " DESCRIÇÃO DO PRODUTO", border=1, fill=True)
    pdf.cell(20, 10, "QTD", border=1, fill=True, align="C")
    pdf.cell(35, 10, "UNITÁRIO", border=1, fill=True, align="C")
    pdf.cell(35, 10, "TOTAL", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Arial", "", 12)
    total_geral = 0
    for item in dados["itens"]:
        desc = item["Produto"]
        if item.get("Dimensoes"):
            desc += f" ({item['Dimensoes']})"
        pdf.cell(100, 10, f" {desc}", border=1)
        pdf.cell(20, 10, str(item["Qtd"]), border=1, align="C")
        pdf.cell(35, 10, f"R$ {item['Unitario']:.2f}", border=1, align="C")
        pdf.cell(35, 10, f"R$ {item['Total']:.2f}", border=1, align="C")
        pdf.ln()
        total_geral += item["Total"]

    pdf.ln(4)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(255, 102, 0)
    pdf.cell(120, 10, "", border=0)
    pdf.cell(35, 10, "TOTAL GERAL:", border=0, align="R")
    pdf.cell(35, 10, f"R$ {total_geral:.2f}", border=0, align="C")

    pdf.ln(12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "OBSERVAÇÕES E CONDIÇÕES:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 5, "- Prazo de produção: A combinar após aprovação da arte.", ln=True)
    pdf.cell(0, 5, "- Validade deste orçamento: 07 dias.", ln=True)
    pdf.cell(0, 5, "- Forma de pagamento: 50% no pedido e 50% na entrega.", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(255, 245, 235)
    pdf.cell(0, 10, f"  PAGAMENTO VIA PIX (CNPJ): 44.383.359/0001-60  ", border=0, ln=True, fill=True)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=Orcamento_{dados['cliente']}.pdf"})

@app.post("/upload/camisetas")
def upload_camisetas(file: UploadFile = File(...)):
    with open("/app/tabela_camisetas.csv", "wb") as f:
        f.write(file.file.read())
    return {"ok": True}

@app.post("/upload/precos")
def upload_precos(file: UploadFile = File(...)):
    with open(CSV_PRECOS, "wb") as f:
        f.write(file.file.read())
    return {"ok": True}