import streamlit as st
import pandas as pd
import numpy as np

def main():
    st.set_page_config(page_title="Comparador de Demanda", layout="wide")

    st.title("📊 Comparador de Releases de Demanda Consolidada")
    st.subheader("Analiza el impacto total de tus componentes e identifica qué productos influyen más en la variación")

    # Panel lateral para configurar umbrales de alerta
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    # Generar datos simulados donde se incluye la columna 'Producto' para rastrear la procedencia
    data_v1 = {
        "Material": ["MAT-001", "MAT-002", "MAT-001", "MAT-003", "MAT-002", "MAT-004"],
        "Descripción": ["Resistencia 10k", "Condensador 47uF", "Resistencia 10k", "Microcontrolador", "Condensador 47uF", "Pantalla OLED"],
        "Producto": ["Televisor 4K", "Control Remoto", "Radio FM", "Televisor 4K", "Radio FM", "Smart Watch"],
        "Demanda_V1": [800, 300, 400, 300, 200, 150]
    }

    data_v2 = {
        "Material": ["MAT-001", "MAT-002", "MAT-003", "MAT-004", "MAT-001", "MAT-002"],
        "Producto": ["Televisor 4K", "Control Remoto", "Televisor 4K", "Smart Watch", "Radio FM", "Radio FM"],
        "Demanda_V2": [1000, 120, 300, 250, 600, 200]
    }

    df_v1_demo = pd.DataFrame(data_v1)
    df_v2_demo = pd.DataFrame(data_v2)

    st.write("### 📂 Carga de Datos")
    use_demo = st.checkbox("Usar datos de ejemplo para demostración (con asignación de Producto)", value=True)

    if use_demo:
        df_v1 = df_v1_demo
        df_v2 = df_v2_demo
        st.success("Usando datos de demostración con trazabilidad de productos.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            file1 = st.file_uploader("Cargar Release Anterior (CSV/Excel)", type=["csv", "xlsx"])
        with col2:
            file2 = st.file_uploader("Cargar Nuevo Release (CSV/Excel)", type=["csv", "xlsx"])

        if file1 and file2:
            df_v1 = pd.read_csv(file1) if file1.name.endswith('.csv') else pd.read_excel(file1)
            df_v2 = pd.read_csv(file2) if file2.name.endswith('.csv') else pd.read_excel(file2)
        else:
            st.warning("Por favor, sube ambos archivos de demanda o activa la casilla de datos de ejemplo.")
            return

    # Procesamiento
    try:
        col_demanda_v1 = [c for c in df_v1.columns if "Demanda" in c][0]
        col_demanda_v2 = [c for c in df_v2.columns if "Demanda" in c][0]

        # Asegurar columna de Producto
        for df in [df_v1, df_v2]:
            if "Producto" not in df.columns:
                df["Producto"] = "Producto No Especificado"

        # 1. Agrupar por Material y Producto para tener el detalle cruzado
        df_v1_dtl = df_v1.groupby(["Material", "Producto"], as_index=False)[col_demanda_v1].sum()
        df_v2_dtl = df_v2.groupby(["Material", "Producto"], as_index=False)[col_demanda_v2].sum()

        # Unir detalle
        merged_dtl = pd.merge(df_v1_dtl, df_v2_dtl, on=["Material", "Producto"], how="outer").fillna(0)

        # Columnas unificadas para el detalle
        col_ant_dtl = f"{col_demanda_v1}_ant" if col_demanda_v1 == col_demanda_v2 else col_demanda_v1
        col_nue_dtl = f"{col_demanda_v2}_nuevo" if col_demanda_v1 == col_demanda_v2 else col_demanda_v2
        merged_dtl.rename(columns={col_demanda_v1: col_ant_dtl, col_demanda_v2: col_nue_dtl}, inplace=True)

        # Variación individual por Producto-Material
        merged_dtl["Var_Abs_Prod"] = merged_dtl[col_nue_dtl] - merged_dtl[col_ant_dtl]

        # 2. Calcular Totales Consolidados por Material
        df_v1_tot = df_v1.groupby(["Material"], as_index=False)[col_demanda_v1].sum()
        df_v2_tot = df_v2.groupby(["Material"], as_index=False)[col_demanda_v2].sum()

        merged_tot = pd.merge(df_v1_tot, df_v2_tot, on="Material", suffixes=("_ant", "_nuevo"))
        col_ant_tot = f"{col_demanda_v1}_ant" if col_demanda_v1 == col_demanda_v2 else col_demanda_v1
        col_nue_tot = f"{col_demanda_v2}_nuevo" if col_demanda_v1 == col_demanda_v2 else col_demanda_v2

        merged_tot["Var_Abs_Total"] = merged_tot[col_nue_tot] - merged_tot[col_ant_tot]
        merged_tot["Variación % Total"] = (merged_tot["Var_Abs_Total"] / merged_tot[col_ant_tot]) * 100
        merged_tot["Variación % Total"] = merged_tot["Variación % Total"].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Unir Totales al Detalle
        final_df = pd.merge(merged_dtl, merged_tot[["Material", "Var_Abs_Total", "Variación % Total"]], on="Material")

        # 3. Calcular Porcentajes de Influencia/Participación en la variación
        # % de Influencia = (Variación del Producto / Variación Absoluta Total del Componente) * 100
        final_df["% Influencia en Variación"] = np.where(
            final_df["Var_Abs_Total"] != 0,
            (final_df["Var_Abs_Prod"] / final_df["Var_Abs_Total"]) * 100,
            0.0
        )

        # Categorizar sobre el Total Consolidado del Componente
        def categorizar(row):
            var = row["Variación % Total"]
            if var >= umbral_subida:
                return "🔴 Incremento Crítico"
            elif var <= umbral_bajada:
                return "🔵 Disminución Crítica"
            else:
                return "🟢 Estable"

        final_df["Impacto Componente"] = final_df.apply(categorizar, axis=1)

        # Resumen de Métricas Consolidadas únicas
        st.write("### 📈 Resumen de Impacto de Componentes")
        totales_unicos = merged_tot.copy()
        totales_unicos["Impacto"] = totales_unicos.apply(lambda r: "🔴 Incremento Crítico" if r["Variación % Total"] >= umbral_subida else ("🔵 Disminución Crítica" if r["Variación % Total"] <= umbral_bajada else "🟢 Estable"), axis=1)

        totales = totales_unicos["Impacto"].value_counts()
        m1, m2, m3 = st.columns(3)
        m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
        m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
        m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

        # Tabla Detallada
        st.write("### 🔍 Desglose por Componente e Influencia del Producto")

        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
            default=["🔴 Incremento Crítico", "🔵 Disminución Crítica"]
        )

        df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

        # Renombrar columnas para claridad visual del usuario final
        df_presentacion = df_filtrado.rename(columns={
            col_ant_dtl: "Demanda Anterior (Prod)",
            col_nue_dtl: "Demanda Nueva (Prod)",
            "Var_Abs_Prod": "Variación Prod (Abs)",
            "Var_Abs_Total": "Variación Total Componente",
            "Variación % Total": "Variación % Total Componente",
            "Impacto Componente": "Impacto del Componente"
        })

        st.dataframe(df_presentacion.style.format({
            "Demanda Anterior (Prod)": "{:.0f}",
            "Demanda Nueva (Prod)": "{:.0f}",
            "Variación Prod (Abs)": "{:+,.0f}",
            "Variación Total Componente": "{:+,.0f}",
            "Variación % Total Componente": "{:+,.1f}%",
            "% Influencia en Variación": "{:+,.1f}%"
        }))

    except Exception as e:
        st.error(f"Asegúrate de que los archivos contengan las columnas clave: 'Material', 'Producto' y sus respectivas demandas. Error: {e}")

if __name__ == "__main__":
    main()
