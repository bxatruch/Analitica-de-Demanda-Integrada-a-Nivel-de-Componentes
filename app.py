import streamlit as st
import pandas as pd
import numpy as np

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales, tu BOM y opcionalmente el Lead Time para analizar variaciones consolidadas")

    # Panel lateral para configurar umbrales de alerta y filtros
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    st.sidebar.header("⏳ Filtro por Lead Time")
    opciones_lt = [
        "Todos",
        "Menor o igual a 30 días",
        "Menor o igual a 60 días",
        "Menor o igual a 90 días",
        "Menor o igual a 120 días",
        "Menor o igual a 150 días",
        "Menor o igual a 180 días",
        "Solo no definidos"
    ]
    filtro_lt_seleccionado = st.sidebar.selectbox("Filtrar componentes por Lead Time:", opciones_lt, index=0)

    st.write("### 📂 Carga de Archivos de Planificación")
    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts + Lead Time)", value=False)

    df_lead_time = None

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
        df_lead_time = pd.DataFrame({
            "Material": ["Componente A", "Componente B", "Componente C"],
            "Lead Time (Días)": [15, 45, 120]
        })
        st.success("Cargados datos de demostración con estructura mensual y Lead Times.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            file_ant = st.file_uploader("1. Forecast Anterior (Prod. Terminado)", type=["csv", "xlsx"])
        with col2:
            file_nuevo = st.file_uploader("2. Forecast Nuevo (Prod. Terminado)", type=["csv", "xlsx"])
        with col3:
            file_bom = st.file_uploader("3. Estructura BOM (Componentes)", type=["csv", "xlsx"])
        with col4:
            file_lt = st.file_uploader("4. Lead Time de Componentes (Opcional)", type=["csv", "xlsx"])

        if file_ant and file_nuevo and file_bom:
            df_fc_ant = pd.read_csv(file_ant) if file_ant.name.endswith('.csv') else pd.read_excel(file_ant)
            df_fc_nuevo = pd.read_csv(file_nuevo) if file_nuevo.name.endswith('.csv') else pd.read_excel(file_nuevo)
            df_bom = pd.read_csv(file_bom) if file_bom.name.endswith('.csv') else pd.read_excel(file_bom)
            
            if file_lt:
                df_lead_time = pd.read_csv(file_lt) if file_lt.name.endswith('.csv') else pd.read_excel(file_lt)
        else:
            st.warning("Por favor sube los tres primeros ficheros requeridos para proceder.")
            return

    # Procesamiento y Explosión de Materiales
    try:
        # 1. Estandarización Dinámica de la BOM
        col_material = [c for c in df_bom.columns if any(p in c.lower() for p in ["material", "componente", "part_number"])][0]
        col_cant_bom = [c for c in df_bom.columns if any(p in c.lower() for p in ["cant", "qty", "factor", "requerida"])][0]

        df_bom_clean = df_bom.copy()
        df_bom_clean.rename(columns={col_material: "Material", col_cant_bom: "Cantidad_BOM"}, inplace=True)

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

        merged_ant = pd.merge(df_bom_clean, df_fc_ant_clean[["Producto", "Demanda_Ant"]], on="Producto", how="inner")
        merged_ant["Demanda_Comp_Ant"] = merged_ant["Demanda_Ant"] * merged_ant["Cantidad_BOM"]

        merged_nuevo = pd.merge(df_bom_clean, df_fc_nuevo_clean[["Producto", "Demanda_Nueva"]], on="Producto", how="inner")
        merged_nuevo["Demanda_Comp_Nueva"] = merged_nuevo["Demanda_Nueva"] * merged_nuevo["Cantidad_BOM"]

        dtl_ant = merged_ant.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Ant"].sum()
        dtl_nuevo = merged_nuevo.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_dtl = pd.merge(dtl_ant, dtl_nuevo, on=["Material", "Producto"], how="outer").fillna(0)
        merged_dtl["Var_Abs_Prod"] = merged_dtl["Demanda_Comp_Nueva"] - merged_dtl["Demanda_Comp_Ant"]

        tot_ant = merged_ant.groupby(["Material"], as_index=False)["Demanda_Comp_Ant"].sum()
        tot_nuevo = merged_nuevo.groupby(["Material"], as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_tot = pd.merge(tot_ant, tot_nuevo, on="Material", how="outer").fillna(0)
        merged_tot["Var_Abs_Total"] = merged_tot["Demanda_Comp_Nueva"] - merged_tot["Demanda_Comp_Ant"]

        # Inicializar siempre la columna de Lead Time como 'no definido'
        merged_tot["Lead Time"] = "no definido"

        if df_lead_time is not None:
            col_mat_lt = [c for c in df_lead_time.columns if any(p in c.lower() for p in ["material", "componente", "part_number"])][0]
            col_val_lt = [c for c in df_lead_time.columns if any(p in c.lower() for p in ["lead", "time", "tiempo", "entrega"])][0]
            
            df_lt_clean = df_lead_time[[col_mat_lt, col_val_lt]].copy().rename(columns={col_mat_lt: "Material", col_val_lt: "Lead Time_val"})
            
            merged_tot = pd.merge(merged_tot, df_lt_clean, on="Material", how="left")
            merged_tot["Lead Time"] = merged_tot["Lead Time_val"].fillna("no definido")
            merged_tot.drop(columns=["Lead Time_val"], inplace=True)

        merged_tot["Variación % Total"] = (merged_tot["Var_Abs_Total"] / merged_tot["Demanda_Comp_Ant"]) * 100
        merged_tot["Variación % Total"] = merged_tot["Variación % Total"].replace([np.inf, -np.inf], np.nan).fillna(0)

        columnas_totales_interes = ["Material", "Var_Abs_Total", "Variación % Total", "Lead Time"]
        final_df = pd.merge(merged_dtl, merged_tot[columnas_totales_interes], on="Material")

        final_df["% Influencia en Variación"] = np.where(
            final_df["Var_Abs_Total"] != 0,
            (final_df["Var_Abs_Prod"] / final_df["Var_Abs_Total"]) * 100,
            0.0
        )

        def categorizar(row):
            var = row["Variación % Total"]
            if var >= umbral_subida:
                return "🔴 Incremento Crítico"
            elif var <= umbral_bajada:
                return "🔵 Disminución Crítica"
            else:
                return "🟢 Estable"

        final_df["Impacto Componente"] = final_df.apply(categorizar, axis=1)

        # Aplicación del Filtro de Lead Time en Pandas
        if filtro_lt_seleccionado != "Todos":
            if filtro_lt_seleccionado == "Solo no definidos":
                final_df = final_df[final_df["Lead Time"] == "no definido"]
            else:
                # Extraer el límite numérico (por ejemplo, 'Menor o igual a 30 días' -> 30)
                limite = int(filtro_lt_seleccionado.split("a ")[1].split(" ")[0])
                
                # Función para filtrar los valores numéricos y descartar 'no definido'
                def cumple_filtro_lt(val):
                    try:
                        return float(val) <= limite
                    except:
                        return False
                
                final_df = final_df[final_df["Lead Time"].apply(cumple_filtro_lt)]

        st.write("### 📈 Resumen de Impacto Global de Componentes (Filtrados)")
        totales_unicos = final_df.drop_duplicates(subset=["Material"]).copy()
        
        total_inc = len(totales_unicos[totales_unicos["Impacto Componente"] == "🔴 Incremento Crítico"])
        total_dec = len(totales_unicos[totales_unicos["Impacto Componente"] == "🔵 Disminución Crítica"])
        total_est = len(totales_unicos[totales_unicos["Impacto Componente"] == "🟢 Estable"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Incrementos Críticos", total_inc)
        m2.metric("Disminuciones Críticas", total_dec)
        m3.metric("Materiales Estables", total_est)

        st.write("### 🔍 Desglose de Componentes Explosionados")
        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
            default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"]
        )

        df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

        columnas_renombrar = {
            "Demanda_Comp_Ant": "Demanda Requerida Ant (Prod)",
            "Demanda_Comp_Nueva": "Demanda Requerida Nueva (Prod)",
            "Var_Abs_Prod": "Variación Requerida (Abs)",
            "Var_Abs_Total": "Variación Total Componente",
            "Variación % Total": "Variación % Total Componente",
            "Impacto Componente": "Impacto del Componente",
            "Lead Time": "Lead Time (Días/Info)"
        }

        df_presentacion = df_filtrado.rename(columns=columnas_renombrar)

        st.dataframe(df_presentacion.style.format({
            "Demanda Requerida Ant (Prod)": "{:.0f}",
            "Demanda Requerida Nueva (Prod)": "{:.0f}",
            "Variación Requerida (Abs)": "{:+,.0f}",
            "Variación Total Componente": "{:+,.0f}",
            "Variación % Total Componente": "{:+,.1f}%",
            "% Influencia en Variación": "{:+,.1f}%"
        }))

    except Exception as e:
        st.error(f"Ha ocurrido un error al procesar los archivos: {e}")

if __name__ == "__main__":
    main()