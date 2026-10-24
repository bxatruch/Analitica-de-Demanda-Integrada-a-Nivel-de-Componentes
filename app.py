# -*- coding: utf-8 -*-
"""
Archivo de aplicación Streamlit auto-generado.
Contiene la funcionalidad de explosión de BOM, comparación de forecasts, sugerencias estratégicas y proyección estadística.
"""
import streamlit as st
import pandas as pd
import numpy as np
import io

try:
    import openpyxl
except ImportError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl"])

def main():
    st.set_page_config(page_title="Explosión y Comparador de Demanda", layout="wide")

    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales y tu BOM para analizar variaciones consolidadas")

    # Panel lateral para configurar umbrales de alerta
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", min_value=10, max_value=200, value=30, step=5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", min_value=-200, max_value=-10, value=-30, step=5)

    st.write("### 📂 Carga de Archivos de Planificación")
    use_demo = st.checkbox("Usar datos simulados de demostración (BOM + Forecasts + Histórico de Ventas)", value=False)

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
        df_historico_ventas = pd.DataFrame({
            "Producto": ["Producto A", "Producto B", "Producto C"],
            "Mes -3": [900, 450, 280],
            "Mes -2": [950, 480, 290],
            "Mes -1": [1100, 520, 310]
        })
        st.success("Cargados datos de demostración con estructura mensual e histórico de ventas.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            file_ant = st.file_uploader("1. Forecast Anterior (Prod. Terminado)", type=["csv", "xlsx"])
        with col2:
            file_nuevo = st.file_uploader("2. Forecast Nuevo (Prod. Terminado)", type=["csv", "xlsx"])
        with col3:
            file_bom = st.file_uploader("3. Estructura BOM (Componentes)", type=["csv", "xlsx"])
        with col4:
            file_historico = st.file_uploader("4. Histórico de Ventas Reales (Opcional)", type=["csv", "xlsx"])

        if file_ant and file_nuevo and file_bom:
            df_fc_ant = pd.read_csv(file_ant) if file_ant.name.endswith(".csv") else pd.read_excel(file_ant)
            df_fc_nuevo = pd.read_csv(file_nuevo) if file_nuevo.name.endswith(".csv") else pd.read_excel(file_nuevo)
            df_bom = pd.read_csv(file_bom) if file_bom.name.endswith(".csv") else pd.read_excel(file_bom)
            if file_historico:
                df_historico_ventas = pd.read_csv(file_historico) if file_historico.name.endswith(".csv") else pd.read_excel(file_historico)
            else:
                df_historico_ventas = None
        else:
            st.warning("Por favor sube los tres archivos requeridos (Forecast Anterior, Forecast Nuevo y BOM) para proceder.")
            return

    try:
        col_material = [c for c in df_bom.columns if any(p in c.lower() for p in ["material", "componente", "part_number"])][0]
        col_cant_bom = [c for c in df_bom.columns if any(p in c.lower() for p in ["cant", "qty", "factor", "requerida"])][0]

        df_bom_clean = df_bom.copy()
        df_bom_clean.rename(columns={col_material: "Material", col_cant_bom: "Cantidad_BOM"}, inplace=True)

        col_prod_bom = [c for c in df_bom_clean.columns if "prod" in c.lower()][0]
        df_bom_clean.rename(columns={col_prod_bom: "Producto"}, inplace=True)

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

        # --- SUGERENCIAS ---
        st.write("### 💡 Sugerencias Estratégicas (Optimización de MPS y Cobertura de Componentes)")
        materiales_criticos_up = totales_unicos[totales_unicos["Impacto"] == "🔴 Incremento Crítico"]["Material"].tolist()
        materiales_criticos_down = totales_unicos[totales_unicos["Impacto"] == "🔵 Disminución Crítica"]["Material"].tolist()

        col_sug1, col_col2 = st.columns(2)
        with col_sug1:
            st.markdown("#### 📦 Cobertura de Componentes e Inventario")
            if materiales_criticos_up:
                st.warning(f"⚠️ **Riesgo de Desabastecimiento:** Los siguientes componentes muestran incrementos críticos: **{', '.join(materiales_criticos_up)}**. Recomendamos:
- Aumentar temporalmente el stock de seguridad.
- Adelantar las órdenes de compra con proveedores con mayor Lead Time.")
            if materiales_criticos_down:
                st.info(f"📉 **Riesgo de Sobre-inventario:** Se detectó baja en la demanda para: **{', '.join(materiales_criticos_down)}**.
- Sugerimos posponer las órdenes abiertas o entregas en tránsito para evitar sobre-costos de almacenamiento.")
            if not materiales_criticos_up and not materiales_criticos_down:
                st.success("✅ Todos los componentes muestran comportamientos estables dentro de los rangos definidos.")

        with col_col2:
            st.markdown("#### ⚙️ Optimización del Plan Maestro (MPS)")
            productos_afectados = final_df[final_df["Impacto Componente"].isin(["🔴 Incremento Crítico", "🔵 Disminución Crítica"])]["Producto"].unique().tolist()
            if productos_afectados:
                st.markdown(f"**Acciones para el MPS sobre los productos ({', '.join(productos_afectados)}):**")
                st.markdown("1. **Suavizado de Carga:** Distribuir los picos de producción de los productos con incremento agresivo a lo largo de las semanas para evitar cuellos de botella en las líneas.")
                st.markdown("2. **Alineación de Capacidad:** Revisar los turnos de trabajo y disponibilidad de mano de obra para las familias afectadas por incrementos de volumen.")
            else:
                st.write("No se requieren modificaciones de capacidad inmediatas en el MPS actual.")

        # --- PROYECCIONES ---
        if df_historico_ventas is not None:
            st.write("### 🔮 Generador Automático de Proyecciones de Venta")
            st.write("Analiza estadísticamente el histórico de ventas reales para proyectar los próximos períodos.")
            
            num_periodos = st.number_input("Número de meses/períodos a proyectar:", min_value=1, max_value=12, value=3, step=1)
            
            if st.button("Generar Proyección Estadística"):
                col_prod_hist = [c for c in df_historico_ventas.columns if "prod" in c.lower()][0]
                df_hist_clean = df_historico_ventas.copy().rename(columns={col_prod_hist: "Producto"})
                cols_numericas = df_hist_clean.select_dtypes(include=[np.number]).columns.tolist()
                
                if len(cols_numericas) >= 2:
                    proyecciones = []
                    for idx, row in df_hist_clean.iterrows():
                        y = row[cols_numericas].values
                        x = np.arange(len(y))
                        slope, intercept = np.polyfit(x, y, 1)
                        
                        proy_row = {"Producto": row["Producto"]}
                        for p in range(1, num_periodos + 1):
                            val_proy = max(0, int(slope * (len(y) + p - 1) + intercept))
                            proy_row[f"Proyección Mes {p}"] = val_proy
                        proyecciones.append(proy_row)
                    
                    df_proy_final = pd.DataFrame(proyecciones)
                    st.success("✅ Proyección calculada mediante regresión lineal sobre el histórico de ventas.")
                    st.dataframe(df_proy_final)
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_proy_final.to_excel(writer, index=False, sheet_name='Proyecciones')
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Descargar Proyección en Excel",
                        data=processed_data,
                        file_name="proyeccion_ventas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("Se necesitan al menos 2 periodos históricos numéricos para realizar la regresión estadística.")
        else:
            st.info("💡 Sube un archivo de 'Histórico de Ventas Reales' para habilitar la sección de análisis y proyección estadística de demanda.")

    except Exception as e:
        st.error(f"Ha ocurrido un error al procesar y explosionar los archivos de demanda con la BOM: {e}")

if __name__ == '__main__':
    main()