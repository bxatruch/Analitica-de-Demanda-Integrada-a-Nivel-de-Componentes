import streamlit as st
import pandas as pd
import numpy as np
import os

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales y tu BOM para analizar variaciones consolidadas")

    # Inicializar estados de la aplicación
    if "analizar" not in st.session_state:
        st.session_state.analizar = False
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # Panel lateral para configurar umbrales de alerta y controles de flujo
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    st.sidebar.markdown("---")
    st.sidebar.header("🎮 Control de Ejecución")

    # Botón para reiniciar todo el análisis y vaciar archivos cargados
    if st.sidebar.button("🔄 Resetear Aplicación", use_container_width=True):
        st.session_state.analizar = False
        st.session_state.uploader_key += 1
        st.rerun()

    # --- SECCIÓN DE DESCARGA DIRECTA DE PLANTILLAS BASE --- 
    st.markdown("### 📐 Descarga de Plantillas Base")
    st.markdown("Descarga de manera directa los archivos modelo para estructurar tus datos:")

    # Definir la ruta de la carpeta assets de forma segura
    assets_dir = "assets"

    # Lista de tus archivos para evitar repetir código
    archivos = {
        "Plantilla Forecast": "plantilla_forecast.xlsx",
        "Plantilla BOM": "plantilla_bom.xlsx",
        "Plantilla Lead Times": "plantilla_lead_times.xlsx",
    }

    col_temp1, col_temp2, col_temp3 = st.columns(3)
    columnas = [col_temp1, col_temp2, col_temp3]

    for i, (label, nombre_archivo) in enumerate(archivos.items()):
        ruta_completa = os.path.join(assets_dir, nombre_archivo)
        with columnas[i]:
            try:
                if os.path.exists(ruta_completa):
                    with open(ruta_completa, "rb") as f:
                        bytes_data = f.read()
                    st.download_button(
                        label=f"📁 Descargar {label}",
                        data=bytes_data,
                        file_name=nombre_archivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.warning(f"⚠️ {nombre_archivo} no encontrado en la carpeta '{assets_dir}'")
            except Exception as e:
                st.error(f"Error al leer {nombre_archivo}: {str(e)}")

    st.markdown("---")

    st.write("### 📂 Carga de Archivos de Planificación")
    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts)", value=False) 

    if use_demo:
        df_fc_ant = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "01-ene": [1000, 500, 300],
            "01-feb": [1100, 400, 350],
            "01-mar": [1200, 450, 310],
            "01-abr": [1300, 420, 320],
            "01-may": [1400, 480, 330],
            "01-jun": [1500, 410, 340]
        })
        df_fc_nuevo = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "01-ene": [1200, 300, 300],
            "01-feb": [1500, 200, 400],
            "01-mar": [1100, 390, 320],
            "01-abr": [1400, 460, 350],
            "01-may": [1600, 510, 300],
            "01-jun": [1700, 400, 310]
        })
        df_bom = pd.DataFrame({
            "Producto": ["Producto A", "Producto A", "Producto B", "Producto C"],
            "Componente": ["Componente A", "Componente B", "Componente A", "Componente C"],
            "Cantidad requerida": [5, 2, 3, 4]
        })
        st.success("Cargados datos de demostración con estructura mensual extendida (Ene-Jun).")
        st.session_state.analizar = True
    else:
        col1, col2, col3 = st.columns(3)
        key_suffix = f"_reset_{st.session_state.uploader_key}"
        with col1:
            file_ant = st.file_uploader("1. Forecast Anterior (Prod. Terminado)", type=["csv", "xlsx"], key=f"file_ant{key_suffix}")
        with col2:
            file_nuevo = st.file_uploader("2. Forecast Nuevo (Prod. Terminado)", type=["csv", "xlsx"], key=f"file_nuevo{key_suffix}")
        with col3:
            file_bom = st.file_uploader("3. Estructura BOM (Componentes)", type=["csv", "xlsx"], key=f"file_bom{key_suffix}")

        if file_ant and file_nuevo and file_bom:
            df_fc_ant = pd.read_csv(file_ant) if file_ant.name.endswith('.csv') else pd.read_excel(file_ant)
            df_fc_nuevo = pd.read_csv(file_nuevo) if file_nuevo.name.endswith('.csv') else pd.read_excel(file_nuevo)
            df_bom = pd.read_csv(file_bom) if file_bom.name.endswith('.csv') else pd.read_excel(file_bom)

            df_fc_ant.columns = [str(c).strip() for c in df_fc_ant.columns]
            df_fc_nuevo.columns = [str(c).strip() for c in df_fc_nuevo.columns]
            df_bom.columns = [str(c).strip() for c in df_bom.columns]

            if st.button("🚀 Correr Análisis", type="primary", use_container_width=True):
                st.session_state.analizar = True
        else:
            st.warning("Por favor sube los tres ficheros requeridos para proceder.")
            st.session_state.analizar = False
            return

    if st.session_state.analizar:
        try:
            col_material_candidates = [c for c in df_bom.columns if any(p in c.lower() for p in ["componente", "material", "part", "insumo"])]
            col_material = col_material_candidates[0] if col_material_candidates else df_bom.columns[1] if len(df_bom.columns) > 1 else df_bom.columns[0]

            col_cant_candidates = [c for c in df_bom.columns if any(p in c.lower() for p in ["cant", "qty", "factor", "requerida", "uso"])]
            col_cant_bom = col_cant_candidates[0] if col_cant_candidates else df_bom.columns[2] if len(df_bom.columns) > 2 else df_bom.columns[0]

            col_prod_candidates = [c for c in df_bom.columns if any(p in c.lower() for p in ["prod", "term", "sku", "padre"])]
            col_prod_bom = col_prod_candidates[0] if col_prod_candidates else df_bom.columns[0]

            df_bom_clean = df_bom.copy()
            df_bom_clean.rename(columns={col_material: "Material", col_cant_bom: "Cantidad_BOM", col_prod_bom: "Producto"}, inplace=True)

            palabras_mes = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "-", "/", "2024", "2025", "2026"]

            col_meses_ant_detectados = [c for c in df_fc_ant.columns if any(m in str(c).lower() for m in palabras_mes) and not any(p in str(c).lower() for p in ["prod", "sku", "articulo", "artículo", "desc", "name", "nombre", "id"])]
            col_meses_nue_detectados = [c for c in df_fc_nuevo.columns if any(m in str(c).lower() for m in palabras_mes) and not any(p in str(c).lower() for p in ["prod", "sku", "articulo", "artículo", "desc", "name", "nombre", "id"])]

            meses_comunes = sorted(list(set(col_meses_ant_detectados).intersection(set(col_meses_nue_detectados))))

            col_meses_filtrados = meses_comunes
            if meses_comunes:
                st.sidebar.markdown("---")
                st.sidebar.header("📅 Selección Temporal")
                col_meses_filtrados = st.sidebar.multiselect(
                    "Meses/Bloques a evaluar:",
                    options=meses_comunes,
                    default=meses_comunes,
                    help="Selecciona de forma dinámica el rango o bloques de meses que deseas incluir en el cálculo de demanda."
                )
                if not col_meses_filtrados:
                    st.warning("⚠️ Por favor, selecciona al menos un mes en la barra lateral para realizar los cálculos.")
                    return

            col_prod_ant_candidates = [c for c in df_fc_ant.columns if any(p in str(c).lower() for p in ["prod", "sku", "material", "articulo", "artículo", "desc", "código", "codigo"])]
            col_prod_ant = col_prod_ant_candidates[0] if col_prod_ant_candidates else df_fc_ant.columns[0]

            col_prod_nue_candidates = [c for c in df_fc_nuevo.columns if any(p in str(c).lower() for p in ["prod", "sku", "material", "articulo", "artículo", "desc", "código", "codigo"])]
            col_prod_nue = col_prod_nue_candidates[0] if col_prod_nue_candidates else df_fc_nuevo.columns[0]

            df_fc_ant_clean = df_fc_ant.copy().rename(columns={col_prod_ant: "Producto"})
            df_fc_nuevo_clean = df_fc_nuevo.copy().rename(columns={col_prod_nue: "Producto"})

            if col_meses_filtrados:
                for col in col_meses_filtrados:
                    df_fc_ant_clean[col] = pd.to_numeric(df_fc_ant_clean[col], errors="coerce").fillna(0)
                df_fc_ant_clean["Demanda_Ant"] = df_fc_ant_clean[col_meses_filtrados].sum(axis=1)
            else:
                col_dem_ant_cand = [c for c in df_fc_ant_clean.columns if any(p in str(c).lower() for p in ["demanda", "cant", "vol", "total", "suma"])]
                col_dem_ant = col_dem_ant_cand[0] if col_dem_ant_cand else df_fc_ant_clean.columns[1] if len(df_fc_ant_clean.columns) > 1 else df_fc_ant_clean.columns[0]
                df_fc_ant_clean["Demanda_Ant"] = pd.to_numeric(df_fc_ant_clean[col_dem_ant], errors="coerce").fillna(0)

            if col_meses_filtrados:
                for col in col_meses_filtrados:
                    df_fc_nuevo_clean[col] = pd.to_numeric(df_fc_nuevo_clean[col], errors="coerce").fillna(0)
                df_fc_nuevo_clean["Demanda_Nueva"] = df_fc_nuevo_clean[col_meses_filtrados].sum(axis=1)
            else:
                col_dem_nue_cand = [c for c in df_fc_nuevo_clean.columns if any(p in str(c).lower() for p in ["demanda", "cant", "vol", "total", "suma"])]
                col_dem_nue = col_dem_nue_cand[0] if col_dem_nue_cand else df_fc_nuevo_clean.columns[1] if len(df_fc_nuevo_clean.columns) > 1 else df_fc_nuevo_clean.columns[0]
                df_fc_nuevo_clean["Demanda_Nueva"] = pd.to_numeric(df_fc_nuevo_clean[col_dem_nue], errors="coerce").fillna(0)

            merged_ant = pd.merge(df_bom_clean, df_fc_ant_clean[["Producto", "Demanda_Ant"]], on="Producto", how="inner")
            merged_ant["Demanda_Comp_Ant"] = merged_ant["Demanda_Ant"] * merged_ant["Cantidad_BOM"]

            merged_nuevo = pd.merge(df_bom_clean, df_fc_nuevo_clean[["Producto", "Demanda_Nueva"]], on="Producto", how="inner")
            merged_nuevo["Demanda_Comp_Nueva"] = merged_nuevo["Demanda_Nueva"] * merged_nuevo["Cantidad_BOM"]

            if merged_ant.empty and merged_nuevo.empty:
                st.error("⚠️ No se encontraron coincidencias de Productos entre tu archivo de BOM y los Forecasts. Por favor, verifica que los códigos de producto coincidan exactamente en ambos archivos.")
                return

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
            totales_unicos["Impacto"] = totales_unicos.apply(lambda r: "🔴 Incremento Crítico" if r["Var_Abs_Total" ] > 0 and r["Variación % Total"] >= umbral_subida else ("🔵 Disminución Crítica" if r["Var_Abs_Total"] < 0 and r["Variación % Total"] <= umbral_bajada else "🟢 Estable"), axis=1)

            totales = totales_unicos["Impacto"].value_counts()
            m1, m2, m3 = st.columns(3)
            m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
            m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
            m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

            st.write("### 🔍 Desglose de Componentes Explosionados y su Influencia por Producto")

            filtro_impacto = st.multiselect(
                "Filtrar por categoría de Impacto:",
                options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
                default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"]
            )

            df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

            df_presentacion = df_filtrado.rename(columns={                "Demanda_Comp_Ant": "Demanda Requerida Ant (Prod)",
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

if __name__ == '__main__':
    main()