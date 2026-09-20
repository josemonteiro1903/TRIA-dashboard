# 📊 Dashboard TRIA — Estado do Pará

Dashboard interativo desenvolvido em **Python + Streamlit** para acompanhamento dos dados da **TRIA (Triagem de Risco para Insegurança Alimentar)**, ferramenta utilizada no âmbito do **SUS (Sistema Único de Saúde)**. O painel cruza os dados públicos da TRIA com dados de domicílios do **Censo IBGE 2022**, permitindo análises tanto em nível **nacional** quanto **regional (Pará)**, com recortes por Macro Região, Micro Região e Município.

---

## 🎯 Objetivo

O dashboard tem como finalidade:

- Acompanhar a **cobertura de aplicação da TRIA** (quantos domicílios já foram triados em relação ao total estimado de domicílios).
- Identificar o volume de **pessoas e domicílios em risco de insegurança alimentar**.
- Permitir recortes sociais específicos (pessoas com deficiência, população em situação de rua, povos e comunidades tradicionais, faixa etária, sexo do respondente, raça/cor autodeclarada etc.).
- Comparar indicadores entre estados (visão nacional) e entre regiões/municípios do Pará (visão regional).

---

## 🧰 Bibliotecas utilizadas

| Biblioteca | Função no projeto |
|---|---|
| `streamlit` | Framework principal para criação da interface web interativa (sidebar, abas, seletores, tabelas, gráficos). |
| `pandas` | Leitura, limpeza, transformação e agregação dos dados tabulares (CSV/Excel). |
| `plotly.express` | Geração dos gráficos de barras interativos exibidos no dashboard. |
| `unicodedata` | Normalização de texto para remoção de acentos (usado na padronização de nomes de municípios). |
| `requests` | Requisições HTTP para acessar a página oficial da TRIA e baixar o arquivo `.zip` com os dados mais recentes. |
| `zipfile` | Extração do arquivo `.xlsx` de dentro do `.zip` baixado, sem necessidade de salvar em disco. |
| `io.BytesIO` | Permite manipular o conteúdo do `.zip`/`.xlsx` diretamente em memória (buffer de bytes), evitando arquivos temporários. |

---

## 📁 Arquivos de dados esperados

O código espera encontrar os seguintes arquivos na pasta `data/`:

- **`data/IBGE.csv`** — base nacional do Censo IBGE 2022, contendo pelo menos as colunas `Municípios`, `UF` e `domicílios`.
- **`data/Dicionario_TRIA.csv`** — arquivo auxiliar (dicionário) que relaciona cada `Município` à sua `Macro Região` e `Micro Região` de saúde no Pará.

Além disso, o script baixa **dinamicamente** (via *scraping*) a base oficial da TRIA diretamente do site `https://relatorioaps.saude.gov.br/tria`, sempre buscando o `.zip` mais recente disponibilizado na página.

---

## 🧩 Funções principais

### `remover_acentos(texto)`
Recebe uma string e retorna a mesma string sem acentuação, usando normalização Unicode (`NFKD`) e filtrando os caracteres de combinação (acentos). Se o valor recebido não for uma string (ex: `NaN`), retorna o valor original sem alterações.

### `padronizar_municipio(nome)`
Função de padronização usada para garantir que o *merge* entre diferentes bases (IBGE, TRIA, dicionário de regiões) funcione corretamente, evitando divergências como "Belém" vs "BELEM " vs "Belém (PA)". Ela:
1. Remove acentos (reaproveitando `remover_acentos`);
2. Remove espaços nas extremidades e converte tudo para **maiúsculas**;
3. Remove os sufixos `" (PA)"` e `"(PA)"`;
4. Remove espaços duplicados internos.

### `carregar_tria()`
Função responsável por obter os dados oficiais da TRIA diretamente da fonte, em tempo real:
1. Faz uma requisição HTTP à página `https://relatorioaps.saude.gov.br/tria`;
2. Usa o **BeautifulSoup** para varrer todos os links `<a href="">` da página e identificar o primeiro que termine em `.zip`;
3. Baixa esse arquivo `.zip`;
4. Abre o `.zip` em memória (`zipfile.ZipFile` + `BytesIO`) e localiza o primeiro arquivo `.xlsx` dentro dele;
5. Lê esse `.xlsx` com `pandas.read_excel` e retorna o `DataFrame`.

Essa função está decorada com `@st.cache_data(ttl=86400)`, ou seja, o Streamlit armazena o resultado em cache por **24 horas (86400 segundos)**, evitando baixar o arquivo novamente a cada interação do usuário com o dashboard — só refaz o download quando o cache expira.


---

## 🔄 Fluxo de tratamento dos dados

### 1. Base IBGE — nacional (`df_ibge_nacional`)
- Lê `data/IBGE.csv`;
- Remove acentos e padroniza os nomes dos municípios;
- Ordena por município e remove linhas com valores nulos;
- Remove eventuais sufixos entre parênteses do nome do município via regex.

### 2. Base IBGE — regional (`df_ibge_regional`)
- Mesmo processo acima, mas filtrando apenas `UF == 'PA'`.

### 3. Base TRIA — nacional (`df_tria_nacional`)
- Carrega os dados via `carregar_tria()`;
- Padroniza nomes de município;
- Converte colunas percentuais (que vêm como texto com vírgula, ex: `"12,5"`) para `float` usando ponto decimal;
- **Cruzamento com o IBGE:** cria uma chave composta `MUNICÍPIO|UF` em ambas as bases para fazer o *merge* de forma mais precisa (evitando homônimos de municípios em estados diferentes);
- Preenche o total de domicílios de cada município usando o mapeamento por essa chave;
- Municípios sem correspondência recebem a **mediana nacional** de domicílios como valor de preenchimento (com aviso na tela via `st.warning`);
- Remove colunas auxiliares, linhas nulas e duplicatas por código `IBGE`.

### 4. Base TRIA — regional (`df_tria_regional`)
- Mesmo processo de carregamento e limpeza, mas filtrando `UF == 'PA'`;
- Faz *merge* com `Dicionario_TRIA.csv` para trazer as colunas `Macro Região` e `Micro Região`;
- Emite aviso se algum município não encontrar correspondência de região;
- Atribui a coluna `Total domicílios*` diretamente a partir de `df_ibge_regional["domicílios"]` (por posição de índice, não por chave — ver observação abaixo).

---

## 🖥️ Estrutura da interface (Streamlit)

O app é dividido em **duas abas** (`st.tabs`):

### Aba 1 — "TRIA Estado do Pará"
- **Filtros na barra lateral** (`st.sidebar`), em cascata:
  - Estado(s) → Macro Região(ões) → Micro Região(ões) (dependente da Macro selecionada) → Município(s) (dependente da Macro + Micro selecionadas);
- **Gráfico 1:** Total de domicílios vs. domicílios com TRIA aplicada, agrupável por Macro Região, Micro Região ou Município;
- **Gráfico 2:** Percentual de cobertura da TRIA (domicílios triados ÷ total de domicílios);
- **Gráfico 3:** Pessoas em domicílios em risco de insegurança alimentar;
- **Gráfico 4:** Número de domicílios em risco de insegurança alimentar, com seletor de **recorte social** (deficiência, situação de rua, povos tradicionais, menores de 18 anos, sexo do respondente, raça/cor autodeclarada etc.);
- **Gráfico 5:** Percentual de domicílios em risco de insegurança alimentar, também com seletor de recorte social;
- **Tabela final:** exibe os dados filtrados (`st.dataframe`).

### Aba 2 — "TRIA Nacional"
Réplica da lógica da Aba 1, mas agregando os dados por **UF** (estado) em vez de região/município, permitindo comparação entre estados brasileiros.

Todos os gráficos são construídos com `plotly.express.bar`, no formato de barras agrupadas (`barmode="group"`) quando há mais de uma série, com rótulos de valor exibidos fora da barra (`textposition="outside"`).

---

## ▶️ Como executar

```bash
pip install streamlit pandas plotly requests
streamlit run nome_do_arquivo.py
```

> A biblioteca `openpyxl` é necessária internamente pelo `pandas.read_excel` para ler arquivos `.xlsx`, mesmo não sendo importada diretamente no script.

Certifique-se de que a pasta `data/` (com `IBGE.csv` e `Dicionario_TRIA.csv`) esteja no mesmo diretório do script antes de rodar.

---
# TRIA – Triagem para Risco de Insegurança Alimentar
---
## 1. O que é a TRIA?

A **TRIA** (Triagem para Risco de Insegurança Alimentar) é um instrumento rápido, validado e de baixo custo, instituído no âmbito da Atenção Primária à Saúde (APS) pela **Portaria Interministerial MDS/MS nº 25/2024**.

Seu objetivo é rastrear o risco de **Insegurança Alimentar e Nutricional (IA)** em domicílios, atuando como ponte entre o **SUS** e o **Sistema Nacional de Segurança Alimentar e Nutricional (SISAN)** para o enfrentamento da fome e da má nutrição.

---

## 2. Como funciona a TRIA?

### 2.1. Estrutura do instrumento
A TRIA é composta por **apenas 2 perguntas objetivas** (respostas: **Sim** ou **Não**), referentes aos **últimos 3 meses**:

1. *"Nos últimos três meses, os alimentos acabaram antes que você tivesse dinheiro para comprar mais comida?"*
2. *"Nos últimos três meses, você comeu apenas alguns alimentos que ainda tinha, porque o dinheiro acabou?"*

### 2.2. Onde e quando aplicar
- **Profissionais**: qualquer profissional de saúde, educação, assistência social ou saúde pública.
- **Oportunidades**: consultas individuais, pré-natal, puericultura, visitas domiciliares, atividades em grupo, etc.
- **Registro**: integrada à **Ficha de Cadastro Individual (FCI)** do e-SUS APS, podendo ser acessada via:
  - Prontuário Eletrônico do Cidadão (PEC)
  - Coleta de Dados Simplificada (CDS)
  - Aplicativo Android *e-SUS Território*
  - Sistemas próprios integrados

### 2.3. Classificação dos resultados (3 cenários possíveis)

| Respostas | Classificação | Significado |
| :---: | :--- | :--- |
| **Não / Não** | **Segurança Alimentar (SAN)** | Sem risco. Domicílio com acesso regular e permanente a alimentos. |
| **Sim em 1 das 2** | **Insegurança Alimentar Leve** | Há preocupação/incerteza quanto ao acesso, ou baixa disponibilidade de alimentos *in natura*. |
| **Sim nas 2** | **Insegurança Alimentar Moderada ou Grave** | Risco elevado. Exige intervenções imediatas e encaminhamento para programas de garantia de SAN. |

### 2.4. Periodicidade de reaplicação
- **Domicílios com risco (IA)** → reaplicar a cada **3 a 6 meses**.
- **Domicílios sem risco (SAN)** → reaplicar a cada **6 a 12 meses**.

### 2.5. Conduta obrigatória após a triagem
Independentemente do resultado, deve-se realizar a **Vigilância Alimentar e Nutricional (VAN)**, que inclui:
- Avaliação do consumo alimentar
- Avaliação antropométrica (peso, altura, IMC)
- Monitoramento da má nutrição (desnutrição, excesso de peso e carências)

---

## 3. Qual a importância da TRIA na Atenção Primaria a  Saúde?

- **Protagonismo da APS** – Sendo o primeiro contato da comunidade com o sistema de saúde, a APS consegue rastrear precocemente a insegurança alimentar no território.
- **Organização do cuidado** – Os resultados permitem planejar o cuidado individual e familiar, além de articular o SUS com outros setores (assistência social, CRAS, programas de transferência de renda, etc.).
- **Subsídio a políticas públicas** – A identificação sistemática do risco orienta a criação e o fortalecimento de políticas focadas em Segurança Alimentar e Nutricional (SAN).
- **Enfrentamento da múltipla carga de má nutrição** – Ajuda a lidar com a coexistência de desnutrição, excesso de peso e carências nutricionais em populações vulneráveis.

---

## 4. Resumo executivo (em 1 minuto)

> A TRIA é um questionário de **2 perguntas (Sim/Não)** sobre falta de dinheiro para comprar comida nos últimos 3 meses.  
> - **2 "Não"** = segurança alimentar (sem risco).  
> - **1 "Sim"** = risco leve.  
> - **2 "Sim"** = risco moderado/grave (exige encaminhamento).  
> 
> Deve ser aplicado na APS, registrado no e-SUS e repetido a cada 3 a 12 meses, sempre acompanhado de avaliação nutricional. Sua grande importância está em **detectar precocemente o risco a fome e a má nutrição**, permitindo ações intersetoriais para garantir o direito humano à alimentação adequada.

---

## 📌 Fonte dos dados

- **TRIA:** [https://relatorioaps.saude.gov.br/tria](https://relatorioaps.saude.gov.br/tria)
- **IBGE:** Censo Demográfico 2022 (base de domicílios por município): https://censo2022.ibge.gov.br/panorama/recursos.html
- **Inseguranca-alimentar-na-APS.pdf:** https://share.google/jBKCYgKRrRRLWs0LI
- **NOTA TÉCNICA Nº 30/2025-CGAN/DEPPROS/SAPS/MS**: https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/notas-tecnicas/2025/nota-tecnica-no-30-2025-cgan-deppros-saps-ms
