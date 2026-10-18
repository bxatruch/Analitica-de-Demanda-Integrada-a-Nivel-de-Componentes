import streamlit as st
import pandas as pd
import numpy as np
import os

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales, tu BOM y Lead Times para analizar variaciones consolidadas")

    # Panel lateral para configurar umbrales de alerta y bloques
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    st.sidebar.markdown("--- ")
    st.sidebar.header("📦 Configuración de Bloques")
    bloques_input = st.sidebar.number_input("Cantidad de bloques (columnas/meses) a analizar", value=2.0, step=0.5)

    # Si la cantidad de bloques cambia, limpiamos el análisis guardado
    if "ultimo_bloque_analizado" not in st.session_state:
        st.session_state["ultimo_bloque_analizado"] = bloques_input

    if st.session_state["ultimo_bloque_analizado"] != bloques_input:
        st.session_state["ultimo_bloque_analizado"] = bloques_input
        if "analisis_resultado" in st.session_state:
            del st.session_state["analisis_resultado"]

    st.sidebar.markdown("--- ")
    st.sidebar.header("📥 Plantilla de Forecast")
    template_path = "/content/Forecast template.csv"
    if os.path.exists(template_path):
        with open(template_path, "rb") as file:
            st.sidebar.download_button(
                label="📥 Descargar Plantilla Forecast (CSV)",
                data=file,
                file_name="Forecast_template.csv",
                mime="text/csv"
            )
    else:
        st.sidebar.info("Archivo de plantilla no encontrado en el entorno de ejecución.")

    # Instrucciones iniciales del layout
    with st.expander("ℹ️ Instrucciones de Formato y Estructura de Ficheros (Layout)", expanded=True):
        st.markdown("""
        ### 📑 Formato de Archivos Requeridos
        Para garantizar un correcto funcionamiento de la herramienta, asegúrate de que tus archivos cumplan con el siguiente layout:
        
        1. **Forecast (Anterior y Nuevo):**
           * Debe cargarse en formato **tabular**.
           * Debe contener la columna **Producto** (nombre o identificador del Producto Terminado).
           * Debe contener la columna **Unidad de medida**.
           * Debe poseer las columnas de **Meses** de planificación con su respectiva **Proyección de venta por mes** (ej. *ene, feb, mar...*).
        
        2. **Estructura BOM (Lista de Materiales):**
           * Debe contener una relación del **Producto**, su **Componente** (o Material) y la **Cantidad requerida** (Factor de explosión).

        3. **Lead Times (Tiempos de Entrega):**
           * Debe contener la columna del **Componente** (o Material) y su tiempo de entrega (por ejemplo, columna **Lead Time** en días).
        """)

    st.write("### 📂 Carga de Archivos de Planificación")

    # Usar llaves para poder limpiar los file uploaders usando session_state
    if "uploader_key_ant" not in st.session_state:
        st.session_state["uploader_key_ant"] = 100
    if "uploader_key_nuevo" not in st.session_state:
        st.session_state["uploader_key_nuevo"] = 200
    if "uploader_key_bom" not in st.session_state:
        st.session_state["uploader_key_bom"] = 300
    if "uploader_key_lt" not in st.session_state:
        st.session_state["uploader_key_lt"] = 400

    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts + Lead Times)", value=False)

    ready_to_process = False
    df_fc_ant = None
    df_fc_nuevo = None
    df_bom = None
    df_lt = None

    if use_demo:
        df_fc_ant = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "Unidad de medida": ["Unidades", "Unidades", "Unidades"],
            "01-ene": [1000, 500, 300],
            "01-feb": [1100, 400, 350]
        })
        df_fc_nuevo = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "Unidad de medida": ["Unidades", "Unidades", "Unidades"],
            "01-ene": [1200, 300, 300],
            "01-feb": [1500, 200, 400]
        })
        df_bom = pd.DataFrame({
            "Producto": ["Producto A", "Producto A", "Producto B", "Producto C"],
            "Componente": ["Componente A", "Componente B", "Componente A", "Componente C"],
            "Cantidad requerida": [5, 2, 3, 4]
        })
        df_lt = pd.DataFrame({
            "Componente": ["Componente A", "Componente B", "Componente C"],
            "Lead Time": [15, 30, 45]
        })
        st.success("Cargados datos de demostración con estructura mensual y Lead Times.")
        ready_to_process = True
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            file_ant = st.file_uploader("1. Forecast Anterior", type=["csv", "xlsx"], key=f"ant_{st.session_state['uploader_key_ant']}")
        with col2:
            file_nuevo = st.file_uploader("2. Forecast Nuevo", type=["csv", "xlsx"], key=f"nuevo_{st.session_state['uploader_key_nuevo']}")
        with col3:
            file_bom = st.file_uploader("3. Estructura BOM", type=["csv", "xlsx"], key=f"bom_{st.session_state['uploader_key_bom']}")
        with col4:
            file_lt = st.file_uploader("4. Lead Times (Opcional)", type=["csv", "xlsx"], key=f"lt_{st.session_state['uploader_key_lt']}")

        if file_ant and file_nuevo and file_bom:
            df_fc_ant = pd.read_csv(file_ant) if file_ant.name.endswith('.csv') else pd.read_excel(file_ant)
            df_fc_nuevo = pd.read_csv(file_nuevo) if file_nuevo.name.endswith('.csv') else pd.read_excel(file_nuevo)
            df_bom = pd.read_csv(file_bom) if file_bom.name.endswith('.csv') else pd.read_excel(file_bom)
            if file_lt:
                df_lt = pd.read_csv(file_lt) if file_lt.name.endswith('.csv') else pd.read_excel(file_lt)
            ready_to_process = True
        else:
            st.warning("Por favor sube los tres primeros ficheros requeridos para proceder.")
            if "analisis_resultado" in st.session_state:
                del st.session_state["analisis_resultado"]

    # Botones de Acción (Ejecutar y Resetear)
    if ready_to_process:
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            ejecutar = st.button("🚀 Ejecutar Análisis", use_container_width=True)
        with c_act2:
            resetear = st.button("🗑️ Resetear / Limpiar Datos", use_container_width=True)

        if resetear:
            st.session_state["uploader_key_ant"] += 1
            st.session_state["uploader_key_nuevo"] += 1
            st.session_state["uploader_key_bom"] += 1
            st.session_state["uploader_key_lt"] += 1
            if "analisis_resultado" in st.session_state:
                del st.session_state["analisis_resultado"]
            st.rerun()

        if ejecutar:
            palabras_mes = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            col_meses_ant = [c for c in df_fc_ant.columns if any(m in c.lower() for m in palabras_mes)]
            col_meses_nue = [c for c in df_fc_nuevo.columns if any(m in c.lower() for m in palabras_mes)]
            meses_comunes = [m for m in col_meses_ant if m in col_meses_nue]
            columnas_disponibles = len(meses_comunes)

            is_not_int = not float(bloques_input).is_integer()
            valor_int = int(bloques_input) if not is_not_int else 0

            if is_not_int or valor_int <= 0 or valor_int > columnas_disponibles:
                st.error("❌ Error de bloques definidos")
                if "analisis_resultado" in st.session_state:
                    del st.session_state["analisis_resultado"]
                return

            try:
                col_material = [c for c in df_bom.columns if any(p in c.lower() for p in ["material", "componente", "part_number"])][0]
                col_cant_bom = [c for c in df_bom.columns if any(p in c.lower() for p in ["cant", "qty", "factor", "requerida"])][0]

                df_bom_clean = df_bom.copy()
                df_bom_clean.rename(columns={col_material: "Material", col_cant_bom: "Cantidad_BOM"}, inplace=True)

                col_prod_bom = [c for c in df_bom_clean.columns if "prod" in c.lower()][0]
                df_bom_clean.rename(columns={col_prod_bom: "Producto"}, inplace=True)

                col_prod_ant = [c for c in df_fc_ant.columns if "prod" in c.lower()][0]
                col_prod_nue = [c for c in df_fc_nuevo.columns if "prod" in c.lower()][0]

                df_fc_ant_clean = df_fc_ant.copy().rename(columns={col_prod_ant: "Producto"})
                df_fc_nuevo_clean = df_fc_nuevo.copy().rename(columns={col_prod_nue: "Producto"})

                meses_a_analizar = meses_comunes[:valor_int]
                df_fc_ant_clean["Demanda_Ant"] = df_fc_ant_clean[meses_a_analizar].sum(axis=1)
                df_fc_nuevo_clean["Demanda_Nueva"] = df_fc_nuevo_clean[meses_a_analizar].sum(axis=1)

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

                # Procesar Lead Times si están disponibles
                has_lead_times = (df_lt is not None)
                if has_lead_times:
                    try:
                        col_lt_mat = [c for c in df_lt.columns if any(p in c.lower() for p in ["material", "componente", "part_number"])][0]
                        col_lt_val = [c for c in df_lt.columns if any(p in c.lower() for p in ["lead", "time", "tiempo", "entrega"])][0]
                        df_lt_clean = df_lt[[col_lt_mat, col_lt_val]].copy().rename(columns={col_lt_mat: "Material", col_lt_val: "Lead Time"})
                        merged_tot = pd.merge(merged_tot, df_lt_clean, on="Material", how="left").fillna({"Lead Time": 0})
                    except Exception as lt_err:
                        st.warning(f"No se pudo procesar el formato del archivo de Lead Times: {lt_err}")

                final_df = pd.merge(merged_dtl, merged_tot, on="Material")
                final_df["% Influencia en Variación"] = np.where(
                    final_df["Var_Abs_Total"] != 0,
                    (final_df["Var_Abs_Prod"] / final_df["Var_Abs_Total"]) * 100,
                    0.0
                )

                st.session_state["analisis_resultado"] = {
                    "final_df": final_df,
                    "merged_tot": merged_tot,
                    "valor_int": valor_int,
                    "meses_a_analizar": meses_a_analizar,
                    "has_lt": has_lead_times
                }

            except Exception as e:
                st.error(f"Ha ocurrido un error al procesar y explosionar los archivos de demanda con la BOM: {e}")
                if "analisis_resultado" in st.session_state:
                    del st.session_state["analisis_resultado"]

        # Renderizar resultados
        if "analisis_resultado" in st.session_state:
            res = st.session_state["analisis_resultado"]
            final_df = res["final_df"]
            merged_tot = res["merged_tot"]
            valor_int = res["valor_int"]
            meses_a_analizar = res["meses_a_analizar"]
            has_lt = res.get("has_lt", False)

            def categorizar(row):
                var = row["Variación % Total"]
                if var >= umbral_subida:
                    return "🔴 Incremento Crítico"
                elif var <= umbral_bajada:
                    return "🔵 Disminución Crítica"
                else:
                    return "🟢 Estable"

            final_df["Impacto Componente"] = final_df.apply(categorizar, axis=1)

            st.write(f"### 📈 Resumen de Impacto Global (Análisis limitado a {valor_int} meses: {', '.join(meses_a_analizar)})")
            totales_unicos = merged_tot.copy()
            totales_unicos["Impacto"] = totales_unicos.apply(lambda r: "🔴 Incremento Crítico" if r["Var_Abs_Total" ] > 0 and r["Variación % Total"] >= umbral_subida else ("🔵 Disminución Crítica" if r["Var_Abs_Total"] < 0 and r["Variación % Total"] <= umbral_bajada else "🟢 Estable"), axis=1)

            totales = totales_unicos["Impacto"].value_counts()
            m1, m2, m3 = st.columns(3)
            m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
            m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
            m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

            st.write("### 🔍 Desglose de Componentes Explosionados y su Influencia por Producto")

            # Bloque de filtros
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filtro_impacto = st.multiselect(
                    "Filtrar por categoría de Impacto:",
                    options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
                    default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
                    key="multiselect_filtro_impacto"
                )

            # Filtro Dropdown para Lead Time
            lead_time_limite = None
            if has_lt:
                max_lt = int(final_df["Lead Time"].max())
                # Crear rangos en bloques de 30 días basándose en el máximo encontrado
                if max_lt > 0:
                    opciones_lt = ["Mostrar Todos"] + [f"Menor a {d} días" for d in range(30, max_lt + 31, 30)]
                else:
                    opciones_lt = ["Mostrar Todos"]

                with f_col2:
                    seleccion_lt = st.selectbox(
                        "Filtrar por Lead Time del Componente:",
                        options=opciones_lt,
                        index=0,
                        key="selectbox_filtro_lt"
                    )
                    if seleccion_lt != "Mostrar Todos":
                        lead_time_limite = int(seleccion_lt.split(" ")[2])

            # Aplicar Filtro de Impacto
            df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)]

            # Aplicar Filtro de Lead Time
            if lead_time_limite is not None:
                df_filtrado = df_filtrado[df_filtrado["Lead Time"] < lead_time_limite]

            df_filtrado = df_filtrado.sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

            cols_renombrar = {
                "Demanda_Comp_Ant": "Demanda Requerida Ant (Prod)",
                "Demanda_Comp_Nueva": "Demanda Requerida Nueva (Prod)",
                "Var_Abs_Prod": "Variación Requerida (Abs)",
                "Var_Abs_Total": "Variación Total Componente",
                "Variación % Total": "Variación % Total Componente",
                "Impacto Componente": "Impacto del Componente"
            }
            if has_lt:
                cols_renombrar["Lead Time"] = "Lead Time (Días)"

            df_presentacion = df_filtrado.rename(columns=cols_renombrar)

            formatos = {
                "Demanda Requerida Ant (Prod)": "{:.0f}",
                "Demanda Requerida Nueva (Prod)": "{:.0f}",
                "Variación Requerida (Abs)": "{:+,.0f}",
                "Variación Total Componente": "{:+,.0f}",
                "Variación % Total Componente": "{:+,.1f}%",
                "% Influencia en Variación": "{:+,.1f}%"
            }
            if has_lt:
                formatos["Lead Time (Días)"] = "{:.0f}"

            st.dataframe(df_presentacion.style.format(formatos))

if __name__ == "__main__":
    main()
