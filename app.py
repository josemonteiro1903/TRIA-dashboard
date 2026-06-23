import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata


# Função para remover os acentos de um texto
def remover_acentos(texto):
    if not isinstance(texto, str):
        return texto
    # Normaliza o texto e remove os caracteres de acentuação
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def padronizar_municipio(nome):
    """
    Remove acentos, espaços extras, coloca em maiúsculas e
    remove o sufixo ' (PA)' ou '(PA)'.
    """
    if not isinstance(nome, str):
        return nome
    nome = remover_acentos(nome)
    nome = nome.strip().upper()
    nome = nome.replace(" (PA)", "").replace("(PA)", "")
    # Remove múltiplos espaços internos
    nome = " ".join(nome.split())
    return nome

# CONFIGURAÇÃO

st.set_page_config(
    page_title="Dashboard TRIA",
    layout="wide"
)

st.title("📊 Dashboard - TRIA no estado do Pará")

# LEITURA E TRATAMENTO DE DADOS

# DATAFRAME DADOS IBGE NACIONAL
df_ibge_nacional = pd.read_csv(
    "data/IBGE.csv"
)
df_ibge_nacional['Municipio '] = df_ibge_nacional['Municipio '].apply(remover_acentos)
df_ibge_nacional["Municipio "] = df_ibge_nacional["Municipio "].apply(padronizar_municipio)
df_ibge_nacional = df_ibge_nacional.sort_values(by='Municipio ')
df_ibge_nacional = df_ibge_nacional.dropna()
df_ibge_nacional['Municipio '] = df_ibge_nacional['Municipio '].str.replace(r'\s*\([^)]*\)', '', regex=True).str.strip()


# DATAFRAME DADOS IBGE REGIONAL
df_ibge_regional = pd.read_csv(
    "data/IBGE.csv"
)
df_ibge_regional = df_ibge_regional[df_ibge_regional["Municipio "].str.endswith("(PA)")]
df_ibge_regional['Municipio '] = df_ibge_regional['Municipio '].apply(remover_acentos)
df_ibge_regional["Municipio "] = df_ibge_regional["Municipio "].apply(padronizar_municipio)
df_ibge_regional = df_ibge_regional.sort_values(by='Municipio ')
df_ibge_regional = df_ibge_regional.dropna()

# DATAFRAME TRIA NACIONAL
df_tria_nacional = pd.read_csv("data/TRIA.csv")
df_tria_nacional['Município'] = df_tria_nacional['Município'].apply(remover_acentos)
df_tria_nacional["Município"] = df_tria_nacional["Município"].apply(padronizar_municipio)
df_tria_nacional = df_tria_nacional.sort_values(by='Município')

# 1. Filtra as colunas que começam com '%' e têm tipo 'object'
colunas_porcentagem = [
    col for col in df_tria_nacional.columns
    if col.startswith('%') and df_tria_nacional[col].dtype == 'object'
]

# 2. Aplica a substituição da vírgula por ponto e converte para float
for col in colunas_porcentagem:
    df_tria_nacional[col] = df_tria_nacional[col].astype(str).str.replace(',', '.', regex=False)
    df_tria_nacional[col] = pd.to_numeric(df_tria_nacional[col], errors='coerce')


# ------------------------------------------------------------
# ADICIONA DOMICÍLIOS DO IBGE À TRIA
# ------------------------------------------------------------

# Cria uma chave padronizada para os dois DataFrames
df_ibge_nacional["_municipio_key"] = (
    df_ibge_nacional["Municipio "]
    .apply(padronizar_municipio)
)

df_tria_nacional["_municipio_key"] = (
    df_tria_nacional["Município"]
    .apply(padronizar_municipio)
)

# Remove possíveis duplicados do IBGE
df_ibge_nacional = (
    df_ibge_nacional
    .drop_duplicates(subset="_municipio_key")
)

# Mediana nacional de domicílios
mediana_domicilios = df_ibge_nacional["Domicilios"].median()


# Cria dicionário Municipio -> Domicilios
mapa_domicilios = dict(
    zip(
        df_ibge_nacional["_municipio_key"],
        df_ibge_nacional["Domicilios"]
    )
)

# Faz a correspondência
df_tria_nacional["Total domicílios*"] = (
    df_tria_nacional["_municipio_key"]
    .map(mapa_domicilios)
)

# Conta quantos não encontraram correspondência
sem_correspondencia = (
    df_tria_nacional["Total domicílios*"]
    .isna()
    .sum()
)

# Preenche com a mediana
df_tria_nacional["Total domicílios*"] = (
    df_tria_nacional["Total domicílios*"]
    .fillna(mediana_domicilios)
)


df_tria_nacional = df_tria_nacional.dropna()
df_tria_nacional = df_tria_nacional.reset_index(drop=True)
df_tria_nacional = df_tria_nacional.drop_duplicates(subset=['IBGE'])

# DATAFRAME TRIA REGIONAL
df_tria_regional = pd.read_csv("data/TRIA.csv")
df_tria_regional = df_tria_regional.dropna()
df_tria_regional = df_tria_regional[df_tria_regional['UF'] == 'PA']
df_tria_regional['Município'] = df_tria_regional['Município'].apply(remover_acentos)
df_tria_regional["Município"] = df_tria_regional["Município"].apply(padronizar_municipio)
df_tria_regional = df_tria_regional.sort_values(by='Município')

# 1. Filtra as colunas que começam com '%' e têm tipo 'object'
colunas_porcentagem = [
    col for col in df_tria_regional.columns
    if col.startswith('%') and df_tria_regional[col].dtype == 'object'
]

# 2. Aplica a substituição da vírgula por ponto e converte para float
for col in colunas_porcentagem:
    df_tria_regional[col] = df_tria_regional[col].astype(str).str.replace(',', '.', regex=False)
    df_tria_regional[col] = pd.to_numeric(df_tria_regional[col], errors='coerce')

# Suponha que seu CSV tenha colunas: 'Município', 'Macro Região', 'Micro Região'
df_regioes = pd.read_csv("data/Dicionario.csv")

# Padronize o nome do município no CSV auxiliar
df_regioes["Município"] = df_regioes["Município"].apply(padronizar_municipio)

# Merge para adicionar as regiões
df_tria_regional = df_tria_regional.merge(
    df_regioes[["Município", "Macro Região", "Micro Região"]],
    on="Município",
    how="left"
)

# Verifica novamente se houve perda
sem_regiao = df_tria_regional["Macro Região"].isna().sum()
if sem_regiao > 0:
    st.warning(f"⚠️ {sem_regiao} município(s) não encontraram correspondência no arquivo de regiões.")

# Agora df_tria_regional está completo com domicílios e regiões

df_ibge_regional = df_ibge_regional.reset_index(drop=True)
df_tria_regional = df_tria_regional.reset_index(drop=True)
df_tria_regional["Total domicílios*"] = df_ibge_regional["Domicilios"]
df_tria_regional = df_tria_regional.dropna()

# ABAS

aba1, aba2 = st.tabs(
    ["TRIA Estado do Pará", "TRIA Nacional"]
)

with aba1:
    
    # FILTROS
 
    st.sidebar.header("Filtros")
    estado = st.sidebar.multiselect(
        "Selecione o(s) Estado(s)",
        options=sorted(df_tria_nacional["UF"].unique()),
        default=sorted(df_tria_nacional["UF"].unique())
    )
    
    macro = st.sidebar.multiselect(
        "Selecione a(s) Macro Região(ões)",
        options=sorted(df_tria_regional["Macro Região"].unique()),
        default=sorted(df_tria_regional["Macro Região"].unique())
    )

    micro_disponiveis = sorted(
        df_tria_regional[
            df_tria_regional["Macro Região"].isin(macro)
        ]["Micro Região"].unique()
    )

    micro = st.sidebar.multiselect(
        "Selecione a(s) Micro Região(ões)",
        options=micro_disponiveis,
        default=micro_disponiveis
    )

    municipios_disponiveis = sorted(
        df_tria_regional[
            (df_tria_regional["Macro Região"].isin(macro))
            &
            (df_tria_regional["Micro Região"].isin(micro))
        ]["Município"].unique()
    )

    municipios = st.sidebar.multiselect(
        "Selecione o(s) Município(s)",
        options=municipios_disponiveis,
        default=municipios_disponiveis
    )

    
    # DATAFRAMES POR NÍVEL
    
    dfn_estado = df_tria_nacional[
        df_tria_nacional["UF"].isin(estado)
    ]

    df_macro = df_tria_regional[
        df_tria_regional["Macro Região"].isin(macro)
    ]

    df_micro = df_tria_regional[
        (df_tria_regional["Macro Região"].isin(macro))
        &
        (df_tria_regional["Micro Região"].isin(micro))
    ]

    df_municipio = df_tria_regional[
        (df_tria_regional["Macro Região"].isin(macro))
        &
        (df_tria_regional["Micro Região"].isin(micro))
        &
        (df_tria_regional["Município"].isin(municipios))
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
    agrupado = (
        dados
        .groupby("UF", as_index=False)
        [
            [
                "Total domicílios*",
                "Domicílios com a TRIA aplicada"
            ]
        ]
        .sum()
    )

    agrupado_long = agrupado.melt(
        id_vars="UF",
        value_vars=[
            "Total domicílios*",
            "Domicílios com a TRIA aplicada"
        ],
        var_name="Tipo",
        value_name="Quantidade"
    )

    fig = px.bar(
        agrupado_long,
        x="UF",
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
        xaxis_title="UF",
        yaxis_title="Quantidade de domicílios"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # GRÁFICO 2
    

    st.subheader("Porcentagem de cobertura da TRIA")

    dados = dfn_estado

    agrupado_cobertura = (
        dados
        .groupby("UF", as_index=False)
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
        x="UF",
        y="% de cobertura da TRIA",
        title=f"Porcentagem de cobertura da TRIA por {nivel_agrupamento2}"
    )

    fig.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="UF",
        yaxis_title="Cobertura da TRIA (%)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    # GRÁFICO 3
    
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

    # GRÁFICO 4
    

    st.subheader(
        "Número de domicílios em risco de insegurança alimentar"
    )

    dados = dfn_estado
    
    nivel_recorte3 = st.selectbox(
        "Escolha o nível de recorte social:",
        ["Domicílios em risco de insegurança alimentar", "Domicílios em risco de insegurança alimentar com pessoas com deficiência", "Domicílios em risco de insegurança alimentar com pessoas em situação de rua", "Domicílios em risco de insegurança alimentar com pessoas de povo ou comunidade tradicional", "Domicílios em risco de insegurança alimentar com pessoas menores de 18 anos", "Domicílios em risco de insegurança alimentar com RF respondente do sexo feminino", "Domicílios em risco de insegurança alimentar com RF respondente do sexo masculino", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado pardo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado branco", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado amarelo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado preto", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado indígena"],
        key="grafico_recorte3"
    )

    agrupado_risco = (
        dados
        .groupby("UF", as_index=False)
        [nivel_recorte3]
        .sum()
    )

    fig = px.bar(
        agrupado_risco,
        x="UF",
        y=nivel_recorte3,
        text=nivel_recorte3,
        title=f"Número de domicílios em risco de insegurança alimentar por Estado"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="UF",
        yaxis_title="Quantidade de Domicilios"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # GRÁFICO 5
    
    st.subheader("Percentual de domicílios em risco de insegurança alimentar")


    nivel_recorte4 = st.selectbox(
        "Escolha o nível de visualização de recorte social:",
        ["Domicílios em risco de insegurança alimentar", "Domicílios em risco de insegurança alimentar com pessoas com deficiência", "Domicílios em risco de insegurança alimentar com pessoas em situação de rua", "Domicílios em risco de insegurança alimentar com pessoas de povo ou comunidade tradicional", "Domicílios em risco de insegurança alimentar com pessoas menores de 18 anos", "Domicílios em risco de insegurança alimentar com RF respondente do sexo feminino", "Domicílios em risco de insegurança alimentar com RF respondente do sexo masculino", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado pardo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado branco", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado amarelo", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado preto", "Domicílios em risco de insegurança alimentar com RF respondente autodeclarado indígena"],
        key="grafico_recorte4"
    )

    dados = dfn_estado

    agrupado_cobertura4 = (
        dados
        .groupby("UF", as_index=False)
        [
            [
                nivel_recorte4,
                "Domicílios com a TRIA aplicada"
            ]
        ]
        .sum()
    )

    agrupado_cobertura4["% de insegurança alimentar"] = (
        agrupado_cobertura4[nivel_recorte4]
        /
        agrupado_cobertura4["Domicílios com a TRIA aplicada"]
    )*100

    
    fig = px.bar(
        agrupado_cobertura4,
        x="UF",
        y="% de insegurança alimentar",
        title=f"% {nivel_recorte4} por Estado"
    )

    fig.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="UF",
        yaxis_title="Percentual de domicílios em risco de insegurança alimentar"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # TABELA

    st.subheader("Dados filtrados")
    st.dataframe(dfn_estado)