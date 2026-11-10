import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Retail Dashboard", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

# Inyección de CSS Extremo para igualar la imagen de referencia
st.markdown("""
<style>
    /* Fondo principal gris/menta claro */
    .stApp {
        background-color: #e6f0ee;
    }
    
    /* Ocultar elementos nativos de Streamlit para limpiar la interfaz */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilizar la barra lateral (Sidebar oscura) */
    [data-testid="stSidebar"] {
        background-color: #272733 !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Espaciado general */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)

# Variable global para mantener el orden en los gráficos y tablas
orden_segmentos = ['Campeones', 'Leales', 'Nuevos / Prometedores', 'Regulares', 'En Riesgo', 'Perdidos / Hibernando']

# Paleta basada en la imagen: Oscuro, Salmón, Menta/Verde
C_DARK = '#272733'
C_SALMON = '#ff8a71'
C_GREEN = '#98e58f'

# ==========================================
# 2. CARGA Y PREPARACIÓN DE DATOS
# ==========================================
@st.cache_data
def load_data():
    rfm = pd.read_csv("data/processed/rfm_clusters.csv")
    rules = pd.read_csv("data/processed/reglas_asociacion.csv")
    
    nombres_clusters = {
        0: 'Perdidos (C0)', 1: 'Ocasionales (C1)', 2: 'VIPs (C2)', 3: 'En Riesgo (C3)'
    }
    rfm['Nombre_Cluster'] = rfm['Cluster'].map(nombres_clusters)
    rfm['Segmento_Negocio'] = pd.Categorical(rfm['Segmento_Negocio'], categories=orden_segmentos, ordered=True)
    return rfm, rules

try:
    rfm, rules = load_data()
except FileNotFoundError:
    st.error("❌ Archivos no encontrados.")
    st.stop()

# ==========================================
# 3. BARRA LATERAL (Imitando menú izquierdo)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; letter-spacing: 2px;'>L O G O T Y P E</h2><br>", unsafe_allow_html=True)
    st.markdown("### ⚙️ FILTROS")
    
    segmentos_seleccionados = st.multiselect(
        "Segmentos:", options=rfm['Segmento_Negocio'].cat.categories, default=rfm['Segmento_Negocio'].cat.categories
    )
    
    rfm_filt = rfm[rfm['Segmento_Negocio'].isin(segmentos_seleccionados)]
    
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; color: #888;'>Desarrollado en Python</p>", unsafe_allow_html=True)

# Cálculos KPIs
ingresos_totales = rfm_filt['Monetary'].sum()
clientes_activos = len(rfm_filt)
ticket_promedio = ingresos_totales / rfm_filt['Frequency'].sum() if rfm_filt['Frequency'].sum() > 0 else 0
campeones = len(rfm_filt[rfm_filt['Segmento_Negocio'] == 'Campeones'])

# ==========================================
# 4. FUNCIÓN PARA TARJETAS ESTILO UI (Header negro, Cuerpo blanco)
# ==========================================
def draw_kpi_card(title, value, sub_text, sub_color):
    html = f"""
    <div style="background: white; border-radius: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; overflow: hidden; font-family: sans-serif;">
        <div style="background: #272733; color: white; padding: 8px 15px; font-size: 0.85rem; font-weight: 600; letter-spacing: 1px;">
            {title.upper()}
        </div>
        <div style="padding: 15px;">
            <div style="font-size: 2rem; font-weight: 700; color: #272733; margin-bottom: 5px;">{value}</div>
            <div style="font-size: 0.75rem; font-weight: 600; color: {sub_color};">{sub_text}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 5. ESTRUCTURA DEL DASHBOARD (HEADER Y KPIS)
# ==========================================
st.markdown(f"<h3 style='color: {C_DARK};'>HOME <span style='font-size: 1rem; font-weight: normal;'> 🏠 DASHBOARD</span></h3>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    draw_kpi_card("Clientes Activos", f"{clientes_activos:,}", "+5% SINCE LAST MONTH", C_GREEN)
with c2:
    draw_kpi_card("Campeones (VIP)", f"{campeones:,}", "+4.54% SINCE LAST MONTH", C_SALMON)
with c3:
    draw_kpi_card("Ticket Promedio", f"£{ticket_promedio:,.2f}", "+2.54% SINCE LAST MONTH", C_GREEN)
with c4:
    draw_kpi_card("Ingresos (Sales)", f"£{ingresos_totales:,.0f}", "+6.54% SINCE LAST MONTH", C_GREEN)

# ==========================================
# 6. GRÁFICOS (Imitando fondo verde y diseño de líneas)
# ==========================================
# Fila central: Líneas
st.markdown(f"""
    <div style="background: white; padding: 15px; border-radius: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;">
        <h5 style="color: {C_DARK}; font-size: 0.9rem; margin-top: 0;">PERCENTAGE (Gasto Promedio por Segmento)</h5>
    </div>
""", unsafe_allow_html=True)

# Gráfico de líneas
df_line = rfm_filt.groupby('Segmento_Negocio', observed=True)['Monetary'].mean().reset_index()
fig_line = px.line(df_line, x='Segmento_Negocio', y='Monetary', markers=True)
fig_line.update_traces(line_color=C_DARK, marker=dict(size=10, color=C_SALMON, line=dict(width=2, color='white')))
fig_line.update_layout(
    height=250, margin=dict(l=20, r=20, t=10, b=20),
    plot_bgcolor='white', paper_bgcolor='white',
    xaxis=dict(showgrid=False, title=""), yaxis=dict(showgrid=True, gridcolor='#f0f0f0', title="")
)
st.plotly_chart(fig_line, use_container_width=True)

# Fila inferior: Gráfico de Barras con fondo verde (Imitando "TOTAL ORDERS")
st.markdown(f"""
    <div style="background: {C_DARK}; color: white; padding: 8px 15px; font-size: 0.85rem; font-weight: 600; border-radius: 6px 6px 0 0;">
        TOTAL ORDERS (Distribución de Clientes)
    </div>
""", unsafe_allow_html=True)

df_bar = rfm_filt['Segmento_Negocio'].value_counts().reset_index()
df_bar.columns = ['Segmento', 'Cantidad']
fig_bar = px.bar(df_bar, x='Segmento', y='Cantidad')
fig_bar.update_traces(marker_color=C_DARK, width=0.3)
fig_bar.update_layout(
    height=300, margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor=C_GREEN, paper_bgcolor=C_GREEN,  # Fondo verde de la imagen
    xaxis=dict(showgrid=False, title="", tickfont=dict(color='white')), 
    yaxis=dict(showgrid=False, title="", tickfont=dict(color='white'))
)
st.plotly_chart(fig_bar, use_container_width=True)