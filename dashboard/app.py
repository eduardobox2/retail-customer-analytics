import re
import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================================
# CONFIGURACIÓN
# ======================================================
st.set_page_config(page_title="Clientes y ventas cruzadas | Retail", page_icon="🛍️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #f6f7f9; }
header, footer, #MainMenu { visibility: hidden; }
.block-container { padding-top: 1.5rem; max-width: 1250px; }
h1, h2, h3 { color: #1b2430; letter-spacing: -0.01em; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e3e6ea; }
[data-testid="stMetric"] { background: #ffffff; border: 1px solid #e3e6ea; border-radius: 8px; padding: 14px 16px; }
[data-testid="stMetricValue"] { color: #1b2430; font-weight: 600; }
.insight { background: #ffffff; border-left: 4px solid #1f6f8b; padding: 12px 16px; border-radius: 4px; color: #1b2430; margin: 8px 0 16px 0; }
</style>
""", unsafe_allow_html=True)

# El mismo color para el mismo segmento en todos los gráficos
ORDEN = ['Campeones', 'Leales', 'Nuevos / Prometedores', 'Regulares', 'En Riesgo', 'Perdidos / Hibernando']
COLORES = {
    'Campeones': '#1b7f5c', 'Leales': '#6fb98f', 'Nuevos / Prometedores': '#3b82c4',
    'Regulares': '#e0b43c', 'En Riesgo': '#e07b39', 'Perdidos / Hibernando': '#c0392b',
}
ACCIONES = pd.DataFrame([
    ['Campeones', 'Programa VIP y acceso anticipado a novedades', 'Retener y subir recompra'],
    ['Leales', 'Venta cruzada con los combos de la pestaña Canasta', 'Aumentar ticket'],
    ['Nuevos / Prometedores', 'Bienvenida y incentivo para la segunda compra', 'Convertir en leales'],
    ['Regulares', 'Promociones por temporada y recordatorios', 'Aumentar frecuencia'],
    ['En Riesgo', 'Descuento de reactivación, priorizando a los de mayor gasto', 'Recuperar antes de perderlos'],
    ['Perdidos / Hibernando', 'Campaña de bajo costo; si no responden, dejar de invertir', 'Evitar gasto inútil'],
], columns=['Segmento', 'Acción recomendada', 'Objetivo'])


def libras(x):
    return f"£{x:,.0f}"


# ======================================================
# DATOS
# ======================================================
@st.cache_data
def cargar():
    rfm = pd.read_csv("data/processed/rfm_clusters.csv")
    reglas = pd.read_csv("data/processed/reglas_asociacion.csv")

    rfm['Segmento_Negocio'] = pd.Categorical(rfm['Segmento_Negocio'], categories=ORDEN, ordered=True)

    # Nombra los clusters según su perfil real (no a ojo)
    perfil = rfm.groupby('Cluster')[['Recency', 'Frequency', 'Monetary']].mean()
    nombres = {c: f"Cluster {c}" for c in perfil.index}
    if len(perfil) == 4:
        vip = perfil['Monetary'].idxmax()
        resto = perfil.drop(vip)
        perdidos = resto['Recency'].idxmax()
        resto = resto.drop(perdidos)
        activos = resto['Recency'].idxmin()
        riesgo = resto.index.difference([activos])[0]
        nombres.update({vip: 'VIP', perdidos: 'Perdidos', activos: 'Activos', riesgo: 'Ocasionales'})
    rfm['Grupo_KMeans'] = rfm['Cluster'].map(nombres)

    # Limpia los conjuntos de productos si vienen como "frozenset({'A'})"
    for col in ['antecedents', 'consequents']:
        if col in reglas.columns:
            reglas[col] = reglas[col].astype(str).apply(
                lambda s: ", ".join(re.findall(r"'([^']*)'", s)) or s)
    return rfm, reglas


try:
    rfm, reglas = cargar()
except FileNotFoundError:
    st.error("No encuentro los archivos en data/processed/. Ejecuta primero los notebooks o scripts del proyecto.")
    st.stop()

# ======================================================
# FILTROS
# ======================================================
with st.sidebar:
    st.header("Filtros")
    segs = st.multiselect("Segmentos", ORDEN, default=ORDEN)
    rec_max = int(rfm['Recency'].max())
    rec = st.slider("Días desde la última compra", 0, rec_max, (0, rec_max))
    gasto_max = int(rfm['Monetary'].quantile(0.99))
    gasto = st.slider("Gasto total del cliente (£)", 0, gasto_max, (0, gasto_max),
                      help="Se corta en el percentil 99 para ignorar casos extremos.")
    st.caption("Los filtros se aplican a las pestañas de Resumen, Segmentos y Grupos K-Means.")

df = rfm[
    rfm['Segmento_Negocio'].isin(segs)
    & rfm['Recency'].between(*rec)
    & ((rfm['Monetary'] <= gasto[1]) | (gasto[1] == gasto_max))
    & (rfm['Monetary'] >= gasto[0])
]
if df.empty:
    st.warning("Con estos filtros no queda ningún cliente. Amplía los rangos.")
    st.stop()

# ======================================================
# ENCABEZADO
# ======================================================
st.title("Quiénes son mis mejores clientes y qué venderles")
st.caption("Tienda online del Reino Unido, 2009 a 2011. Segmentación RFM, K-Means y análisis de canasta.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Resumen", "Segmentos", "Grupos K-Means", "Canasta de compras", "Qué hacer"])

# ======================================================
# 1. RESUMEN
# ======================================================
with tab1:
    ingresos = df['Monetary'].sum()
    pedidos = df['Frequency'].sum()
    top20 = df.nlargest(max(1, int(len(df) * 0.2)), 'Monetary')['Monetary'].sum()
    riesgo = df['Segmento_Negocio'].isin(['En Riesgo', 'Perdidos / Hibernando']).mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes", f"{len(df):,}")
    c2.metric("Ingresos", libras(ingresos))
    c3.metric("Ticket promedio por pedido", f"£{ingresos / pedidos:,.2f}")
    c4.metric("Clientes en riesgo o perdidos", f"{riesgo:.0%}")

    st.markdown(
        f"<div class='insight'>El 20% de clientes que más gasta genera el "
        f"<b>{top20 / ingresos:.0%}</b> de los ingresos. Cuidar a ese grupo es la prioridad.</div>",
        unsafe_allow_html=True)

    res = df.groupby('Segmento_Negocio', observed=True).agg(
        Clientes=('Monetary', 'size'), Ingresos=('Monetary', 'sum')).reset_index()
    res['% de clientes'] = res['Clientes'] / res['Clientes'].sum() * 100
    res['% de ingresos'] = res['Ingresos'] / res['Ingresos'].sum() * 100
    largo = res.melt(id_vars='Segmento_Negocio', value_vars=['% de clientes', '% de ingresos'],
                     var_name='Medida', value_name='Porcentaje')
    fig = px.bar(largo, y='Segmento_Negocio', x='Porcentaje', color='Medida', barmode='group',
                 orientation='h', category_orders={'Segmento_Negocio': ORDEN[::-1]},
                 color_discrete_map={'% de clientes': '#b8c2cc', '% de ingresos': '#1f6f8b'},
                 title="Cuántos clientes hay en cada segmento frente a cuánto ingreso aportan")
    fig.update_layout(height=420, plot_bgcolor='white', paper_bgcolor='#f6f7f9',
                      yaxis_title="", xaxis_title="Porcentaje del total", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 2. SEGMENTOS
# ======================================================
with tab2:
    st.subheader("Perfil de cada segmento")
    perfil = df.groupby('Segmento_Negocio', observed=True).agg(
        Clientes=('Monetary', 'size'),
        Dias_desde_ultima_compra=('Recency', 'mean'),
        Compras=('Frequency', 'mean'),
        Gasto_medio=('Monetary', 'mean'),
        Ingresos=('Monetary', 'sum')).round(1).reset_index()
    perfil['% de ingresos'] = (perfil['Ingresos'] / perfil['Ingresos'].sum() * 100).round(1)
    st.dataframe(perfil.rename(columns={
        'Segmento_Negocio': 'Segmento', 'Dias_desde_ultima_compra': 'Días desde última compra',
        'Compras': 'Compras (promedio)', 'Gasto_medio': 'Gasto medio (£)', 'Ingresos': 'Ingresos (£)'}),
        use_container_width=True, hide_index=True)

    fig = px.box(df, x='Segmento_Negocio', y='Monetary', color='Segmento_Negocio', log_y=True,
                 color_discrete_map=COLORES, category_orders={'Segmento_Negocio': ORDEN},
                 title="Gasto por cliente en cada segmento (escala logarítmica)")
    fig.update_layout(height=420, showlegend=False, plot_bgcolor='white', paper_bgcolor='#f6f7f9',
                      xaxis_title="", yaxis_title="Gasto total (£)")
    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# 3. GRUPOS K-MEANS
# ======================================================
with tab3:
    st.subheader("Los grupos que encontró el algoritmo")
    muestra = df.sample(min(len(df), 3000), random_state=1)
    fig = px.scatter(muestra, x='Recency', y='Monetary', color='Grupo_KMeans', log_y=True, opacity=0.5,
                     hover_data=['Frequency', 'Segmento_Negocio'],
                     title="Cada punto es un cliente (muestra de hasta 3,000)")
    fig.update_layout(height=450, plot_bgcolor='white', paper_bgcolor='#f6f7f9',
                      xaxis_title="Días desde la última compra", yaxis_title="Gasto total (£, escala log)",
                      legend_title="Grupo")
    st.plotly_chart(fig, use_container_width=True)

    cruce = pd.crosstab(df['Segmento_Negocio'], df['Grupo_KMeans'], normalize='index').mul(100).round(0)
    fig2 = px.imshow(cruce, text_auto=True, aspect='auto', color_continuous_scale='Blues',
                     title="Qué porcentaje de cada segmento cae en cada grupo K-Means")
    fig2.update_layout(height=400, paper_bgcolor='#f6f7f9', xaxis_title="Grupo K-Means",
                       yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Si cada fila se concentra en un solo grupo, las reglas de negocio y el algoritmo coinciden.")

# ======================================================
# 4. CANASTA
# ======================================================
with tab4:
    st.subheader("Qué productos se compran juntos")
    cols = {c.lower(): c for c in reglas.columns}
    necesarias = ['antecedents', 'consequents', 'support', 'confidence', 'lift']
    if not all(n in cols for n in necesarias):
        st.warning("El archivo de reglas debe tener las columnas: " + ", ".join(necesarias))
    else:
        r = reglas.rename(columns={cols[n]: n for n in necesarias})
        a, b = st.columns(2)
        lift_min = a.slider("Lift mínimo", 1.0, float(max(r['lift'].max(), 2.0)), 3.0, 0.5,
                            help="Cuántas veces más probable es la compra conjunta que por azar.")
        conf_min = b.slider("Confianza mínima", 0.0, 1.0, 0.5, 0.05,
                            help="De los que compran A, qué proporción también compra B.")
        f = r[(r['lift'] >= lift_min) & (r['confidence'] >= conf_min)].sort_values('lift', ascending=False)
        st.write(f"**{len(f):,}** reglas cumplen los criterios.")
        if len(f):
            fig = px.scatter(f.head(500), x='support', y='confidence', color='lift', size='lift',
                             hover_data=['antecedents', 'consequents'], color_continuous_scale='Teal',
                             title="Soporte y confianza de cada regla (el color indica el lift)")
            fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='#f6f7f9',
                              xaxis_title="Soporte (frecuencia de la pareja)", yaxis_title="Confianza")
            st.plotly_chart(fig, use_container_width=True)

            f = f.assign(Regla=f['antecedents'] + "  →  " + f['consequents'])
            st.dataframe(
                f[['Regla', 'support', 'confidence', 'lift']].head(50).rename(columns={
                    'support': 'Soporte', 'confidence': 'Confianza', 'lift': 'Lift'}).round(3),
                use_container_width=True, hide_index=True)

            prod = st.selectbox("Busca un producto y mira con qué se vende",
                                sorted(set(f['antecedents'])))
            st.dataframe(f[f['antecedents'] == prod][['consequents', 'confidence', 'lift']].head(5)
                         .rename(columns={'consequents': 'Se compra también', 'confidence': 'Confianza',
                                          'lift': 'Lift'}).round(3), hide_index=True)

# ======================================================
# 5. ACCIONES
# ======================================================
with tab5:
    st.subheader("Qué hacer con cada segmento")
    tabla = ACCIONES.merge(
        df.groupby('Segmento_Negocio', observed=True)['Monetary'].agg(['size', 'sum']).reset_index()
          .rename(columns={'Segmento_Negocio': 'Segmento', 'size': 'Clientes', 'sum': 'Ingresos (£)'}),
        on='Segmento', how='left').fillna(0)
    tabla['Ingresos (£)'] = tabla['Ingresos (£)'].round(0)
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    st.markdown("**Estimación de impacto**")
    tasa = st.slider("Porcentaje de clientes en riesgo que logramos recuperar", 1, 50, 10)
    er = df[df['Segmento_Negocio'] == 'En Riesgo']
    if len(er):
        extra = er['Monetary'].mean() * len(er) * tasa / 100
        st.markdown(
            f"<div class='insight'>Si recuperamos el {tasa}% de los {len(er):,} clientes en riesgo, "
            f"con su gasto medio histórico de {libras(er['Monetary'].mean())}, "
            f"los ingresos adicionales serían de unos <b>{libras(extra)}</b>. "
            f"Es una estimación simple: no descuenta el costo de la campaña.</div>",
            unsafe_allow_html=True)
    else:
        st.info("No hay clientes 'En Riesgo' con los filtros actuales.")