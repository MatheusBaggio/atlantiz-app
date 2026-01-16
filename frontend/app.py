import streamlit as st, requests, pandas as pd

API = "https://atlantiz-api.fly.dev"

st.set_page_config(page_title="Atlantiz Orçamentos", layout="centered")
st.title("Atlantiz Orçamentos")
st.markdown("---")

cliente = st.text_input("Nome do cliente", "Consumidor")
qtd      = st.number_input("Quantidade de camisetas", 1, 500, 1)
tamanhos = st.columns(4)
qp = tamanhos[0].number_input("P (1,8)", 0)
qm = tamanhos[1].number_input("M (6,75)", 0)
qg = tamanhos[2].number_input("G (11,75)", 0)
qgg = tamanhos[3].number_input("GG (32,5)", 0)

custo_estampa = qp*1.8 + qm*6.75 + qg*11.75 + qgg*32.5
total_manual  = qtd * 25
itens = [{"Produto":"CAMISETA ALGODÃO","Qtd":qtd,"Total":total_manual,"Custo_Estampa":custo_estampa,"Categoria":"Vestuario"}]

if st.button("Calcular orçamento"):
    resp = requests.post(f"{API}/orcamento", json={"cliente":cliente,"itens":itens})
    if resp.ok:
        valor = resp.json()["total"]
        st.success(f"Total com 7 %: R$ {valor}")
        st.balloons()
    else:
        st.error("Erro na API")