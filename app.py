import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Comparador de Demanda", layout="wide")

st.title("📦 Comparador de Demanda para Purchasing Planners")
st.write("Compara dos releases de demanda para identificar de forma proactiva variaciones críticas de materiales.")

# 1. Carga de Archivos
col1, col2 = st.columns(2)
with col1:
    file_anterior = st.file_uploader("Cargar Release Anterior (CSV)", type=["csv"])
with col2:
    file_actual = st.file_uploader("Cargar Release Actual (CSV)", type=["csv"])

# Simulación de datos si no se suben archivos para poder probar la interfaz
if not file_anterior or not file_actual:
    st.info("💡 Sube dos archivos para empezar. Mientras tanto, se muestran datos de ejemplo:")
    
    # Crear datos ficticios
    data_ant = pd.DataFrame({
        'Material': ['MAT-001', 'MAT-002', 'MAT-003', 'MAT-004', 'MAT-005'],
        'Demanda_Anterior': [1000, 1500, 500, 2000, 800]
    })
    data_act = pd.DataFrame({
        'Material': ['MAT-001', 'MAT-002', 'MAT-003', 'MAT-004', 'MAT-005'],
        'Demanda_Actual': [1500, 300, 510, 2000, 100] # MAT-001 sube +50%, MAT-002 baja -80%, MAT-005 baja -87.5%
    })
else:
    data_ant = pd.read_csv(file_anterior)
    data_act = pd.read_csv(file_actual)

# 2. Procesamiento de Comparación
try:
    # Unir datasets por la columna clave del Material
    df_compare = pd.merge(data_ant, data_act, on="Material", how="outer").fillna(0)
    
    # Calcular diferencias
    df_compare['Variacion_Absoluta'] = df_compare['Demanda_Actual'] - df_compare['Demanda_Anterior']
    
    # Calcular variación porcentual evitando división por cero
    df_compare['Variacion_Porcentual'] = np.where(
        df_compare['Demanda_Anterior'] > 0,
        (df_compare['Variacion_Absoluta'] / df_compare['Demanda_Anterior']) * 100,
        0
    )
    
    # 3. Clasificación del Impacto
    umbral_subida = st.sidebar.slider("Umbral de incremento agresivo (%)", 10, 100, 30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de disminución agresiva (%)", -100, -10, -30, step=5)
    
    def categorizar(row):
        if row['Variacion_Porcentual'] >= umbral_subida:
            return '🔴 Incremento Crítico'
        elif row['Variacion_Porcentual'] <= umbral_bajada:
            return '🔵 Disminución Crítica'
        else:
            return '🟢 Estable'
            
    df_compare['Categoria_Impacto'] = df_compare.apply(categorizar, axis=1)
    
    # 4. Métricas Rápidas
    criticos_subida = df_compare[df_compare['Categoria_Impacto'] == '🔴 Incremento Crítico'].shape[0]
    criticos_bajada = df_compare[df_compare['Categoria_Impacto'] == '🔵 Disminución Crítica'].shape[0]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Materiales Analizados", len(df_compare))
    m2.metric("🔴 Incrementos Críticos", criticos_subida)
    m3.metric("🔵 Disminuciones Críticas", criticos_bajada)
    
    # Filtro interactivo
    categoria_seleccionada = st.multiselect(
        "Filtrar por impacto:", 
        options=['🔴 Incremento Crítico', '🔵 Disminución Crítica', '🟢 Estable'],
        default=['🔴 Incremento Crítico', '🔵 Disminución Crítica']
    )
    
    df_filtrado = df_compare[df_compare['Categoria_Impacto'].isin(categoria_seleccionada)]
    
    # Mostrar resultados
    st.subheader("Resultados del Análisis")
    st.dataframe(df_filtrado.style.format({
        'Demanda_Anterior': '{:,.0f}',
        'Demanda_Actual': '{:,.0f}',
        'Variacion_Absoluta': '{:+,.0f}',
        'Variacion_Porcentual': '{:+.1f}%'
    }))
    
except Exception as e:
    st.error(f"Error al procesar los archivos. Asegúrate de que tengan una columna llamada 'Material' y columnas numéricas para la demanda. Detalle: {e}")
