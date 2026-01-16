import streamlit as st
import requests
import pandas as pd

API = "https://atlantiz-api.fly.dev"

st.set_page_config(page_title="Atlantiz Orçamentos", layout="wide")
st.title("Atlantiz Orçamentos")

# ---------- ABA 1: ORÇAMENTO ----------
aba1, aba2 = st.tabs(["📝 Gerar Orçamento", "⚙️ Cadastrar Produtos"])

with aba2:
    st.header("Cadastrar / Editar Produtos Terceiros")
    with st.form("cadastro"):
        nome = st.text_input("Nome do material (ex: Banner, Adesivo)")
        tipo = st.selectbox("Tipo de cobrança", ["M² (Área)", "Fixo (Unidade)"])
        col = st.columns(3)
        f1 = col[0].number_input("Preço base (F1)", 0.0)
        q2 = col[1].number_input("Qtd mín F2", 0)
        f2 = col[1].number_input("Preço F2", 0.0)
        q3 = col[2].number_input("Qtd mín F3", 0)
        f3 = col[2].number_input("Preço F3", 0.0)
        submitted = st.form_submit_button("Salvar")
        if submitted and nome:
            payload = {"Nome": nome, "Tipo": tipo, "F1": f1, "Q2": q2, "F2": f2, "Q3": q3, "F3": f3}
            r = requests.post(f"{API}/precos", json=payload)
            if r.ok:
                st.success(f"Produto '{nome}' salvo!")
            else:
                st.error("Erro ao salvar – tente novamente.")

with aba1:
    cliente = st.text_input("Cliente", "Consumidor")
    tipo_prod = st.radio("Tipo", ["Camisetas", "Outros"], horizontal=True)

    if tipo_prod == "Camisetas":
        malha = st.selectbox("Malha", ["CAMISETA ALGODÃO", "CAMISETA OVERSIZED MALHÃO", "CAMISA POLO", "MOLETOM", "MOLETOM CANGURU"])
        qtd = st.number_input("Quantidade", 1, 500, 1)
        cols = st.columns(4)
        qp = cols[0].number_input("P (1,8)", 0)
        qm = cols[1].number_input("M (6,75)", 0)
        qg = cols[2].number_input("G (11,75)", 0)
        qgg = cols[3].number_input("GG (32,5)", 0)
        custo_estampa = qp * 1.8 + qm * 6.75 + qg * 11.75 + qgg * 32.5
        valor_base = 25
        unit = (valor_base + 5 + custo_estampa) * 1.07
        total_item = unit * qtd
        if st.button("Adicionar camisetas"):
            st.session_state.carrinho.append({
                "Produto": malha,
                "Qtd": qtd,
                "Unitario": round(unit, 2),
                "Total": round(total_item, 2),
                "Categoria": "Vestuario"
            })

    else:  # OUTROS PRODUTOS
        r = requests.get(f"{API}/precos")
        if r.ok:
            produtos = r.json()
            nomes = [p["Nome"] for p in produtos]
            if nomes:
                sel = st.selectbox("Material cadastrado", nomes)
                prod = next(p for p in produtos if p["Nome"] == sel)
                qtd_outros = st.number_input("Quantidade", 1)
                modo = st.selectbox("Modo de preço", ["Automático", "F1", "F2", "F3"])
                if prod["Tipo"] == "M² (Área)":
                    lar = st.number_input("Largura (m)", 0.1, 10.0, 1.0)
                    alt = st.number_input("Altura (m)", 0.1, 10.0, 1.0)
                    area = lar * alt
                    if modo == "F3" and prod["Q3"] > 0 and area * qtd_outros >= prod["Q3"]:
                        preco = prod["F3"]
                    elif modo == "F2" and prod["Q2"] > 0 and area * qtd_outros >= prod["Q2"]:
                        preco = prod["F2"]
                    else:
                        preco = prod["F1"]
                    unitario = area * preco
                    dimensoes = f"{lar}x{alt}m"
                else:  # preço fixo
                    if modo == "F3" and prod["Q3"] > 0 and qtd_outros >= prod["Q3"]:
                        preco = prod["F3"]
                    elif modo == "F2" and prod["Q2"] > 0 and qtd_outros >= prod["Q2"]:
                        preco = prod["F2"]
                    else:
                        preco = prod["F1"]
                    unitario = preco
                    dimensoes = ""
                total_outros = unitario * qtd_outros
                st.info(f"Unitário: R$ {unitario:.2f}")
                if st.button("Adicionar material"):
                    st.session_state.carrinho.append({
                        "Produto": sel,
                        "Qtd": qtd_outros,
                        "Unitario": round(unitario, 2),
                        "Total": round(total_outros, 2),
                        "Categoria": "Outros",
                        "Dimensoes": dimensoes
                    })
            else:
                st.warning("Nenhum produto cadastrado ainda. Use a aba ⚙️ Cadastrar Produtos.")
        else:
            st.error("Não consegui buscar produtos cadastrados.")

# ---------- CARRINHO ----------
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

if st.session_state.carrinho:
    st.markdown("---")
    st.subheader("Carrinho")
    for idx, item in enumerate(st.session_state.carrinho):
        col1, col2, col3, col4, col5 = st.columns([4, 1, 2, 2, 1])
        desc = item["Produto"]
        if item.get("Dimensoes"):
            desc += f" ({item['Dimensoes']})"
        col1.write(desc)
        col2.write(str(item["Qtd"]))
        col3.write(f"R$ {item['Unitario']:.2f}")
        col4.write(f"R$ {item['Total']:.2f}")
        if col5.button("🗑️", key=f"del{idx}"):
            st.session_state.carrinho.pop(idx)
            st.rerun()

    total_geral = sum(i["Total"] for i in st.session_state.carrinho)
    st.markdown(f"### Total geral: **R$ {total_geral:.2f}**")

    if st.button("📄 Gerar PDF (download)"):
        pdf_resp = requests.post(f"{API}/pdf", json={"cliente": cliente, "itens": st.session_state.carrinho})
        if pdf_resp.status_code == 200:
            st.download_button("📥 Baixar Orçamento", data=pdf_resp.content, file_name=f"Orcamento_{cliente}.pdf")
        else:
            st.error("Erro ao gerar PDF.")