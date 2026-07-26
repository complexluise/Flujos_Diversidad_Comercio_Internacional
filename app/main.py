import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Diversidad Económica",
    page_icon="🐲",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
    }
)

years = np.arange(1995, 2023)

ruta_datos = "data/processed_data/BACI_HS92_V202401b/"


@st.cache_data
def load_data_diversity_countries() -> pd.DataFrame:
    df = pd.read_csv(f"{ruta_datos}countries_diversity.csv").drop(columns="Unnamed: 0")
    # `is_latinoamerica` viene como booleano, pero la paleta se define con
    # etiquetas de texto. Sin esta conversión el color_discrete_map no coincide
    # con ningún valor y Plotly ignora la paleta por completo.
    df["is_latinoamerica"] = df["is_latinoamerica"].map(
        {True: "Latinoamérica", False: "No Latinoamérica"}
    )
    return df


@st.cache_data
def load_data_diversity_classification_region() -> pd.DataFrame:
    return pd.read_csv(f"{ruta_datos}diversity_by_year_region.csv")


@st.cache_data
def load_data_diversity_classification_advanced() -> pd.DataFrame:
    return pd.read_csv(f"{ruta_datos}diversity_by_year_advanced_not-advanced.csv")


df_diversidad_paises = load_data_diversity_countries()


def filter_dataframe(df: pd.DataFrame, year: int) -> pd.DataFrame:
    return df[df['year'] == year]


def get_palette_and_name(scheme: str):
    palettes = {
        "por_region": {
            "Latin America & Caribbean ": '#1f77b4',
            "Aggregates": '#ff7f0e',
            "South Asia": '#2ca02c',
            "Sub-Saharan Africa ": '#d62728',
            "Europe & Central Asia": '#9467bd',
            "Middle East & North Africa": '#8c564b',
            "East Asia & Pacific": '#e377c2',
            "North America": '#7f7f7f'
        },
        "por_avanzadas": {
            "Unknown": '#bcbd22',
            "Economías avanzadas": '#17becf',
            "Economías no avanzadas": '#e377c2'
        },
        "Latinoamerica": {
            "Latinoamérica": '#1f77b4',
            "No Latinoamérica": '#ff7f0e'
        }
    }
    return palettes[scheme]


def update_figure(year: int, palette: dict) -> go.Figure:
    filtered_df = filter_dataframe(df_diversidad_paises, year)
    fig = px.scatter(
        filtered_df,
        x="export_product_diversity",
        y="import_product_diversity",
        color='is_latinoamerica',
        color_discrete_map=palette,
        marginal_y="violin",
        marginal_x="histogram",
        trendline="ols",
        template="simple_white",
        title=f'Diversidad de exportaciones e importaciones - {year}',
        hover_data=['countries'],
        labels={
            "export_product_diversity": "Diversidad de exportación de productos",
            "import_product_diversity": "Diversidad de importación de productos"
        }
    )
    fig.update_layout(
        font=dict(family="Arial", color="black", size=16),
        title_font=dict(family="Arial", color="black"),
        legend_title_font=dict(color="black"),
        xaxis=dict(range=[0, 1200]),
        yaxis=dict(range=[0, 1500]),
    )
    fig.update_xaxes(title_font_family="Arial")
    return fig


def diversity_over_time_plot(df: pd.DataFrame, diversity_type: str, palette: dict, classification_scheme: str) -> go.Figure:
    fig = go.Figure()

    for region in df[classification_scheme].unique():
        region_data = df[df[classification_scheme] == region]
        if diversity_type in ["Ambos", "Exportación"]:
            fig.add_trace(go.Scatter(
                x=region_data['year'],
                y=region_data['export_product_diversity'],
                mode='lines',
                name=f'{region} - Export',
                line=dict(color=palette.get(region, '#000000')),
                legendgroup=region
            ))
        if diversity_type in ["Ambos", "Importación"]:
            fig.add_trace(go.Scatter(
                x=region_data['year'],
                y=region_data['import_product_diversity'],
                mode='lines',
                name=f'{region} - Import',
                line=dict(color=palette.get(region, '#000000'), dash='dash'),
                legendgroup=region
            ))

    fig.update_layout(
        title="Exportación e importación de la diversidad de productos a través del tiempo",
        xaxis_title="Año",
        yaxis_title="Diversidad de Productos",
        legend_title="Región y tipo de diversidad",
        hovermode="closest",
        legend=dict(groupclick="toggleitem")
    )
    return fig


st.title("Diversidad de Exportaciones e Importaciones por País en cada Año")
year = st.slider("Seleccione un año:", min_value=years.min(), max_value=years.max(), value=years.min())
palette = get_palette_and_name("Latinoamerica")
st.plotly_chart(update_figure(year, palette), use_container_width=True)

st.title("Diversidad a lo largo del tiempo: Latinoamérica y Mundo")
diversity_type = st.selectbox("Elige tipo de diversidad:", ["Ambos", "Exportación", "Importación"], index=0)
classification_scheme = st.selectbox("Elige el tipo de clasificación: ", ["por_region", "por_avanzadas"], index=0)
palette = get_palette_and_name(classification_scheme)

df_classified = {
        "por_region": load_data_diversity_classification_region(),
        "por_avanzadas": load_data_diversity_classification_advanced()
}
st.plotly_chart(diversity_over_time_plot(df_classified[classification_scheme], diversity_type, palette, classification_scheme), use_container_width=True)
