# Instalar streamlit si no está en el entorno (necesario en Google Colab)
try:
    import streamlit as st
except ImportError:
    !pip install -q streamlit
    import streamlit as st

import pandas as pd
import numpy as np

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales y tu BOM para analizar variaciones consolidadas")

    # Panel lateral para configurar umbrales de alerta
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    st.write("### 📂 Carga de Archivos de Planificación")
    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts)", value=False)

    if use_demo:
        df_fc_ant = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "01-ene": [1000, 500, 300],
            "01-feb": [1100, 400, 350]
        })
        df_fc_nuevo = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "01-ene": [1200, 300, 300],
            "01-feb": [1500, 200, 400]
        })
        df_bom = pd.DataFrame({
            "Producto": ["Producto A", "Producto A", "Producto B", "Producto C"],
            "Componente": ["Componente A", "Componente B", "Componente A", "Componente C"],
            "Cantidad requerida": [5, 2, 3, 4]
        })
        # Asegurar conversión de columnas a string incluso en el demo
        df_fc_ant.columns = df_fc_ant.columns.map(str)
        df_fc_nuevo.columns = df_fc_nuevo.columns.map(str)
        df_bom.columns = df_bom.columns.map(str)
        st.success("Cargados datos de demostración con estructura mensual.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            file_ant = st.file_uploader("1. Forecast Anterior (Prod. Terminado)", type=["csv", "xlsx"])
        with col2:
            file_nuevo = st.file_uploader("2. Forecast Nuevo (Prod. Terminado)", type=["csv", "xlsx"])
        with col3:
            file_bom = st.file_uploader("3. Estructura BOM (Componentes)", type=["csv", "xlsx"])

        if file_ant and file_nuevo and file_bom:
            df_fc_ant = pd.read_csv(file_ant) if file_ant.name.endswith('.csv') else pd.read_excel(file_ant)
            df_fc_nuevo = pd.read_csv(file_nuevo) if file_nuevo.name.endswith('.csv') else pd.read_excel(file_nuevo)
            df_bom = pd.read_csv(file_bom) if file_bom.name.endswith('.csv') else pd.read_excel(file_bom)
            
            # Convertir todas las cabeceras de columnas a strings inmediatamente al cargar
            df_fc_ant.columns = df_fc_ant.columns.map(str)
            df_fc_nuevo.columns = df_fc_nuevo.columns.map(str)
            df_bom.columns = df_bom.columns.map(str)
        else:
            st.warning("Por favor sube los tres ficheros requeridos para proceder.")
            return

    # Procesamiento y Explosión de Materiales
    try:
        # 1. Estandarización Dinámica de la BOM
        # Mapear 'Componente' -> 'Material'
        col_material = [c for c in df_bom.columns if any(p in c.lower() for p in ["material", "componente", "part_number"])][0]
        col_cant_bom = [c for c in df_bom.columns if any(p in c.lower() for p in ["cant", "qty", "factor", "requerida"])][0]

        df_bom_clean = df_bom.copy()
        df_bom_clean.rename(columns={col_material: "Material", col_cant_bom: "Cantidad_BOM"}, inplace=True)

        # Buscar columna Producto
        col_prod_bom = [c for c in df_bom_clean.columns if "prod" in c.lower()][0]
        df_bom_clean.rename(columns={col_prod_bom: "Producto"}, inplace=True)

        # 2. Identificación de Columnas Temporales (Meses) en los Forecasts
        palabras_mes = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

        col_meses_ant = [c for c in df_fc_ant.columns if any(m in c.lower() for m in palabras_mes)]
        col_meses_nue = [c for c in df_fc_nuevo.columns if any(m in c.lower() for m in palabras_mes)]

        col_prod_ant = [c for c in df_fc_ant.columns if "prod" in c.lower()][0]
        col_prod_nue = [c for c in df_fc_nuevo.columns if "prod" in c.lower()][0]

        df_fc_ant_clean = df_fc_ant.copy().rename(columns={col_prod_ant: "Producto"})
        df_fc_nuevo_clean = df_fc_nuevo.copy().rename(columns={col_prod_nue: "Producto"})

        # Consolidar Demanda Anual sumando todas las columnas de meses encontradas
        if col_meses_ant:
            df_fc_ant_clean["Demanda_Ant"] = df_fc_ant_clean[col_meses_ant].sum(axis=1)
        else:
            col_dem_ant = [c for c in df_fc_ant_clean.columns if any(p in c.lower() for p in ["demanda", "cant", "vol"])][0]
            df_fc_ant_clean["Demanda_Ant"] = df_fc_ant_clean[col_dem_ant]

        if col_meses_nue:
            df_fc_nuevo_clean["Demanda_Nueva"] = df_fc_nuevo_clean[col_meses_nue].sum(axis=1)
        else:
            col_dem_nue = [c for c in df_fc_nuevo_clean.columns if any(p in c.lower() for p in ["demanda", "cant", "vol"])][0]
            df_fc_nuevo_clean["Demanda_Nueva"] = df_fc_nuevo_clean[col_dem_nue]

        # --- EXPLOSIÓN DE DEMANDA ANTERIOR ---
        merged_ant = pd.merge(df_bom_clean, df_fc_ant_clean[["Producto", "Demanda_Ant"]], on="Producto", how="inner")
        merged_ant["Demanda_Comp_Ant"] = merged_ant["Demanda_Ant"] * merged_ant["Cantidad_BOM"]

        # --- EXPLOSIÓN DE DEMANDA NUEVA ---
        merged_nuevo = pd.merge(df_bom_clean, df_fc_nuevo_clean[["Producto", "Demanda_Nueva"]], on="Producto", how="inner")
        merged_nuevo["Demanda_Comp_Nueva"] = merged_nuevo["Demanda_Nueva"] * merged_nuevo["Cantidad_BOM"]

        # 1. Agrupar por Componente y Producto Terminado para el detalle cruzado
        dtl_ant = merged_ant.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Ant"].sum()
        dtl_nuevo = merged_nuevo.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_dtl = pd.merge(dtl_ant, dtl_nuevo, on=["Material", "Producto"], how="outer").fillna(0)
        merged_dtl["Var_Abs_Prod"] = merged_dtl["Demanda_Comp_Nueva"] - merged_dtl["Demanda_Comp_Ant"]

        # 2. Calcular Totales Consolidados por Material
        tot_ant = merged_ant.groupby(["Material"], as_index=False)["Demanda_Comp_Ant"].sum()
        tot_nuevo = merged_nuevo.groupby(["Material"], as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_tot = pd.merge(tot_ant, tot_nuevo, on="Material", how="outer").fillna(0)

        merged_tot["Var_Abs_Total"] = merged_tot["Demanda_Comp_Nueva"] - merged_tot["Demanda_Comp_Ant"]
        merged_tot["Variación % Total"] = (merged_tot["Var_Abs_Total"] / merged_tot["Demanda_Comp_Ant"]) * 100
        merged_tot["Variación % Total"] = merged_tot["Variación % Total"].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Unir totales de variación al DataFrame detallado
        final_df = pd.merge(merged_dtl, merged_tot[["Material", "Var_Abs_Total", "Variación % Total"]], on="Material")

        # 3. Calcular % de Influencia en la variación del componente
        final_df["% Influencia en Variación"] = np.where(
            final_df["Var_Abs_Total"] != 0,
            (final_df["Var_Abs_Prod"] / final_df["Var_Abs_Total"]) * 100,
            0.0
        )

        # Categorización
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
        st.write("### 📈 Resumen de Impacto Global de Componentes")
        totales_unicos = merged_tot.copy()
        totales_unicos["Impacto"] = totales_unicos.apply(lambda r: "🔴 Incremento Crítico" if r["Var_Abs_Total" ] > 0 and r["Variación % Total"] >= umbral_subida else ("🔵 Disminución Crítica" if r["Var_Abs_Total"] < 0 and r["Variación % Total"] <= umbral_bajada else "🟢 Estable"), axis=1)

        totales = totales_unicos["Impacto"].value_counts()
        m1, m2, m3 = st.columns(3)
        m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
        m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
        m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

        # Tabla Detallada
        st.write("### 🔍 Desglose de Componentes Explosionados y su Influencia por Producto")

        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
            default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"]
        )

        df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

        # Renombrar columnas para claridad visual
        df_presentacion = df_filtrado.rename(columns={
            "Demanda_Comp_Ant": "Demanda Requerida Ant (Prod)",
            "Demanda_Comp_Nueva": "Demanda Requerida Nueva (Prod)",
            "Var_Abs_Prod": "Variación Requerida (Abs)",
            "Var_Abs_Total": "Variación Total Componente",
            "Variación % Total": "Variación % Total Componente",
            "Impacto Componente": "Impacto del Componente"
        })

        st.dataframe(df_presentacion.style.format({
            "Demanda Requerida Ant (Prod)": "{:.0f}",
            "Demanda Requerida Nueva (Prod)": "{:.0f}",
            "Variación Requerida (Abs)": "{:+,.0f}",
            "Variación Total Componente": "{:+,.0f}",
            "Variación % Total Componente": "{:+,.1f}%",
            "% Influencia en Variación": "{:+,.1f}%"
        }))

    except Exception as e:
        st.error(f"Ha ocurrido un error al procesar y explosionar los archivos de demanda con la BOM: {e}")

if __name__ == "__main__":
    main()