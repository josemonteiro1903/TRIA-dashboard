import streamlit as st
import pandas as pd
import plotly.express as px


# CONFIGURAÇÃO

st.set_page_config(
    page_title="Dashboard TRIA",
    layout="wide"
)

st.title("📊 Dashboard - TRIA no estado do Pará")


# LEITURA DOS DADOS


df = pd.read_csv("data/TRIA_2026.csv")
dfn = pd.read_csv("data/TRIA_Nacional_2026.csv")

# ABAS

aba1, aba2 = st.tabs(
    ["TRIA Estado do Pará", "TRIA Nacional"]
)

with aba1:

    # FILTROS

    st.sidebar.header("Filtros")

    estado = st.sidebar.multiselect(
        "Selecione o(s) Estado(s)",
        options=sorted(dfn["UF"].unique()),
        default=sorted(dfn["UF"].unique())
    )
    
    macro = st.sidebar.multiselect(
        "Selecione a(s) Macro Região(ões)",
        options=sorted(df["Macro Região"].unique()),
        default=sorted(df["Macro Região"].unique())
    )

    micro_disponiveis = sorted(
        df[
            df["Macro Região"].isin(macro)
        ]["Micro Região"].unique()
    )

    micro = st.sidebar.multiselect(
        "Selecione a(s) Micro Região(ões)",
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

    
    # DATAFRAMES POR NÍVEL
    
    dfn_estado = dfn[
        dfn["UF"].isin(estado)
    ]

    df_macro = df[
        df["Macro Região"].isin(macro)
    ]

    df_micro = df[
        (df["Macro Região"].isin(macro))
        &
        (df["Micro Região"].isin(micro))
    ]

    df_municipio = df[
        (df["Macro Região"].isin(macro))
        &
        (df["Micro Região"].isin(micro))
        &
        (df["Município"].isin(municipios))
    ]

    
    # GRÁFICO 1
    
    st.subheader("Comparação de Domicílios")

    nivel_agrupamento = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"]
    )

    if nivel_agrupamento == "Macro Região":
        dados = df_macro

    elif nivel_agrupamento == "Micro Região":
        dados = df_micro

    else:
        dados = df_municipio

    agrupado = (
        dados
        .groupby(nivel_agrupamento, as_index=False)
        [
            [
                "Total domicílios*",
                "Domicílios com a TRIA aplicada"
            ]
        ]
        .sum()
    )

    agrupado_long = agrupado.melt(
        id_vars=nivel_agrupamento,
        value_vars=[
            "Total domicílios*",
            "Domicílios com a TRIA aplicada"
        ],
        var_name="Tipo",
        value_name="Quantidade"
    )

    fig = px.bar(
        agrupado_long,
        x=nivel_agrupamento,
        y="Quantidade",
        color="Tipo",
        barmode="group",
        text="Quantidade",
        title=f"Total de domicílios x Domicílios com TRIA aplicada por {nivel_agrupamento}"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title=nivel_agrupamento,
        yaxis_title="Quantidade de domicílios"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    
    # GRÁFICO 2
    

    st.subheader("Porcentagem de cobertura da TRIA")

    nivel_agrupamento2 = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"],
        key="grafico_cobertura"
    )

    if nivel_agrupamento2 == "Macro Região":
        dados = df_macro

    elif nivel_agrupamento2 == "Micro Região":
        dados = df_micro

    else:
        dados = df_municipio

    agrupado_cobertura = (
        dados
        .groupby(nivel_agrupamento2, as_index=False)
        [
            [
                "Total domicílios*",
                "Domicílios com a TRIA aplicada"
            ]
        ]
        .sum()
    )

    agrupado_cobertura["% de cobertura da TRIA"] = (
        agrupado_cobertura["Domicílios com a TRIA aplicada"]
        /
        agrupado_cobertura["Total domicílios*"]
    ) * 100

    fig = px.bar(
        agrupado_cobertura,
        x=nivel_agrupamento2,
        y="% de cobertura da TRIA",
        title=f"Porcentagem de cobertura da TRIA por {nivel_agrupamento2}"
    )

    fig.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title=nivel_agrupamento2,
        yaxis_title="Cobertura da TRIA (%)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    
    # GRÁFICO 3
    

    st.subheader(
        "Pessoas em domicílios em risco de insegurança alimentar"
    )

    nivel_agrupamento3 = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"],
        key="grafico_risco"
    )

    if nivel_agrupamento3 == "Macro Região":
        dados = df_macro

    elif nivel_agrupamento3 == "Micro Região":
        dados = df_micro

    else:
        dados = df_municipio

    agrupado_risco = (
        dados
        .groupby(nivel_agrupamento3, as_index=False)
        [
            "Pessoas em domicílios em risco de insegurança alimentar"
        ]
        .sum()
    )

    fig = px.bar(
        agrupado_risco,
        x=nivel_agrupamento3,
        y="Pessoas em domicílios em risco de insegurança alimentar",
        text="Pessoas em domicílios em risco de insegurança alimentar",
        title=f"Pessoas em domicílios em risco de insegurança alimentar por {nivel_agrupamento3}"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title=nivel_agrupamento3,
        yaxis_title="Quantidade de Pessoas"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    
    # GRÁFICO 4
    

    st.subheader(
        "Número de domicílios em risco de insegurança alimentar"
    )

    nivel_agrupamento4 = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"],
        key="grafico_numero_domicilios"
    )
    nivel_recorte = st.selectbox(
        "Escolha o nível de recorte social:",
        ["Domicílios em risco de insegurança alimentar", "Domicílios em risco de insegurança alimentar com pessoas com deficiência", "Domicílios em risco de insegurança alimentar com pessoas em situação de rua", "Domicílios em risco de insegurança alimentar com pessoas de povo ou comunidade tradicional", "Domicílios em risco de insegurança alimentar com pessoas menores de 18 anos", "Domicílios em risco de insegurança alimentar com RF respondente do sexo feminino", "Domicílios em risco de insegurança alimentar com RF respondente do sexo masculino", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado pardo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado branco", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado amarelo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado preto", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado indígena"],
        key="grafico_recorte"
    )

    if nivel_agrupamento4 == "Macro Região":
        dados = df_macro

    elif nivel_agrupamento4 == "Micro Região":
        dados = df_micro

    else:
        dados = df_municipio
    

    agrupado_risco = (
        dados
        .groupby(nivel_agrupamento4, as_index=False)
        [nivel_recorte]
        .sum()
    )

    fig = px.bar(
        agrupado_risco,
        x=nivel_agrupamento4,
        y=nivel_recorte,
        text=nivel_recorte,
        title=f"Número de domicílios em risco de insegurança alimentar por {nivel_agrupamento3}"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title=nivel_agrupamento4,
        yaxis_title="Quantidade de Domicilios"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    
    # GRÁFICO 5
    
    st.subheader("Percentual de domicílios em risco de insegurança alimentar")

    nivel_agrupamento5 = st.selectbox(
        "Escolha o nível de visualização:",
        ["Macro Região", "Micro Região", "Município"],
        key="grafico_porcentagem"
    )

    nivel_recorte2 = st.selectbox(
        "Escolha o nível de visualização de recorte social:",
        ["Domicílios em risco de insegurança alimentar", "Domicílios em risco de insegurança alimentar com pessoas com deficiência", "Domicílios em risco de insegurança alimentar com pessoas em situação de rua", "Domicílios em risco de insegurança alimentar com pessoas de povo ou comunidade tradicional", "Domicílios em risco de insegurança alimentar com pessoas menores de 18 anos", "Domicílios em risco de insegurança alimentar com RF respondente do sexo feminino", "Domicílios em risco de insegurança alimentar com RF respondente do sexo masculino", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado pardo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado branco", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado amarelo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado preto", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado indígena"],
        key="grafico_recorte2"
    )

    

    if nivel_agrupamento5 == "Macro Região":
        dados = df_macro

    elif nivel_agrupamento5 == "Micro Região":
        dados = df_micro

    else:
        dados = df_municipio

    agrupado_cobertura2 = (
        dados
        .groupby(nivel_agrupamento5, as_index=False)
        [
            [
                nivel_recorte2,
                "Domicílios com a TRIA aplicada"
            ]
        ]
        .sum()
    )

    agrupado_cobertura2["% de insegurança alimentar"] = (
        agrupado_cobertura2[nivel_recorte2]
        /
        agrupado_cobertura2["Domicílios com a TRIA aplicada"]
    )*100

    
    fig = px.bar(
        agrupado_cobertura2,
        x=nivel_agrupamento5,
        y="% de insegurança alimentar",
        title=f"% {nivel_recorte2} por {nivel_agrupamento5}"
    )

    fig.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title=nivel_agrupamento5,
        yaxis_title="Percentual de domicílios em risco de insegurança alimentar"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    
    
    # TABELA

    st.subheader("Dados filtrados")
    st.dataframe(df_municipio)

with aba2:

    # GRÁFICO 1
    
    st.subheader("Comparação de Domicílios")

    dados = dfn_estado

    agrupadon = (
        dados
        .groupby("UF", as_index=False)
        [
            [
                "Pessoas em domicílios em risco de insegurança alimentar"
            ]
        ]
        .sum()
    )

    agrupadon_long = agrupadon.melt(
        id_vars="UF",
        value_vars=[
            "Pessoas em domicílios em risco de insegurança alimentar"
        ],
        var_name="Tipo",
        value_name="Quantidade"
    )

    fig = px.bar(
        agrupadon_long,
        x="UF",
        y="Quantidade",
        color="Tipo",
        barmode="group",
        text="Quantidade",
        title=f"Pessoas em domicílios em risco de insegurança alimentar por Estado"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="UF",
        yaxis_title="Quantidade de pessoas em domicílios em risco de insegurança alimentar"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    # TABELA

    st.subheader("Dados filtrados")
    st.dataframe(dfn_estado)