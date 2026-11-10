from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =====================================================================
# CONFIGURACIÓN GENERAL
# =====================================================================
st.set_page_config(page_title="Retail · Clientes y Ventas", page_icon="📊", layout="wide")

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data" / "processed"
st.markdown(f"<style>{(Path(__file__).parent / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

PALETA = ["#6C5CE7", "#00CEC9", "#FD79A8", "#FDCB6E", "#74B9FF", "#55EFC4", "#E17055", "#A29BFE"]
ORDEN_SEGMENTOS = ["Campeones", "Leales", "Nuevos / Prometedores", "Necesitan atención", "En Riesgo", "Perdidos / Hibernando"]
COLOR_SEGMENTO = {
    "Campeones": "#FDCB6E", "Leales": "#00B894", "Nuevos / Prometedores": "#74B9FF",
    "Necesitan atención": "#A29BFE", "En Riesgo": "#E17055", "Perdidos / Hibernando": "#636E72",
}
COLOR_CLUSTER = {
    "Perdidos": "#636E72", "Inactivos": "#636E72", "Durmientes": "#E17055", "Activos recientes": "#00CEC9", "Ocasionales": "#74B9FF",
    "Regulares": "#00CEC9", "Leales": "#00B894", "VIP": "#FDCB6E",
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================
@st.cache_data
def cargar_datos():
    rfm = pd.read_csv(DATOS / "rfm_clusters.csv", dtype={"Customer ID": str})
    reglas = pd.read_csv(DATOS / "reglas_asociacion.csv")
    ventas = pd.read_csv(DATOS / "ventas_mensuales.csv")
    productos = pd.read_csv(DATOS / "top_productos.csv")
    dia_hora = pd.read_csv(DATOS / "ventas_dia_hora.csv")
    return rfm, reglas, ventas, productos, dia_hora


def estilo(fig, alto=400, titulo=None):
    """Formato visual común para todos los gráficos."""
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=alto, margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
                      font=dict(family="Segoe UI, Arial", size=13), legend_title_text="")
    if titulo:
        fig.update_layout(title=dict(text=f"<b>{titulo}</b>", x=0.01))
    return fig


def tarjeta(etiqueta, valor, detalle="", color="#6C5CE7"):
    return (f'<div class="kpi" style="--accent:{color}"><div class="label">{etiqueta}</div>'
            f'<div class="value">{valor}</div><div class="sub">{detalle}</div></div>')


def libras(x):
    return f"£{x:,.0f}"


def libras_corto(x):
    """Formato compacto para tarjetas: £16.5 M / £250 K."""
    if abs(x) >= 1e6:
        return f"£{x / 1e6:,.2f} M"
    if abs(x) >= 1e4:
        return f"£{x / 1e3:,.0f} K"
    return f"£{x:,.0f}"


def grafico(fig):
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


# =====================================================================
# CARGA DE DATOS
# =====================================================================
try:
    rfm, reglas, ventas, productos, dia_hora = cargar_datos()
except FileNotFoundError as error:
    st.error(f"❌ No se encontró un archivo de datos ({error.filename}). "
             "Ejecuta primero los notebooks 01, 02 y 03, y lanza el dashboard desde la carpeta raíz del proyecto.")
    st.stop()

segmentos_disponibles = [s for s in ORDEN_SEGMENTOS if s in rfm["Segmento_Negocio"].unique()]
orden_clusters = rfm.drop_duplicates("Cluster").sort_values("Cluster")["Cluster_Nombre"].tolist()
color_cluster = {n: COLOR_CLUSTER.get(n, PALETA[i % len(PALETA)]) for i, n in enumerate(orden_clusters)}

# =====================================================================
# ENCABEZADO
# =====================================================================
st.markdown("""
<div class="hero">
  <h1> Retail Analytics · Clientes y Ventas</h1>
  <p>Segmentación RFM + K-Means y canasta de compras (Apriori) · Tienda online del Reino Unido, 2009-2011</p>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# FILTROS LATERALES (afectan a la información de clientes)
# =====================================================================
with st.sidebar:
    st.header("🎛️ Filtros de clientes")
    sel_segmentos = st.multiselect("Segmento de negocio", segmentos_disponibles, default=segmentos_disponibles)
    sel_clusters = st.multiselect("Cluster K-Means", orden_clusters, default=orden_clusters)
    paises = rfm["Pais"].value_counts().index.tolist()
    sel_paises = st.multiselect("País", paises, default=paises)
    rec_min, rec_max = int(rfm["Recency"].min()), int(rfm["Recency"].max())
    rango_rec = st.slider("Días desde la última compra", rec_min, rec_max, (rec_min, rec_max))
    gasto_max = int(np.ceil(rfm["Monetary"].max() / 100) * 100)
    rango_gasto = st.slider("Gasto total (£)", 0, gasto_max, (0, gasto_max), step=100)
    st.caption("Estos filtros aplican a las pestañas de **Resumen** y **Segmentos**.")

f = rfm[rfm["Segmento_Negocio"].isin(sel_segmentos) & rfm["Cluster_Nombre"].isin(sel_clusters) & rfm["Pais"].isin(sel_paises)
        & rfm["Recency"].between(*rango_rec) & rfm["Monetary"].between(*rango_gasto)].copy()

tab_resumen, tab_segmentos, tab_canasta, tab_ventas = st.tabs(
    [" Resumen", "👥 Segmentos y clusters", "🛒 Canasta de compras", "📈 Ventas en el tiempo"])

# =====================================================================
# PESTAÑA 1 · RESUMEN
# =====================================================================
with tab_resumen:
    if f.empty:
        st.warning("No hay clientes con los filtros seleccionados.")
    else:
        riesgo = f["Segmento_Negocio"].isin(["En Riesgo", "Perdidos / Hibernando"]).mean()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(tarjeta("Clientes", f"{len(f):,}", f"{len(f) / len(rfm):.0%} del total", "#6C5CE7"), unsafe_allow_html=True)
        c2.markdown(tarjeta("Ingresos", libras_corto(f["Monetary"].sum()), f"total: {libras(f['Monetary'].sum())}", "#00CEC9"), unsafe_allow_html=True)
        c3.markdown(tarjeta("Gasto por cliente", libras(f["Monetary"].mean()), f"mediana {libras(f['Monetary'].median())}", "#FDCB6E"), unsafe_allow_html=True)
        c4.markdown(tarjeta("Compras por cliente", f"{f['Frequency'].mean():.1f}", "facturas promedio", "#74B9FF"), unsafe_allow_html=True)
        c5.markdown(tarjeta("En riesgo o perdidos", f"{riesgo:.0%}", "oportunidad de reactivación", "#E17055"), unsafe_allow_html=True)

        seg = f.groupby("Segmento_Negocio").agg(Clientes=("Customer ID", "count"), Ingresos=("Monetary", "sum")).reset_index()
        seg["% Clientes"] = seg["Clientes"] / seg["Clientes"].sum() * 100
        seg["% Ingresos"] = seg["Ingresos"] / seg["Ingresos"].sum() * 100
        top_seg = seg.sort_values("% Ingresos", ascending=False).iloc[0]
        st.markdown(f'<div class="insight">💡 <b>{top_seg["Segmento_Negocio"]}</b> es el segmento que más aporta: '
                    f'{top_seg["% Clientes"]:.0f}% de los clientes generan el <b>{top_seg["% Ingresos"]:.0f}%</b> de los ingresos.</div>',
                    unsafe_allow_html=True)

        izq, der = st.columns([2, 3])
        with izq:
            fig = px.pie(seg, names="Segmento_Negocio", values="Clientes", hole=0.55, color="Segmento_Negocio",
                         color_discrete_map=COLOR_SEGMENTO, category_orders={"Segmento_Negocio": ORDEN_SEGMENTOS})
            fig.update_traces(textinfo="percent", textfont_size=13)
            grafico(estilo(fig, 400, "Clientes por segmento"))
        with der:
            largo = seg.melt(id_vars="Segmento_Negocio", value_vars=["% Clientes", "% Ingresos"], var_name="Métrica", value_name="%")
            fig = px.bar(largo, x="Segmento_Negocio", y="%", color="Métrica", barmode="group", text=largo["%"].map("{:.0f}%".format),
                         color_discrete_map={"% Clientes": "#636E72", "% Ingresos": "#6C5CE7"},
                         category_orders={"Segmento_Negocio": ORDEN_SEGMENTOS})
            fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)
            fig.update_layout(xaxis_title="", yaxis_title="% del total")
            grafico(estilo(fig, 400, "¿Quién genera el dinero? % de clientes vs % de ingresos"))

# =====================================================================
# PESTAÑA 2 · SEGMENTOS Y CLUSTERS
# =====================================================================
with tab_segmentos:
    if f.empty:
        st.warning("No hay clientes con los filtros seleccionados.")
    else:
        st.subheader("Mapa de clientes")
        col_a, col_b = st.columns([2, 1])
        colorear = col_a.radio("Colorear por", ["Cluster K-Means", "Segmento de negocio"], horizontal=True)
        vista_3d = col_b.toggle("Vista 3D (arrastra para girar)", value=False)
        columna = "Cluster_Nombre" if colorear == "Cluster K-Means" else "Segmento_Negocio"
        mapa_color = color_cluster if columna == "Cluster_Nombre" else COLOR_SEGMENTO
        orden_cat = orden_clusters if columna == "Cluster_Nombre" else ORDEN_SEGMENTOS

        if vista_3d:
            fig = px.scatter_3d(f, x="Recency", y="Frequency", z="Monetary", color=columna, color_discrete_map=mapa_color,
                                log_x=True, log_y=True, log_z=True, opacity=0.75, hover_data=["Customer ID", "Pais"],
                                category_orders={columna: orden_cat})
            fig.update_traces(marker_size=3)
            grafico(estilo(fig, 620))
        else:
            fig = px.scatter(f, x="Recency", y="Monetary", color=columna, size="Frequency", size_max=22, log_y=True,
                             color_discrete_map=mapa_color, opacity=0.6, hover_data=["Customer ID", "Pais", "Frequency"],
                             category_orders={columna: orden_cat},
                             labels={"Recency": "Días desde la última compra", "Monetary": "Gasto total (£, escala log)"})
            grafico(estilo(fig, 520, "Cada punto es un cliente (tamaño = nº de compras)"))

        st.subheader("Perfil de cada cluster")
        perfil = f.groupby("Cluster_Nombre").agg(Clientes=("Customer ID", "count"), Recencia=("Recency", "mean"),
                                                 Frecuencia=("Frequency", "mean"), Gasto_Medio=("Monetary", "mean"),
                                                 Ingresos=("Monetary", "sum")).reindex(orden_clusters).dropna().reset_index()
        perfil["% Clientes"] = perfil["Clientes"] / perfil["Clientes"].sum() * 100
        perfil["% Ingresos"] = perfil["Ingresos"] / perfil["Ingresos"].sum() * 100

        izq, der = st.columns([3, 2])
        with izq:
            st.dataframe(perfil, hide_index=True, width="stretch", column_config={
                "Cluster_Nombre": "Cluster", "Recencia": st.column_config.NumberColumn("Recencia (días)", format="%.0f"),
                "Frecuencia": st.column_config.NumberColumn("Compras", format="%.1f"),
                "Gasto_Medio": st.column_config.NumberColumn("Gasto medio", format="£%.0f"),
                "Ingresos": st.column_config.NumberColumn("Ingresos", format="£%.0f"),
                "% Clientes": st.column_config.ProgressColumn("% Clientes", format="%.0f%%", min_value=0, max_value=100),
                "% Ingresos": st.column_config.ProgressColumn("% Ingresos", format="%.0f%%", min_value=0, max_value=100)})
        with der:
            medias = np.log1p(perfil[["Recencia", "Frecuencia", "Gasto_Medio"]])
            rango = (medias.max() - medias.min()).replace(0, np.nan)
            norm = ((medias - medias.min()) / rango).fillna(0.5)
            norm["Recencia"] = 1 - norm["Recencia"]
            ejes = ["Compra reciente", "Frecuencia", "Gasto"]
            fig = go.Figure()
            for i, fila in perfil.iterrows():
                v = norm.loc[i, ["Recencia", "Frecuencia", "Gasto_Medio"]].tolist()
                fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=ejes + ejes[:1], fill="toself", name=fila["Cluster_Nombre"],
                                              line_color=color_cluster[fila["Cluster_Nombre"]], opacity=0.6))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False)))
            grafico(estilo(fig, 340))

        st.subheader("¿Coinciden las dos segmentaciones?")
        cruce = pd.crosstab(f["Segmento_Negocio"], f["Cluster_Nombre"])
        cruce = cruce.reindex(index=[s for s in ORDEN_SEGMENTOS if s in cruce.index], columns=[c for c in orden_clusters if c in cruce.columns])
        fig = px.imshow(cruce.div(cruce.sum(axis=1), axis=0) * 100, text_auto=".0f", aspect="auto",
                        color_continuous_scale=["#1A1D29", "#6C5CE7", "#00CEC9"],
                        labels=dict(x="Cluster K-Means", y="Segmento de negocio", color="% fila"))
        grafico(estilo(fig, 380))

        st.subheader("Lista de clientes")
        buscar = st.text_input("🔎 Buscar por ID de cliente", placeholder="Ej: 12347")
        tabla = f[f["Customer ID"].str.contains(buscar.strip(), na=False)] if buscar.strip() else f
        tabla = tabla[["Customer ID", "Pais", "Segmento_Negocio", "Cluster_Nombre", "Recency", "Frequency", "Monetary",
                       "R_Score", "F_Score", "M_Score"]].sort_values("Monetary", ascending=False)
        st.dataframe(tabla, hide_index=True, width="stretch", column_config={
            "Customer ID": "Cliente", "Pais": "País", "Segmento_Negocio": "Segmento", "Cluster_Nombre": "Cluster",
            "Recency": "Recencia", "Frequency": "Compras", "Monetary": st.column_config.NumberColumn("Gasto", format="£%.0f")})
        st.download_button("⬇️ Descargar tabla filtrada (CSV)", tabla.to_csv(index=False).encode("utf-8"),
                           "clientes_filtrados.csv", "text/csv")

# =====================================================================
# PESTAÑA 3 · CANASTA DE COMPRAS
# =====================================================================
with tab_canasta:
    st.subheader("Productos que se compran juntos")
    st.markdown('<div class="insight">💡 <b>Lift</b> indica cuántas veces es más probable comprar B si ya compraron A. '
                '<b>Confianza</b> es la probabilidad de que compren B cuando compran A. '
                'Úsalo para armar combos y recomendaciones.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    lift_min = c1.slider("Lift mínimo", float(np.floor(reglas["lift"].min())), float(np.ceil(reglas["lift"].max())),
                         float(np.floor(reglas["lift"].min())), 0.5)
    conf_min = c2.slider("Confianza mínima", 0, 100, 30, 5, format="%d%%") / 100
    sop_min = c3.slider("Soporte mínimo", 0.0, float(reglas["support"].max() * 100), 0.0, 0.1, format="%.1f%%") / 100
    ambas = c4.toggle("Ambas direcciones", value=False)

    r = reglas[(reglas["lift"] >= lift_min) & (reglas["confidence"] >= conf_min) & (reglas["support"] >= sop_min)].copy()
    if not ambas:
        r = r[r["Es_Direccion_Principal"]]
    r["Regla"] = r["antecedents"] + "  →  " + r["consequents"]

    if r.empty:
        st.warning("Ninguna regla cumple esos filtros. Prueba a bajarlos.")
    else:
        k1, k2, k3 = st.columns(3)
        k1.markdown(tarjeta("Reglas encontradas", f"{len(r)}", "con los filtros actuales", "#6C5CE7"), unsafe_allow_html=True)
        k2.markdown(tarjeta("Lift máximo", f"{r['lift'].max():.1f}", "la asociación más fuerte", "#E17055"), unsafe_allow_html=True)
        k3.markdown(tarjeta("Confianza media", f"{r['confidence'].mean():.0%}", "probabilidad de compra conjunta", "#00B894"), unsafe_allow_html=True)

        izq, der = st.columns(2)
        with izq:
            fig = px.scatter(r, x="support", y="confidence", size="lift", color="lift", hover_name="Regla", size_max=30,
                             color_continuous_scale=["#74B9FF", "#6C5CE7", "#E17055"],
                             labels=dict(support="Soporte", confidence="Confianza", lift="Lift"))
            fig.update_layout(xaxis_tickformat=".1%", yaxis_tickformat=".0%")
            grafico(estilo(fig, 460, "Mapa de reglas (cada burbuja es una regla)"))
        with der:
            top = r.sort_values("lift", ascending=False).head(12).reset_index(drop=True)
            corto = lambda s: s if len(s) <= 24 else s[:23] + "…"
            top = top.assign(Etiqueta=(top.index + 1).astype(str) + ". " + top["antecedents"].map(corto) + " → " + top["consequents"].map(corto))
            top = top.iloc[::-1]
            fig = px.bar(top, x="lift", y="Etiqueta", orientation="h", color="confidence", text=top["lift"].map("{:.1f}".format),
                         hover_name="Regla", hover_data={"Etiqueta": False}, color_continuous_scale=["#A29BFE", "#00B894"],
                         labels=dict(lift="Lift", confidence="Confianza"))
            fig.update_layout(yaxis_title="", yaxis_tickfont_size=10, coloraxis_colorbar_tickformat=".0%")
            fig.update_yaxes(automargin=True)
            grafico(estilo(fig, 460, "Top asociaciones por lift"))

        tabla = r.sort_values("lift", ascending=False)[["antecedents", "consequents", "support", "confidence", "lift"]]
        st.dataframe(tabla, hide_index=True, width="stretch", column_config={
            "antecedents": "Si compran esto…", "consequents": "…también compran esto",
            "support": st.column_config.NumberColumn("Soporte", format="percent"),
            "confidence": st.column_config.ProgressColumn("Confianza", format="percent", min_value=0, max_value=1),
            "lift": st.column_config.NumberColumn("Lift", format="%.1f")})

    st.subheader(" Recomendador de productos")
    todos = sorted({p for a in reglas["antecedents"] for p in a.split(" + ")})
    elegido = st.selectbox("Elige un producto y mira qué recomendar al cliente:", todos)
    rec = reglas[reglas["antecedents"].map(lambda a: elegido in a.split(" + "))].sort_values("confidence", ascending=False)
    if rec.empty:
        st.info("Este producto no tiene recomendaciones.")
    else:
        for _, fila in rec.head(5).iterrows():
            st.markdown(f'<div class="insight">🛍️ Recomendar <b>{fila["consequents"]}</b> — '
                        f'{fila["confidence"]:.0%} de probabilidad · lift {fila["lift"]:.1f}</div>', unsafe_allow_html=True)

# =====================================================================
# PESTAÑA 4 · VENTAS EN EL TIEMPO
# =====================================================================
with tab_ventas:
    st.caption("Esta pestaña usa todas las ventas y tiene su propio filtro de país (no depende de la barra lateral).")
    paises_v = ventas.groupby("Pais")["Ingresos"].sum().sort_values(ascending=False).index.tolist()
    sel_v = st.multiselect("País", paises_v, default=paises_v, key="paises_ventas")
    v = ventas[ventas["Pais"].isin(sel_v)]

    if v.empty:
        st.warning("Selecciona al menos un país.")
    else:
        mensual = v.groupby("Mes").agg(Ingresos=("Ingresos", "sum"), Facturas=("Facturas", "sum")).reset_index()
        mensual["Fecha"] = pd.to_datetime(mensual["Mes"])
        c1, c2, c3 = st.columns(3)
        c1.markdown(tarjeta("Ingresos", libras_corto(v["Ingresos"].sum()), f"{mensual['Fecha'].min():%b %Y} → {mensual['Fecha'].max():%b %Y}", "#6C5CE7"), unsafe_allow_html=True)
        c2.markdown(tarjeta("Facturas", f"{v['Facturas'].sum():,}", "pedidos realizados", "#00CEC9"), unsafe_allow_html=True)
        c3.markdown(tarjeta("Ticket medio", libras(v["Ingresos"].sum() / v["Facturas"].sum()), "ingreso por factura", "#FDCB6E"), unsafe_allow_html=True)

        fig = px.area(mensual, x="Fecha", y="Ingresos", markers=True)
        fig.update_traces(line_color="#6C5CE7", fillcolor="rgba(108,92,231,0.25)")
        fig.update_layout(xaxis_title="", yaxis_title="Ingresos (£)")
        grafico(estilo(fig, 380, "Ingresos mensuales"))

        izq, der = st.columns(2)
        with izq:
            anual = mensual.assign(Año=mensual["Fecha"].dt.year.astype(str), NumMes=mensual["Fecha"].dt.month)
            fig = px.line(anual, x="NumMes", y="Ingresos", color="Año", markers=True,
                          color_discrete_sequence=["#636E72", "#00CEC9", "#FDCB6E"])
            fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MESES, title="")
            grafico(estilo(fig, 400, "Comparación por año (2009 y 2011 están incompletos)"))
        with der:
            por_pais = ventas.groupby("Pais")["Ingresos"].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(por_pais.sort_values("Ingresos"), x="Ingresos", y="Pais", orientation="h", color="Ingresos",
                         color_continuous_scale=["#A29BFE", "#6C5CE7"])
            fig.update_layout(coloraxis_showscale=False, yaxis_title="")
            grafico(estilo(fig, 400, "Top 10 países por ingresos"))

        izq, der = st.columns(2)
        with izq:
            n = st.slider("Cantidad de productos a mostrar", 5, 30, 12)
            top = productos.head(n).sort_values("Ingresos")
            fig = px.bar(top, x="Ingresos", y="Producto", orientation="h", color="Unidades",
                         color_continuous_scale=["#74B9FF", "#6C5CE7"])
            fig.update_layout(yaxis_title="", yaxis_tickfont_size=10)
            fig.update_yaxes(automargin=True)
            grafico(estilo(fig, 480, "Productos más rentables"))
        with der:
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            pivote = dia_hora.pivot(index="Dia", columns="Hora", values="Ingreso").reindex(dias).fillna(0)
            fig = px.imshow(pivote, aspect="auto", color_continuous_scale=["#1A1D29", "#6C5CE7", "#00CEC9"],
                            labels=dict(x="Hora del día", y="", color="Ingresos (£)"))
            grafico(estilo(fig, 480, "¿Cuándo compran? Día y hora"))

st.markdown("---")
st.caption("Proyecto de segmentación de clientes · Datos: Online Retail II (UCI) · Moneda: libras esterlinas (£)")