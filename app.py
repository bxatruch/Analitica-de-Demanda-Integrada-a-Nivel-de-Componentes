import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Comparador de Demanda & BOM", layout="wide")

st.title("📦 Comparador de Demanda con Explosión de BOM")
st.write("Compara releases de demanda de producto terminado, cruza con la BOM y obtén los componentes con mayor impacto.")

# Sidebar para umbrales de alerta
st.sidebar.header("⚙️ Configuración de Alertas")
umbral_subida = st.sidebar.slider("Umbral de incremento agresivo (%)", 10, 100, 30, step=5)
umbral_bajada = st.sidebar.slider("Umbral de disminución agresiva (%)", -100, -10, -30, step=5)

# Sección 1: Carga de Archivos de Demanda y BOM
st.subheader("📂 Carga de Datos")
col1, col2, col3 = st.columns(3)
with col1:
    file_anterior = st.file_uploader("Release Anterior (CSV)", type=["csv"])
with col2:
    file_actual = st.file_uploader("Release Actual (CSV)", type=["csv"])
with col3:
    file_bom = st.file_uploader("Cargar BOM / Lista de Materiales (CSV)", type=["csv"])

# Datos simulados por defecto si no se cargan archivos
if not file_anterior or not file_actual or not file_bom:
    st.info("💡 Cargando datos de ejemplo para demostración. Sube tus propios archivos CSV para analizar datos reales.")
    
    # Simulación Demanda Anterior
    data_ant = pd.DataFrame({
        'Producto': ['PROD-A', 'PROD-B'],
        'Demanda_Anterior': [100, 200]
    })
    # Simulación Demanda Actual
    data_act = pd.DataFrame({
        'Producto': ['PROD-A', 'PROD-B'],
        'Demanda_Actual': [150, 50] # A sube +50%, B baja -75%
    })
    # Simulación BOM (Estructura: Producto terminado -> Componente -> Cantidad requerida por producto)
    data_bom = pd.DataFrame({
        'Producto': ['PROD-A', 'PROD-A', 'PROD-B', 'PROD-B'],
        'Componente': ['COMP-Alpha', 'COMP-Beta', 'COMP-Beta', 'COMP-Gamma'],
        'Cantidad_Por_Producto': [2.0, 1.5, 3.0, 1.0]
    })
else:
    try:
        data_ant = pd.read_csv(file_anterior)
        data_act = pd.read_csv(file_actual)
        data_bom = pd.read_csv(file_bom)
    except Exception as e:
        st.error(f"Error al leer los archivos cargados: {e}")
        st.stop()

try:
    # 2. Procesamiento de Comparación a nivel de Producto Terminado
    # Asegurar nombres consistentes
    data_ant.columns = [col.strip() for col in data_ant.columns]
    data_act.columns = [col.strip() for col in data_act.columns]
    data_bom.columns = [col.strip() for col in data_bom.columns]

    # Renombrar primera columna a 'Producto' si es necesario para facilitar el cruce
    prod_col_ant = data_ant.columns[0]
    prod_col_act = data_act.columns[0]
    bom_prod_col = data_bom.columns[0]
    
    df_ant = data_ant.rename(columns={prod_col_ant: 'Producto'})
    df_act = data_act.rename(columns={prod_col_act: 'Producto'})
    df_bom = data_bom.rename(columns={bom_prod_col: 'Producto'})
    
    # Aseguramos nombres de columnas de demanda numéricas
    demand_col_ant = df_ant.columns[1]
    demand_col_act = df_act.columns[1]
    df_ant = df_ant.rename(columns={demand_col_ant: 'Demanda_Anterior'})
    df_act = df_act.rename(columns={demand_col_act: 'Demanda_Actual'})

    df_prod_compare = pd.merge(df_ant, df_act, on="Producto", how="outer").fillna(0)

    # 3. Explosión de Demanda a través de la BOM para calcular requerimientos de Componentes
    # Cruzamos la tabla de comparación de productos con la BOM
    df_exploded = pd.merge(df_bom, df_prod_compare, on="Producto", how="inner")

    # Calcular demanda requerida para cada componente
    df_exploded['Requerimiento_Anterior'] = df_exploded['Demanda_Anterior'] * df_exploded['Cantidad_Por_Producto']
    df_exploded['Requerimiento_Actual'] = df_exploded['Demanda_Actual'] * df_exploded['Cantidad_Por_Producto']

    # Agrupar por Componente para consolidar si un componente se usa en múltiples productos
    df_comp_summary = df_exploded.groupby('Componente').agg({
        'Requerimiento_Anterior': 'sum',
        'Requerimiento_Actual': 'sum'
    }).reset_index()

    # 4. Calcular Variaciones en Componentes
    df_comp_summary['Variacion_Absoluta'] = df_comp_summary['Requerimiento_Actual'] - df_comp_summary['Requerimiento_Anterior']
    df_comp_summary['Variacion_Porcentual'] = np.where(
        df_comp_summary['Requerimiento_Anterior'] > 0,
        (df_comp_summary['Variacion_Absoluta'] / df_comp_summary['Requerimiento_Anterior']) * 100,
        0
    )

    # Categorizar Impacto en Componentes
    def categorizar_componente(row):
        if row['Variacion_Porcentual'] >= umbral_subida:
            return '🔴 Incremento Crítico'
        elif row['Variacion_Porcentual'] <= umbral_bajada:
            return '🔵 Disminución Crítica'
        else:
            return '🟢 Estable'

    df_comp_summary['Categoria_Impacto'] = df_comp_summary.apply(categorizar_componente, axis=1)

    # Mostrar métricas del impacto en componentes
    criticos_subida = df_comp_summary[df_comp_summary['Categoria_Impacto'] == '🔴 Incremento Crítico'].shape[0]
    criticos_bajada = df_comp_summary[df_comp_summary['Categoria_Impacto'] == '🔵 Disminución Crítica'].shape[0]

    st.write("---")
    st.subheader("📊 Impacto Consolidado en Componentes (BOM Exploded)")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Componentes Totales Impactados", len(df_comp_summary))
    m2.metric("🔴 Incrementos Críticos", criticos_subida)
    m3.metric("🔵 Disminuciones Críticas", criticos_bajada)

    # Filtro interactivo de impacto
    categoria_seleccionada = st.multiselect(
        "Filtrar componentes mostrados por categoría de impacto:",
        options=['🔴 Incremento Crítico', '🔵 Disminución Crítica', '🟢 Estable'],
        default=['🔴 Incremento Crítico', '🔵 Disminución Crítica']
    )

    df_filtrado = df_comp_summary[df_comp_summary['Categoria_Impacto'].isin(categoria_seleccionada)]

    # Visualización de la tabla
    st.subheader("📋 Reporte de Materiales Afectados")
    st.dataframe(df_filtrado.style.format({
        'Requerimiento_Anterior': '{:,.2f}',
        'Requerimiento_Actual': '{:,.2f}',
        'Variacion_Absoluta': '{:+,.2f}',
        'Variacion_Porcentual': '{:+.1f}%'
    }))

    # 5. Función para exportar a Excel
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte_Impacto')
        processed_data = output.getvalue()
        return processed_data

    excel_data = to_excel(df_filtrado)

    st.download_button(
        label="📥 Descargar Reporte en Excel",
        data=excel_data,
        file_name='reporte_impacto_materiales.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

except Exception as e:
    st.error(f"Ocurrió un error al procesar el mapeo con la BOM. Asegúrate de que los archivos tengan las columnas correctas ('Producto', 'Componente', 'Cantidad_Por_Producto'). Detalle: {e}")
