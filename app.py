import streamlit as st
import pandas as pd
import plotly.express as px
from pandas import NA

# ============== Configurações de Página =====================
st.set_page_config(
    page_title="Painel de Eventos - Nimbus",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊",
)

DEFAULT_HEIGHT = 600

DEFAULT_LAYOUT = dict(
    paper_bgcolor="#F8FAFC",
    plot_bgcolor="#F8FAFC",
    font=dict(color="#003366"),
    title_x=0.4
)


st.markdown("""
<style>
/* ============================== */
/* 🎨 Tema personalizado PMDF      */
/* ============================== */

/* Fundo geral e texto */
body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #F8FAFC !important;
    color: #1E293B !important;
}

/* Container das abas */
div[data-baseweb="tab-list"] {
    justify-content: center !important;      /* centraliza as abas */
    gap: 0.8rem !important;                  /* espaçamento entre abas */
    margin-top: 0.5rem !important;
}

/* Aba ativa */
div[data-baseweb="tab-list"] button[aria-selected="true"] {
    background-color: #003366 !important;    /* azul PMDF */
    color: #FFFFFF !important;
    padding: 5px 10px !important;
    border-radius: 5px 5px 0 0 !important;
    font-weight: 700 !important;
    box-shadow: 0px -3px 6px rgba(0, 0, 0, 0.1);
}

/* Abas inativas */
div[data-baseweb="tab-list"] button[aria-selected="false"] {
    background-color: #E2E8F0 !important;
    color: #003366 !important;
    padding: 5px 10px !important;
    border-radius: 5px 5px 0 0 !important;
    font-weight: 600 !important;
    border: 1px solid #CBD5E1 !important;
    transition: all 0.2s ease-in-out;
}

/* Hover nas abas inativas */
div[data-baseweb="tab-list"] button[aria-selected="false"]:hover {
    background-color: #C8A100 !important;  /* dourado PMDF */
    color: #FFFFFF !important;
    transform: scale(1.03);
}

/* Efeito de foco na aba ativa */
div[data-baseweb="tab-list"] button[aria-selected="true"]:hover {
    background-color: #00224D !important;
}

/* ============================== */
/* Layout e estética geral        */
/* ============================== */

/* Centralizar os títulos h1/h2 */
h1, h2 {
    text-align: center !important;
    color: #003366 !important;
    font-weight: 700 !important;
}

/* Links e botões */
a, .stButton>button {
    background-color: #003366 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
a:hover, .stButton>button:hover {
    background-color: #C8A100 !important;
    color: #003366 !important;
}

/* Linhas divisórias */
hr {
    border: 1px solid #003366 !important;
}

/* Cards e métricas */
[data-testid="stMetricValue"] {
    color: #003366 !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)


# ============== Funções Utilitárias =========================
def normalize_columns(df):
    df.columns = [c.lower().strip().replace(' ', '_').replace('-', '_') for c in df.columns]
    return df

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel("df_nimbus_att.xlsx")
    df = normalize_columns(df)
    return df

# ============== Carregar Dados ===============================
df = load_data()
df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce")
df["fim"] = pd.to_datetime(df["fim"], errors="coerce")
df["publico_previsto"] = pd.to_numeric(df["publico_previsto"], errors="coerce")
df["duracao_h"] = round((df["fim"] - df["inicio"]).dt.total_seconds() / 3600, 2)
df["mes"] = df["inicio"].dt.to_period("M").astype(str)
df["hora_inicio"] = df["inicio"].dt.hour
df["hora_fim"] = df["fim"].dt.hour
df["dia_semana"] = df["inicio"].dt.dayofweek
df["dia_semana_nome"] = df["dia_semana"].map({
    0: "Segunda-feira", 
    1: "Terça-feira", 
    2: "Quarta-feira", 
    3: "Quinta-feira", 
    4: "Sexta-feira", 
    5: "Sábado", 
    6: "Domingo"
})

# Ajuste para remover eventos com duração negativa ou > 72h
df.loc[(df['duracao_h'] < 0) | (df['duracao_h'] > 72), 'duracao_h'] = NA    

# Ajustar automaticamente quando há erro de ano
mask_ano_errado = df['fim'].dt.year - df['inicio'].dt.year > 0
df.loc[mask_ano_errado, 'fim'] = df.loc[mask_ano_errado, 'fim'] - pd.DateOffset(years=1)

# Guardar cópia do DataFrame completo (antes dos filtros)
df_completo = df.copy()

# ============== Sidebar =====================================
st.sidebar.title("⚙️ Filtros")
st.sidebar.caption("Use os filtros para refinar todas as análises do painel.")

data_inicio = df["inicio"].min()
data_fim = df["inicio"].max()
periodo = st.sidebar.date_input("Período", value=(data_inicio, data_fim))

# Filtrar por período (converter date para datetime)
if len(periodo) == 2:
    df = df[df["inicio"].between(pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1]))]

if "cidade" in df.columns:
    cidades = sorted(df["cidade"].dropna().unique().tolist())
    cidades_selecionadas = st.sidebar.multiselect("Cidades", cidades, default=cidades)
    df = df[df["cidade"].isin(cidades_selecionadas)]

if "cpr" in df.columns:
    cprs = df["cpr"].unique()
    cprs_selecionadas = st.sidebar.multiselect("CPRs", cprs, default=cprs)
    df = df[df["cpr"].isin(cprs_selecionadas)]

if "upm" in df.columns:
    upms = sorted(df["upm"].dropna().unique().tolist())
    upms_selecionadas = st.sidebar.multiselect("UPMs", upms, default=upms)
    df = df[df["upm"].isin(upms_selecionadas)]

if "natureza" in df.columns:
    naturezas = sorted(df["natureza"].dropna().unique().tolist())
    naturezas_selecionadas = st.sidebar.multiselect("Naturezas", naturezas, default=naturezas)
    df = df[df["natureza"].isin(naturezas_selecionadas)]

if "os_gerada" in df.columns:
    os_geradas = df["os_gerada"].unique()
    os_geradas_selecionadas = st.sidebar.multiselect("OS Geradas", os_geradas, default=os_geradas)
    df = df[df["os_gerada"].isin(os_geradas_selecionadas)]

if "local_caracteristica" in df.columns:
    local_caracteristicas = sorted(df["local_caracteristica"].dropna().unique().tolist())
    local_caracteristicas_selecionadas = st.sidebar.multiselect("Local - Característica", local_caracteristicas, default=local_caracteristicas)
    df = df[df["local_caracteristica"].isin(local_caracteristicas_selecionadas)]    

st.title("📊 Painel de Eventos — Nimbus")

# Mostrar totais gerais (antes dos filtros)
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Total na planilha:** {len(df_completo):,.0f} eventos".replace(',', '.'))
with col2:
    st.info(f"**Após filtros:** {len(df):,.0f} eventos".replace(',', '.'))
with col3:
    if len(df_completo) > 0:
        pct = (len(df) / len(df_completo)) * 100
        st.info(f"**Exibindo:** {pct:.1f}% do total")

#st.dataframe(df)

st.markdown("---")

# ============== Seções em Abas ===============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1) 🗂️ Visão Geral",
    "2) 🌍 Distribuição Geográfica",
    "3) 🏷️ Natureza dos Eventos",
    "4) 📅 Análise Temporal",
    "5) 🚔 Eficiência Operacional"
])

# ============================================================
# 1. VISÃO GERAL
# ============================================================
with tab1:
    st.subheader("Indicadores Gerais (Dados Filtrados)")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Eventos (filtrados)", f"{len(df):,.0f}".replace(',', '.'))
    with c2:
        st.metric("Público Total", f"{df['publico_previsto'].sum():,.0f}".replace(',', '.'))
    with c3:
        st.metric("Público Médio", f"{df['publico_previsto'].mean():,.0f}".replace(',', '.'))
    with c4:
        st.metric("Eventos com OS gerada (SIM)", df[df["os_gerada"] == "SIM"].shape[0])
    with c5: 
        st.metric("Público Total (OS gerada)", f"{df[df['os_gerada'] == 'SIM']['publico_previsto'].sum():,.0f}".replace(',', '.'))
    
    c6, c7 = st.columns(2)

    with c6:
        if 'local_caracteristica' in df.columns:
            df["local_carac_legendas"] = df["local_caracteristica"].replace({
                "PUBA": "Público Aberto",
                "PUBF": "Público Fechado",
                "PRIA": "Privado Aberto",
                "PRIF": "Privado Fechado"
            })
            fig = px.pie(df, names="local_carac_legendas", title="Distribuição por característica do local", height=DEFAULT_HEIGHT)
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível calcular a duração (datas/horários de início e fim ausentes).")

    with c7:
        if 'cpr' in df.columns:
            fig = px.pie(df, names="cpr", title="Distribuição por CPRs", height=DEFAULT_HEIGHT)
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível calcular a duração (datas/horários de início e fim ausentes).")

# ============================================================
# 2. DISTRIBUIÇÃO GEOGRÁFICA
# ============================================================
with tab2:
    st.subheader("Distribuição Geográfica, UPMs e CPRs")

    c1, c2 = st.columns(2)

    with c1:
        if "upm" in df.columns:
            por_upm = df.groupby("upm").size().reset_index(name="eventos")
            fig = px.bar(por_upm.sort_values("eventos", ascending=True), x="eventos", y="upm", orientation="h", title="Eventos por UPM", 
                        height=DEFAULT_HEIGHT, labels={"eventos": "Eventos", "upm": "UPM"})
            fig.update_layout(**DEFAULT_LAYOUT)            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível calcular a distribuição geográfica (coluna de cidade ausente).")

    with c2:
        if "cpr" in df.columns:
            por_cpr = df.groupby("cpr").size().reset_index(name="eventos")
            fig = px.bar(por_cpr, x="cpr", y="eventos", title="Eventos por CPR", height=DEFAULT_HEIGHT,
                        labels={"eventos": "Eventos", "cpr": "CPR"})
            fig.update_layout(**DEFAULT_LAYOUT)            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível calcular a distribuição geográfica (coluna de CPR ausente).")

    if "cidade" in df.columns:
        por_cidade = df.groupby("cidade").size().reset_index(name="eventos")
        fig = px.bar(por_cidade.sort_values("eventos", ascending=False), x="cidade", y="eventos", title="Eventos por cidade", height=DEFAULT_HEIGHT,
                    labels={"eventos": "Eventos", "cidade": "Cidade"})
        fig.update_layout(**DEFAULT_LAYOUT)            
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não foi possível calcular a distribuição geográfica (coluna de cidade ausente).")

# ============================================================
# 3. NATUREZA DOS EVENTOS
# ============================================================
with tab3:
    st.subheader("Natureza dos Eventos")

    c1, c2 = st.columns(2)

    if "natureza" in df.columns:
        with c1: 
            por_natureza = df["natureza"].dropna().value_counts().reset_index(name="qtd")
            por_natureza.columns = ['natureza', 'qtd']
            fig = px.bar(por_natureza.sort_values('qtd', ascending=False), x='natureza', y='qtd', title="Quantidade por natureza", height=DEFAULT_HEIGHT,
                        labels={"qtd": "Quantidade", "natureza": "Natureza"})
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if "publico_previsto" in df.columns:
                bp_df = df.dropna(subset=["natureza", "publico_previsto"])
                if not bp_df.empty:
                    fig = px.box(bp_df, x="natureza", y="publico_previsto", title="Distribuição de público previsto por natureza", height=DEFAULT_HEIGHT)
                    fig.update_layout(xaxis_title="Natureza", yaxis_title="Público previsto")
                    fig.update_layout(**DEFAULT_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados suficientes para o boxplot.")
            else:
                st.info("Coluna de público previsto não encontrada para o boxplot.")
    else:
        st.info("Coluna de natureza não encontrada.")

# ============================================================
# 4. ANÁLISE TEMPORAL
# ============================================================
with tab4:
    st.subheader("Distribuição temporal")


    st.metric("Duração média dos eventos", f"{df['duracao_h'].mean(skipna=True):,.1f} horas")

    c1, c2 = st.columns(2)

    with c1:
        if "dia_semana_nome" in df.columns:
            por_dia_semana = df.groupby("dia_semana_nome").size().reset_index(name="eventos")
            fig = px.area(por_dia_semana, x="dia_semana_nome", y="eventos", title="Eventos por dia da semana", height=DEFAULT_HEIGHT,
                        labels={"eventos": "Eventos", "dia_semana_nome": "Dia da semana"})
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível calcular a distribuição por dia da semana (coluna de dia da semana ausente).")

    with c2:
        if 'mes' in df.columns:
            por_mes = df.groupby("mes").size().reset_index(name="eventos")
            fig = px.area(por_mes, x='mes', y='eventos', title="Tendência mensal de eventos", height=DEFAULT_HEIGHT,
                        labels={"eventos": "Eventos", "mes": "Mês"})
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível calcular a tendência mensal (coluna de data ausente).")


    if "natureza" in df.columns:
        media_por_natureza = df.groupby("natureza")["duracao_h"].mean().reset_index(name="duracao_h").sort_values("duracao_h", ascending=False)
        fig = px.bar(media_por_natureza, x="natureza", y="duracao_h", title="Duração média dos eventos por natureza", height=DEFAULT_HEIGHT,
                    labels={"duracao_h": "Duração média", "natureza": "Natureza"})
        fig.update_layout(**DEFAULT_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não foi possível calcular a duração média dos eventos por natureza (coluna de natureza ausente).")

# ============================================================
# 5. EFICIÊNCIA OPERACIONAL
# ============================================================
with tab5:
    st.subheader("Indicadores Operacionais")

    if "os_gerada" in df.columns:
            pct_os = (df["os_gerada"].eq("SIM").mean() * 100) if len(df) else 0
            st.metric("Percentual com OS gerada", f"{pct_os:.1f}%")
    else:
        st.info("Coluna de OS gerada não encontrada.")

    c1, c2 = st.columns(2)

    with c1:
        if "upm" in df.columns:
            por_upm_os = (df.groupby(["upm", "os_gerada"]).size().reset_index(name="eventos").sort_values("eventos", ascending=False))
            fig = px.bar(por_upm_os, x="upm", y="eventos", color="os_gerada", title="Eventos por UPM e OS gerada", height=DEFAULT_HEIGHT,
                        labels={"eventos": "Eventos", "upm": "", "os_gerada": "OS gerada"})
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna de UPM não encontrada.")

    with c2:
        if "cpr" in df.columns:
            por_cpr_os = (df.groupby(["cpr", "os_gerada"]).size().reset_index(name="eventos").sort_values("eventos", ascending=False))
            fig = px.bar(por_cpr_os, x="cpr", y="eventos", color="os_gerada", title="Eventos por CPR e OS gerada", height=DEFAULT_HEIGHT,
                        labels={"eventos": "Eventos", "cpr": "", "os_gerada": "OS gerada"})
            fig.update_layout(**DEFAULT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna de CPR não encontrada.")
