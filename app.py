import streamlit as st
import pandas as pd
import numpy as np

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts y la BOM para explosionar los requerimientos de componentes y analizar variaciones")

    # Panel lateral para configurar umbrales de alerta
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    st.write("### 📂 Carga de Archivos de Planificación")
    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts)", value=True)

    if use_demo:
        # Generar datos simulados internos
        # 1. Forecasts (Demanda de Productos Terminados)
        df_fc_ant = pd.DataFrame({
            "Producto": ["Televisor 4K", "Radio FM", "Smart Watch"],
            "Demanda_Ant": [100, 200, 150]
        })
        df_fc_nuevo = pd.DataFrame({
            "Producto": ["Televisor 4K", "Radio FM", "Smart Watch"],
            "Demanda_Nueva": [120, 300, 100]
        })
        # 2. BOM (Relación de Producto terminado -> Componente/Material y su cantidad requerida)
        df_bom = pd.DataFrame({
            "Producto": ["Televisor 4K", "Televisor 4K", "Radio FM", "Radio FM", "Smart Watch"],
            "Material": ["MAT-001", "MAT-003", "MAT-001", "MAT-002", "MAT-004"],
            "Descripción": ["Resistencia 10k", "Microcontrolador", "Resistencia 10k", "Condensador 47uF", "Pantalla OLED"],
            "Cantidad_BOM": [8, 1, 2, 1, 1] # cantidad de componentes por unidad de producto terminado
        })
        st.success("Cargados datos de demostración del flujo completo (Forecasts y BOM).")
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
        else:
            st.warning("Por favor sube los tres ficheros requeridos (Forecast Anterior, Nuevo y BOM) para proceder.")
            return

    # Procesamiento y Explosión de Materiales
    try:
        # Estandarizar nombres de columnas clave
        # Buscamos columnas de demanda numéricas dinámicamente
        col_dem_ant = [c for c in df_fc_ant.columns if "Demanda" in c or "Cant" in c or "Volume" in c][0]
        col_dem_nue = [c for c in df_fc_nuevo.columns if "Demanda" in c or "Cant" in c or "Volume" in c][0]
        col_cant_bom = [c for c in df_bom.columns if "Cant" in c or "Qty" in c or "Factor" in c][0]

        # Asegurar nombres de unión
        df_fc_ant.rename(columns={col_dem_ant: "Demanda_Ant"}, inplace=True)
        df_fc_nuevo.rename(columns={col_dem_nue: "Demanda_Nueva"}, inplace=True)
        df_bom.rename(columns={col_cant_bom: "Cantidad_BOM"}, inplace=True)

        # --- EXPLOSIÓN DE DEMANDA ANTERIOR ---
        # Unimos el Forecast de Producto Terminado con la BOM
        merged_ant = pd.merge(df_bom, df_fc_ant, on="Producto", how="inner")
        merged_ant["Demanda_Comp_Ant"] = merged_ant["Demanda_Ant"] * merged_ant["Cantidad_BOM"]

        # --- EXPLOSIÓN DE DEMANDA NUEVA ---
        merged_nuevo = pd.merge(df_bom, df_fc_nuevo, on="Producto", how="inner")
        merged_nuevo["Demanda_Comp_Nueva"] = merged_nuevo["Demanda_Nueva"] * merged_nuevo["Cantidad_BOM"]

        # 1. Agrupar por Componente y Producto Terminado para el detalle cruzado
        dtl_ant = merged_ant.groupby(["Material", "Descripción", "Producto"], as_index=False)["Demanda_Comp_Ant"].sum()
        dtl_nuevo = merged_nuevo.groupby(["Material", "Descripción", "Producto"], as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_dtl = pd.merge(dtl_ant, dtl_nuevo, on=["Material", "Descripción", "Producto"], how="outer").fillna(0)
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

        # 3. Calcular Influencia de cada Producto en la variación del componente
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
        totales_unicos["Impacto"] = totales_unicos.apply(lambda r: "🔴 Incremento Crítico" if r["Variación % Total"] >= umbral_subida else ("🔵 Disminución Crítica" if r["Variación % Total"] <= umbral_bajada else "🟢 Estable"), axis=1)

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
