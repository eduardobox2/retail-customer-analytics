# 📊 E-commerce Customer Intelligence & Cross-Selling

Este proyecto es una solución analítica *End-to-End* diseñada para un e-commerce del Reino Unido. Procesa más de 1 millón de registros transaccionales para descubrir el valor oculto de los clientes y generar recomendaciones automáticas de productos.

## 🎯 Objetivos del Negocio
* **Segmentación:** Identificar a los clientes más valiosos (VIP) y aquellos con alto riesgo de abandono.
* **Validación Analítica:** Comparar reglas de negocio tradicionales con clustering no supervisado (IA).
* **Motor de Recomendación:** Descubrir patrones de compra conjunta para armar combos y aumentar el ticket promedio.

## 🛠️ Stack Tecnológico
* **Lenguaje:** Python 3
* **Base de Datos:** SQLite (Migración, limpieza y consultas CTE con Pandas/SQLAlchemy)
* **Machine Learning:** Scikit-Learn (K-Means, Método del Codo, Escalado Logarítmico)
* **Market Basket Analysis:** MLxtend (Algoritmo Apriori)
* **Visualización Web:** Streamlit & Plotly (UI/UX personalizada con inyección CSS)

## 🧠 Metodología
1. **ETL & EDA:** Limpieza de datos (nulos, devoluciones) y estructuración en base de datos relacional.
2. **Modelo RFM:** Cálculo de Recencia, Frecuencia y Monto (Monetary) dividido en quintiles.
3. **Clustering (K-Means):** Validación matemática de los segmentos con K=4.
4. **Reglas de Asociación:** Cálculo de *Support, Confidence y Lift* para recomendar productos con alta afinidad.

## 🚀 Cómo ejecutar el Dashboard localmente
1. Clona este repositorio.
2. Crea un entorno virtual e instala las dependencias: `pip install pandas sqlite3 scikit-learn mlxtend streamlit plotly`
3. Ejecuta la aplicación web:
   ```bash
   streamlit run dashboard/app.py