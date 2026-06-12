import streamlit as st
import pandas as pd
import plotly.express as px

# configurando
st.set_page_config(page_title="Dashboard TRIA", layout="wide")

st.title("📊 Dashboard - TRIA no estado do Pará")

# dados
df = pd.read_csv("data/TRIA_dados_filtrados.csv")

#Definindo as abas

aba1, aba2 = st.tabs(["TRIA Estado do Pará", "TRIA Nacional"])

with aba1:
    #Inicio da aba 1

    # filtros

    st.sidebar.header("Filtros")

    
    macro = st.sidebar.multiselect(
        "Selecione a(s) Macro Região(ões)",
        options=sorted(df["Macro Região"].unique()),
        default=sorted(df["Macro Região"].unique())
    )
    micro_disponiveis = sorted(
        df[df["Macro Região"].isin(macro)]["Micro Região"].unique()
    )

    micro = st.sidebar.multiselect(
        "Selecione a(s) Micro Regiões(s)",
        options=micro_disponiveis,
        default=micro_disponiveis
    )

    municipios_disponiveis = sorted(
        df[
            (df["Macro Região"].isin(macro))
            &
            (df["Micro Região"].isin(micro))
        ]["Município"].unique()
    )

    municipios = st.sidebar.multiselect(
        "Selecione o(s) Município(s)",
        options=municipios_disponiveis,
        default=municipios_disponiveis
    )

    df_filtrado = df[
        (df["Macro Região"].isin(macro))
        &
        (df["Micro Região"].isin(micro))
        &
        (df["Município"].isin(municipios))
    ]

    #Gráfico 1, comparação de domicilios e de tria's aplicadas
    st.subheader("Comparação de Domicílios")

    nivel_agrupamento = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"]
    )

    # Agrupamento dinâmico
    agrupado = (
        df_filtrado
        .groupby(nivel_agrupamento, as_index=False)
        [["Total domicílios*", "Domicílios com a TRIA aplicada"]]
        .sum()
    )

    # Transformando para formato longo
    agrupado_long = agrupado.melt(
        id_vars=nivel_agrupamento,
        value_vars=[
            "Total domicílios*",
            "Domicílios com a TRIA aplicada"
        ],
        var_name="Tipo",
        value_name="Quantidade"
    )

    # Gráfico
    fig = px.bar(
        agrupado_long,
        x=nivel_agrupamento,
        y="Quantidade",
        color="Tipo",
        barmode="group",
        text="Quantidade",
        title=f"Total de domicílios x Domicílios com TRIA aplicada por {nivel_agrupamento}"
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        xaxis_title=nivel_agrupamento,
        yaxis_title="Quantidade de domicílios"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Gráfico 2 - Percentual de domicílios em risco de insegurança alimentar

    st.subheader("Pessoas em domicílios em risco de insegurança alimentar")

    nivel_agrupamento2 = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"],
        key="grafico_risco"
    )

    agrupado_risco = (
        df_filtrado
        .groupby(nivel_agrupamento2, as_index=False)
        ["Pessoas em domicílios em risco de insegurança alimentar"]
        .sum()
    )

    fig = px.bar(
        agrupado_risco,
        x=nivel_agrupamento2,
        y="Pessoas em domicílios em risco de insegurança alimentar",
        text="Pessoas em domicílios em risco de insegurança alimentar",
        title=f"Pessoas em domicílios em risco de insegurança alimentar {nivel_agrupamento2}"
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        xaxis_title=nivel_agrupamento2,
        yaxis_title="Quantidade de Pessoas"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabela 
    st.subheader("Dados filtrados")
    st.dataframe(df_filtrado)
