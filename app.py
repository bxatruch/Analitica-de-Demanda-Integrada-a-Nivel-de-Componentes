
import streamlit as st
import pandas as pd
import numpy as np
import os

def obtener_plantilla_bytes(ruta_archivo):
    """
    Lee un archivo local de forma segura y devuelve sus bytes junto con su nombre.
    Útil para st.download_button.
    """
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "rb") as f:
            datos_bytes = f.read()
        nombre_archivo = os.path.basename(ruta_archivo)
        return datos_bytes, nombre_archivo
    return None, None

def obtener_columna_interactiva(df, palabras_clave, nombre_concepto, nombre_archivo, key_prefix):
    """
    Intenta buscar una columna que contenga las palabras clave de forma automática.
    Si no la encuentra, despliega un selectbox en Streamlit para que el usuario la seleccione manualmente.
    """
    columnas = df.columns.tolist()
    coincidencias = [c for c in columnas if any(p in str(c).lower() for p in palabras_clave)]

    if coincidencias:
        return coincidencias[0]

    st.warning(f"⚠️ No se detectó automáticamente la columna de **{nombre_concepto}** en el archivo **{nombre_archivo}**.")
    col_seleccionada = st.selectbox(
        f"Por favor, selecciona qué columna corresponde a **{nombre_concepto}**:",
        options=columnas,
        key=f"{key_prefix}_select_{nombre_concepto.replace(' ', '_').lower()}"
    )
    return col_seleccionada

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales y tu BOM para analizar variaciones consolidadas")

    # Panel lateral para configurar umbrales de alerta y cantidad de bloques
    st.sidebar.header("⚙️ Configuración del Análisis")
    cant_bloques = st.sidebar.slider("Cantidad de bloques (meses) a evaluar", min_value=1, max_value=12, value=3, step=1)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    # --- SECCIÓN DE DESCARGA DE PLANTILLAS ---
    st.write("### 📥 Descarga de Plantillas Oficiales (Machotes)")
    st.info("Por favor, descarga estas plantillas de referencia para asegurar que tus archivos tengan el formato correcto antes de subirlos.")
    col_desc_1, col_desc_2, col_desc_3 = st.columns(3)

    with col_desc_1:
        st.markdown("**1. Plantilla de Forecast**")
        bytes_f, name_f = obtener_plantilla_bytes("assets/plantilla_forecast.xlsx")
        if bytes_f:
            st.download_button(
                label="📊 Descargar Plantilla Forecast",
                data=bytes_f,
                file_name=name_f,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_forecast_v2"
            )
        else:
            st.caption("⚠️ `assets/plantilla_forecast.xlsx` no encontrada.")

    with col_desc_2:
        st.markdown("**2. Plantilla de BOM**")
        bytes_b, name_b = obtener_plantilla_bytes("assets/plantilla_bom.xlsx")
        if bytes_b:
            st.download_button(
                label="⚙️ Descargar Plantilla BOM",
                data=bytes_b,
                file_name=name_b,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_bom_v2"
            )
        else:
            st.caption("⚠️ `assets/plantilla_bom.xlsx` no encontrada.")

    with col_desc_3:
        st.markdown("**3. Plantilla de Lead Times**")
        bytes_l, name_l = obtener_plantilla_bytes("assets/plantilla_lead_times.xlsx")
        if bytes_l:
            st.download_button(
                label="⏳ Descargar Plantilla Lead Times",
                data=bytes_l,
                file_name=name_l,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_lt_v2"
            )
        else:
            st.caption("⚠️ `assets/plantilla_lead_times.xlsx` no encontrada.")

    st.markdown("---")
    st.write("### 📂 Carga de Archivos de Planificación")
    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts)", value=False)

    if use_demo:
        df_fc_ant = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "01-ene": [1000, 500, 300],
            "01-feb": [1100, 400, 350],
            "01-mar": [950, 450, 320],
            "01-abr": [1200, 600, 400]
        })
        df_fc_nuevo = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "01-ene": [1200, 300, 300],
            "01-feb": [1500, 200, 400],
            "01-mar": [1000, 410, 330],
            "01-abr": [1100, 500, 410]
        })
        df_bom = pd.DataFrame({
            "Producto": ["Producto A", "Producto A", "Producto B", "Producto C"],
            "Componente": ["Componente A", "Componente B", "Componente A", "Componente C"],
            "Cantidad requerida": [5, 2, 3, 4]
        })
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
            df_fc_ant = pd.read_csv(file_ant) if file_ant.name.endswith(".csv") else pd.read_excel(file_ant)
            df_fc_nuevo = pd.read_csv(file_nuevo) if file_nuevo.name.endswith(".csv") else pd.read_excel(file_nuevo)
            df_bom = pd.read_csv(file_bom) if file_bom.name.endswith(".csv") else pd.read_excel(file_bom)

            if df_fc_ant.empty or df_fc_nuevo.empty or df_bom.empty:
                st.error("❌ Uno o más archivos subidos están vacíos. Por favor verifica su contenido.")
                return
            else:
                with st.expander("🔍 Vista previa de los archivos cargados"):
                    st.subheader("Forecast Anterior")
                    st.dataframe(df_fc_ant.head(3), use_container_width=True)
                    st.subheader("Forecast Nuevo")
                    st.dataframe(df_fc_nuevo.head(3), use_container_width=True)
                    st.subheader("Estructura BOM")
                    st.dataframe(df_bom.head(3), use_container_width=True)
        else:
            st.warning("Por favor sube los tres ficheros requeridos para proceder.")
            return

    # Procesamiento y Explosión de Materiales
    try:
        st.write("### 🛠️ Estandarización de Estructuras")
        col_material = obtener_columna_interactiva(df_bom, ["material", "componente", "part_number"], "Material o Componente", "Estructura BOM", "bom")
        col_cant_bom = obtener_columna_interactiva(df_bom, ["cant", "qty", "factor", "requerida"], "Cantidad en BOM", "Estructura BOM", "bom")
        col_prod_bom = obtener_columna_interactiva(df_bom, ["prod"], "Producto Terminado", "Estructura BOM", "bom")

        df_bom_clean = df_bom.copy()
        df_bom_clean.rename(columns={col_material: "Material", col_cant_bom: "Cantidad_BOM", col_prod_bom: "Producto"}, inplace=True)
        df_bom_clean["Cantidad_BOM"] = pd.to_numeric(df_bom_clean["Cantidad_BOM"], errors='coerce').fillna(0)

        palabras_mes = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

        col_meses_ant = [c for c in df_fc_ant.columns if any(m in str(c).lower() for m in palabras_mes)]
        col_meses_nue = [c for c in df_fc_nuevo.columns if any(m in str(c).lower() for m in palabras_mes)]

        # Filtrar bloques según selección del planner
        col_meses_ant_eval = col_meses_ant[:cant_bloques]
        col_meses_nue_eval = col_meses_nue[:cant_bloques]

        col_prod_ant = obtener_columna_interactiva(df_fc_ant, ["prod"], "Producto", "Forecast Anterior", "fc_ant")
        col_prod_nue = obtener_columna_interactiva(df_fc_nuevo, ["prod"], "Producto", "Forecast Nuevo", "fc_nue")

        df_fc_ant_clean = df_fc_ant.copy().rename(columns={col_prod_ant: "Producto"})
        df_fc_nuevo_clean = df_fc_nuevo.copy().rename(columns={col_prod_nue: "Producto"})

        if col_meses_ant_eval and col_meses_nue_eval:
            st.success(f"📅 Evaluando dinámicamente mes a mes para los bloques: {', '.join(col_meses_ant_eval)}")
            mes_evaluar = st.selectbox("Selecciona el Mes/Bloque específico a visualizar:", col_meses_ant_eval)
            idx_mes = col_meses_ant_eval.index(mes_evaluar)
            mes_evaluar_nuevo = col_meses_nue_eval[idx_mes] if idx_mes < len(col_meses_nue_eval) else col_meses_nue_eval[0]

            df_fc_ant_clean["Demanda_Ant"] = pd.to_numeric(df_fc_ant_clean[mes_evaluar], errors='coerce').fillna(0)
            df_fc_nuevo_clean["Demanda_Nueva"] = pd.to_numeric(df_fc_nuevo_clean[mes_evaluar_nuevo], errors='coerce').fillna(0)
        else:
            col_dem_ant = obtener_columna_interactiva(df_fc_ant_clean, ["demanda", "cant", "vol", "total"], "Cantidad / Volumen Demanda", "Forecast Anterior", "fc_ant_vol")
            col_dem_nue = obtener_columna_interactiva(df_fc_nuevo_clean, ["demanda", "cant", "vol", "total"], "Cantidad / Volumen Demanda", "Forecast Nuevo", "fc_nue_vol")
            df_fc_ant_clean["Demanda_Ant"] = pd.to_numeric(df_fc_ant_clean[col_dem_ant], errors='coerce').fillna(0)
            df_fc_nuevo_clean["Demanda_Nueva"] = pd.to_numeric(df_fc_nuevo_clean[col_dem_nue], errors='coerce').fillna(0)

        # --- EXPLOSIÓN ---
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
        merged_tot["Variación % Total"] = (merged_tot["Var_Abs_Total"] / merged_tot["Demanda_Comp_Ant"]) * 100
        merged_tot["Variación % Total"] = merged_tot["Variación % Total"].replace([np.inf, -np.inf], np.nan).fillna(0)

        final_df = pd.merge(merged_dtl, merged_tot[["Material", "Var_Abs_Total", "Variación % Total"]], on="Material")
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

        st.write("### 📈 Resumen de Impacto Global de Componentes")
        totales_unicos = merged_tot.copy()
        totales_unicos["Impacto"] = totales_unicos.apply(lambda r: "🔴 Incremento Crítico" if r["Var_Abs_Total" ] > 0 and r["Variación % Total"] >= umbral_subida else ("🔵 Disminución Crítica" if r["Var_Abs_Total"] < 0 and r["Variación % Total" ] <= umbral_bajada else "🟢 Estable"), axis=1)

        totales = totales_unicos["Impacto"].value_counts()
        m1, m2, m3 = st.columns(3)
        m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
        m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
        m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

        st.write("### 🔍 Desglose de Componentes")
        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
            default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"]
        )

        df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

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
