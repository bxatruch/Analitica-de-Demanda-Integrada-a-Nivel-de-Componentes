import streamlit as st
import pandas as pd
import numpy as np
import datetime
import unicodedata

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Explosión y Comparador de Demanda",
    layout="wide"
)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(texto):
    # Normaliza encabezados para comparar nombres sin acentos.
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return texto

def buscar_columna(df, palabras, descripcion):
    # Busca una columna por palabras clave y devuelve su nombre original.
    for columna in df.columns:
        nombre = normalizar_texto(columna)
        if any(palabra in nombre for palabra in palabras):
            return columna
    raise ValueError(
        f"No se encontró la columna '{descripcion}'. "
        f"Columnas disponibles: {list(df.columns)}"
    )

def leer_archivo(archivo):
    # Lee archivos CSV o Excel.
    nombre = archivo.name.lower()
    if nombre.endswith(".csv"):
        return pd.read_csv(archivo)
    if nombre.endswith((".xlsx", ".xls")):
        return pd.read_excel(archivo)
    raise ValueError(
        f"Formato no soportado: {archivo.name}. "
        "Utiliza archivos CSV o Excel."
    )

def es_columna_mes(columna):
    # Identifica columnas mensuales tanto si el encabezado es una fecha real de Excel como si es texto, por ejemplo '01-ene' o 'enero'.
    if isinstance(
        columna,
        (datetime.datetime, datetime.date, pd.Timestamp, np.datetime64)
    ):
        return True

    texto = normalizar_texto(columna)
    palabras_mes = [
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec"
    ]

    # También reconoce encabezados como 2026-01 o 01/2026.
    fecha = pd.to_datetime(texto, errors="coerce")
    if not pd.isna(fecha):
        return True

    return any(mes in texto for mes in palabras_mes)

def obtener_demanda(df, nombre_demanda):
    # Identifica las columnas mensuales o una columna de demanda total. Devuelve una copia del DataFrame con Producto y la demanda calculada.
    df = df.copy()
    col_producto = buscar_columna(
        df,
        ["producto", "prod"],
        "Producto"
    )
    df.rename(
        columns={col_producto: "Producto"},
        inplace=True
    )

    # Identificar los meses sin modificar los nombres originales.
    columnas_meses = [
        columna for columna in df.columns
        if es_columna_mes(columna)
    ]

    if columnas_meses:
        # Convertir los valores mensuales a números.
        valores = df[columnas_meses].apply(
            pd.to_numeric,
            errors="coerce"
        ).fillna(0)
        df[nombre_demanda] = valores.sum(axis=1)
    else:
        # Si no hay columnas mensuales, buscar una columna de demanda total.
        columna_demanda = buscar_columna(
            df,
            ["demanda", "cantidad", "cant", "volumen", "vol"],
            "Demanda o Cantidad"
        )
        df[nombre_demanda] = pd.to_numeric(
            df[columna_demanda],
            errors="coerce"
        ).fillna(0)

    return df[["Producto", nombre_demanda]]

def preparar_bom(df):
    # Estandariza las columnas de la estructura BOM.
    df = df.copy()
    col_material = buscar_columna(
        df,
        ["material", "componente", "part_number", "part number"],
        "Material o Componente"
    )
    col_producto = buscar_columna(
        df,
        ["producto", "prod"],
        "Producto"
    )
    col_cantidad = buscar_columna(
        df,
        ["cantidad requerida", "cantidad", "cant", "qty", "factor"],
        "Cantidad requerida"
    )
    df.rename(
        columns={
            col_material: "Material",
            col_producto: "Producto",
            col_cantidad: "Cantidad_BOM"
        },
        inplace=True
    )

    df["Cantidad_BOM"] = pd.to_numeric(
        df["Cantidad_BOM"],
        errors="coerce"
    ).fillna(0)

    # Limpiar los identificadores para evitar diferencias por espacios.
    for columna in ["Material", "Producto"]:
        df[columna] = df[columna].astype("string").str.strip()

    df = df.dropna(subset=["Material", "Producto"])
    return df

def calcular_porcentaje_variacion(anterior, nuevo):
    # Calcula variación porcentual evitando divisiones por cero.
    anterior = pd.to_numeric(anterior, errors="coerce").fillna(0)
    nuevo = pd.to_numeric(nuevo, errors="coerce").fillna(0)
    variacion = nuevo - anterior

    resultado = np.where(
        anterior != 0,
        (variacion / anterior) * 100,
        np.where(nuevo != 0, np.inf, 0)
    )
    return pd.Series(resultado, index=anterior.index).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0)

# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================

def main():
    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales y tu BOM para analizar variaciones consolidadas")

    # Panel lateral para configurar umbrales de alerta
    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider(
        "Umbral de Incremento Crítico (%)",
        min_value=10,
        max_value=200,
        value=30,
        step=5
    )
    umbral_bajada = st.sidebar.slider(
        "Umbral de Disminución Crítica (%)",
        min_value=-200,
        max_value=-10,
        value=-30,
        step=5
    )

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
        st.success("Cargados datos de demostración.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            file_ant = st.file_uploader("1. Forecast Anterior (Prod. Terminado)", type=["csv", "xlsx", "xls"], key="forecast_anterior")
        with col2:
            file_nuevo = st.file_uploader("2. Forecast Nuevo (Prod. Terminado)", type=["csv", "xlsx", "xls"], key="forecast_nuevo")
        with col3:
            file_bom = st.file_uploader("3. Estructura BOM (Componentes)", type=["csv", "xlsx", "xls"], key="bom")

        if not (file_ant and file_nuevo and file_bom):
            st.info("Por favor, sube los tres archivos requeridos.")
            return

        try:
            df_fc_ant = leer_archivo(file_ant)
            df_fc_nuevo = leer_archivo(file_nuevo)
            df_bom = leer_archivo(file_bom)
            st.success("¡Archivos cargados con éxito!")
        except Exception as e:
            st.error(f"Error al leer los archivos: {e}")
            return

    # Procesamiento y Explosión
    try:
        # 1. Estandarizar la BOM.
        df_bom_clean = preparar_bom(df_bom)

        # 2. Identificar y consolidar la demanda de los Forecasts.
        df_fc_ant_clean = obtener_demanda(df_fc_ant, "Demanda_Ant")
        df_fc_nuevo_clean = obtener_demanda(df_fc_nuevo, "Demanda_Nueva")

        # 3. Explosión de demanda anterior.
        merged_ant = pd.merge(
            df_bom_clean,
            df_fc_ant_clean,
            on="Producto",
            how="inner"
        )
        merged_ant["Demanda_Comp_Ant"] = (
            merged_ant["Demanda_Ant"]
            * merged_ant["Cantidad_BOM"]
        )

        # 4. Explosión de demanda nueva.
        merged_nuevo = pd.merge(
            df_bom_clean,
            df_fc_nuevo_clean,
            on="Producto",
            how="inner"
        )
        merged_nuevo["Demanda_Comp_Nueva"] = (
            merged_nuevo["Demanda_Nueva"]
            * merged_nuevo["Cantidad_BOM"]
        )

        if merged_ant.empty and merged_nuevo.empty:
            st.warning(
                "No se encontraron coincidencias entre los productos "
                "de los Forecasts y los productos de la BOM."
            )
            return

        # Detalle por material y producto
        dtl_ant = merged_ant.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Ant"].sum()
        dtl_nuevo = merged_nuevo.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_dtl = pd.merge(
            dtl_ant,
            dtl_nuevo,
            on=["Material", "Producto"],
            how="outer"
        ).fillna(0)
        merged_dtl["Var_Abs_Prod"] = (
            merged_dtl["Demanda_Comp_Nueva"]
            - merged_dtl["Demanda_Comp_Ant"]
        )

        # Totales consolidados por material
        tot_ant = merged_ant.groupby("Material", as_index=False)["Demanda_Comp_Ant"].sum()
        tot_nuevo = merged_nuevo.groupby("Material", as_index=False)["Demanda_Comp_Nueva"].sum()

        merged_tot = pd.merge(
            tot_ant,
            tot_nuevo,
            on="Material",
            how="outer"
        ).fillna(0)
        merged_tot["Var_Abs_Total"] = (
            merged_tot["Demanda_Comp_Nueva"]
            - merged_tot["Demanda_Comp_Ant"]
        )
        merged_tot["Variación % Total"] = calcular_porcentaje_variacion(
            merged_tot["Demanda_Comp_Ant"],
            merged_tot["Demanda_Comp_Nueva"]
        )

        # Unir detalle y totales
        final_df = pd.merge(
            merged_dtl,
            merged_tot[["Material", "Var_Abs_Total", "Variación % Total"]],
            on="Material",
            how="left"
        )

        # Porcentaje de influencia
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
            return "🟢 Estable"

        final_df["Impacto Componente"] = final_df.apply(categorizar, axis=1)

        # Resumen de impacto global
        st.write("### 📈 Resumen de Impacto Global de Componentes")
        totales_unicos = merged_tot.copy()
        totales_unicos["Impacto"] = totales_unicos.apply(
            lambda r: (
                "🔴 Incremento Crítico"
                if (r["Var_Abs_Total"] > 0 and r["Variación % Total"] >= umbral_subida)
                else (
                    "🔵 Disminución Crítica"
                    if (r["Var_Abs_Total"] < 0 and r["Variación % Total"] <= umbral_bajada)
                    else "🟢 Estable"
                )
            ),
            axis=1
        )
        totales = totales_unicos["Impacto"].value_counts()

        m1, m2, m3 = st.columns(3)
        m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
        m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
        m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

        # Tabla detallada
        st.write("### 🔍 Desglose de Componentes Explosionados y su Influencia por Producto")
        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
            default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"]
        )

        df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(
            by=["Material", "Var_Abs_Prod"],
            ascending=[True, False]
        )

        df_presentacion = df_filtrado.rename(
            columns={ 
                "Demanda_Comp_Ant": "Demanda Requerida Ant (Prod)",
                "Demanda_Comp_Nueva": "Demanda Requerida Nueva (Prod)",
                "Var_Abs_Prod": "Variación Requerida (Abs)",
                "Var_Abs_Total": "Variación Total Componente",
                "Variación % Total": "Variación % Total Componente",
                "Impacto Componente": "Impacto del Componente"
            }
        )

        st.dataframe(
            df_presentacion.style.format({
                "Demanda Requerida Ant (Prod)": "{:,.0f}",
                "Demanda Requerida Nueva (Prod)": "{:,.0f}",
                "Variación Requerida (Abs)": "{:+,.0f}",
                "Variación Total Componente": "{:+,.0f}",
                "Variación % Total Componente": "{:+,.1f}%",
                "% Influencia en Variación": "{:+,.1f}%"
            }),
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Ha ocurrido un error al procesar los archivos: {e}")

if __name__ == "__main__":
    main()