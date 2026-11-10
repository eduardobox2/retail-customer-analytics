import pandas as pd
from sqlalchemy import create_engine
import time
import os

print("Iniciando carga de datos...")
start_time = time.time()

# 1. Definir la ruta del archivo (ajustada para ejecutarse desde la raíz del proyecto)
file_path = 'data/raw/online_retail_II.xlsx'

# Leer ambas hojas del Excel
print("Leyendo hoja 2009-2010...")
df1 = pd.read_excel(file_path, sheet_name='Year 2009-2010')

print("Leyendo hoja 2010-2011...")
df2 = pd.read_excel(file_path, sheet_name='Year 2010-2011')

# Unir ambos DataFrames en uno solo
df_final = pd.concat([df1, df2], ignore_index=True)
print(f"Total de registros a procesar: {len(df_final)}")

# 2. Conectar a la base de datos (SQLite local)
db_path = 'sqlite:///data/retail.db'
engine = create_engine(db_path)

# 3. Subir los datos a la tabla 'retail_sales'
print("Subiendo datos a la base relacional (esto puede tardar un par de minutos)...")
df_final.to_sql('retail_sales', con=engine, if_exists='replace', index=False)

end_time = time.time()
print(f"¡Carga completada en {round(end_time - start_time, 2)} segundos!")
print("Tu base de datos está lista en: data/retail.db")