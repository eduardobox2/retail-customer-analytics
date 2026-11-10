# 📊 E-commerce Customer Intelligence & Cross-Selling

Un análisis *End-to-End* de más de 1 millón de transacciones de retail para segmentar clientes mediante modelos RFM y K-Means, acoplado a un motor de recomendación con el algoritmo Apriori.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://URL-DE-TU-APP-AQUI.streamlit.app/)

*(📸 Reemplaza esta línea por una captura de pantalla `![Dashboard](link-a-tu-imagen.png)` o un GIF corto mostrando tu app)*

## 🎯 Problema de Negocio
El e-commerce genera un gran volumen de transacciones diarias, pero carecía de visibilidad sobre quiénes son sus clientes más valiosos (VIP), quiénes están a punto de abandonar la marca, y qué productos se compran frecuentemente juntos. Este proyecto busca transformar datos crudos en estrategias accionables para retención y *cross-selling*.

## 📂 Datos
* **Fuente:** Dataset *Online Retail II* (UCI Machine Learning Repository). [Enlace al dataset](https://archive.ics.uci.edu/ml/datasets/Online+Retail+II).
* **Tamaño y Periodo:** +1.06 Millones de registros, cubriendo ventas del 2009 al 2011 en Reino Unido.
* **Limpieza:** Se filtraron valores nulos en `Customer ID` (compras de invitados), se eliminaron devoluciones (facturas con prefijo 'C') y registros duplicados de sistema, resultando en un dataset analítico de 779,425 transacciones limpias.

## 📈 Hallazgos Clave
* **La Ley de Pareto se cumple:** Un núcleo de **1,482 clientes "Campeones"** sostiene la mayor parte de la rentabilidad del negocio.
* **Volumen de Abandono:** Existen **1,523 clientes en estado "Perdidos / Hibernando"**, lo que indica fallos históricos en las campañas de fidelización post-compra.
* **Fuerza de Asociación (Market Basket):** El algoritmo Apriori descubrió que los productos `SWEETHEART CERAMIC TRINKET BOX` y `STRAWBERRY CERAMIC TRINKET BOX` tienen un **Lift de 13.9**. Es decir, un cliente tiene casi 14 veces más probabilidades de comprar la segunda caja si ya puso la primera en su carrito.

## 💡 Recomendaciones Estratégicas e Impacto
| Segmento | Acción Recomendada | Canal | Objetivo |
| :--- | :--- | :--- | :--- |
| **Campeones** | Programa VIP, acceso anticipado a colecciones exclusivas. | Email / Web | Retención |
| **Leales** | Venta cruzada dinámica usando las reglas de asociación (Apriori). | Checkout Web | Subir Ticket Promedio |
| **En Riesgo** | Descuento agresivo de reactivación urgente o llamada directa. | Email / SMS | Recuperación |
| **Nuevos** | Campaña de bienvenida con incentivo para su segunda compra. | Email | Fidelización |

💰 **Impacto Estimado:** El análisis detectó un bloque de clientes "En Riesgo" que históricamente gastaban mucho pero han dejado de comprar. Si se logra reactivar solo al **10%** de este segmento mediante campañas dirigidas, se estima una recuperación potencial de **~£370,000** en ingresos.

## 🛠️ Metodología
1. **Modelado RFM:** Se calculó Recencia (días desde última compra), Frecuencia (nº facturas) y Monto (gasto histórico) por cliente, dividiéndolos en quintiles.
2. **Machine Learning No Supervisado:** Se validó la segmentación aplicando **K-Means Clustering**. Usando el Método del Codo, se determinó `K=4` como el número óptimo de clusters matemáticos, los cuales coincidieron altamente con las reglas de negocio manuales (tras aplicar estandarización y escala logarítmica).
3. **Análisis de Canasta (Apriori):** Creación de una matriz One-Hot para extraer reglas de asociación con *Lift > 1*.

## 🚀 Cómo ejecutarlo localmente
Para correr este proyecto en tu máquina y reproducir la base SQLite desde cero:

1. Clona el repositorio:
   ```bash
   git clone [https://github.com/TU_USUARIO/TU_REPO.git](https://github.com/TU_USUARIO/TU_REPO.git)
   cd TU_REPO