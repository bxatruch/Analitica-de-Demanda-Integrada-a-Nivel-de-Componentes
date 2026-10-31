import datetime
import re
import unicodedata
import urllib.request

import numpy as np
import pandas as pd
import streamlit as st


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
    # Normaliza texto para comparar encabezados.
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    return texto


def buscar_columna(df, palabras, descripcion):
    # Busca una columna por palabras clave.
    if df is None or len(df.columns) == 0:
        raise ValueError(
            f"El archivo no contiene columnas para identificar "
            f"'{descripcion}'."
        )

    palabras = [normalizar_texto(p) for p in palabras]

    for columna in df.columns:
        nombre = normalizar_texto(columna)

        if any(palabra in nombre for palabra in palabras):
            return columna

    columnas = ", ".join(str(c) for c in df.columns)

    raise ValueError(
        f"No se encontró la columna '{descripcion}'. "
        f"Encabezados encontrados: {columnas}"
    )


def leer_archivo(archivo):
    # Lee archivos CSV o Excel.
    nombre = archivo.name.lower()

    if nombre.endswith(".csv"):
        return pd.read_csv(archivo)

    if nombre.endswith((".xlsx", ".xls")):
        return pd.read_excel(archivo)

    raise ValueError(
        f"Formato no soportado: {archivo.name}"
    )


# ============================================================
# DETECCIÓN DE COLUMNAS MENSUALES
# ============================================================

MESES = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]


def es_columna_mes(columna):
    # Detecta encabezados mensuales de Excel
    if isinstance(
        columna,
        (datetime.datetime, datetime.date, pd.Timestamp, np.datetime64)
    ):
        return True

    texto = normalizar_texto(columna)

    if any(mes in texto for mes in MESES):
        return True

    if re.fullmatch(r"\d{4}[-/]\d{1,2}", texto):
        return True

    if re.fullmatch(r"\d{1,2}[-/]\d{4}", texto):
        return True

    if re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", texto):
        return True

    if re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", texto):
        return True

    return False


# ============================================================
# PREPARACIÓN DE FORECASTS
# ============================================================

def obtener_demanda(df, nombre_demanda, meses_seleccionados=None):
    # Consolida las columnas mensuales o utiliza una columna total.
    df = df.copy()

    if df.empty or len(df.columns) == 0:
        raise ValueError("El Forecast está vacío o no tiene encabezados.")

    col_producto = buscar_columna(
        df,
        ["producto", "prod", "item", "codigo", "código"],
        "Producto"
    )

    columnas_meses = [
        columna
        for columna in df.columns
        if columna != col_producto and es_columna_mes(columna)
    ]

    if columnas_meses:
        if meses_seleccionados is not None:
            columnas_filtradas = [col for col in columnas_meses if col in meses_seleccionados]
            if columnas_filtradas:
                columnas_meses = columnas_filtradas

        valores = df[columnas_meses].apply(
            pd.to_numeric,
            errors="coerce"
        ).fillna(0)

        df[nombre_demanda] = valores.sum(axis=1)

    else:

        col_demanda = buscar_columna(
            df,
            [
                "demanda",
                "cantidad",
                "cant",
                "volumen",
                "vol",
                "total",
                "qty"
            ],
            "Demanda o Cantidad"
        )

        df[nombre_demanda] = pd.to_numeric(
            df[col_demanda],
            errors="coerce"
        ).fillna(0)

    df.rename(
        columns={col_producto: "Producto"},
        inplace=True
    )

    df["Producto"] = (
        df["Producto"]
        .astype("string")
        .str.strip()
    )

    df = df.dropna(subset=["Producto"])

    return df[["Producto", nombre_demanda]]


# ============================================================
# PREPARACIÓN DE BOM
# ============================================================

def preparar_bom(df):
    # Estandariza las columnas de la estructura BOM.
    df = df.copy()

    if df.empty or len(df.columns) == 0:
        raise ValueError("La BOM está vacía o no tiene encabezados.")

    col_producto = buscar_columna(
        df,
        ["producto", "prod", "parent", "padre"],
        "Producto terminado"
    )

    col_material = buscar_columna(
        df,
        [
            "material",
            "componente",
            "part_number",
            "part number",
            "comp"
        ],
        "Material o Componente"
    )

    col_cantidad = buscar_columna(
        df,
        [
            "cantidad requerida",
            "cantidad",
            "cant",
            "qty",
            "factor",
            "uso"
        ],
        "Cantidad requerida"
    )

    if len({
        col_producto,
        col_material,
        col_cantidad
    }) != 3:
        raise ValueError(
            "La BOM debe tener columnas diferentes para Producto, "
            "Material/Componente y Cantidad requerida."
        )

    df = df.rename(
        columns={
            col_producto: "Producto",
            col_material: "Material",
            col_cantidad: "Cantidad_BOM"
        }
    )

    for columna in ["Producto", "Material"]:
        df[columna] = (
            df[columna]
            .astype("string")
            .str.strip()
        )

    df["Cantidad_BOM"] = pd.to_numeric(
        df["Cantidad_BOM"],
        errors="coerce"
    )

    df["Cantidad_BOM"] = df["Cantidad_BOM"].fillna(0)

    df = df.dropna(subset=["Producto", "Material"])

    return df[
        ["Producto", "Material", "Cantidad_BOM"]
    ]


# ============================================================
# CÁLCULOS
# ============================================================

def calcular_porcentaje_variacion(anterior, nuevo):
    anterior = pd.to_numeric(
        anterior,
        errors="coerce"
    ).fillna(0)

    nuevo = pd.to_numeric(
        nuevo,
        errors="coerce"
    ).fillna(0)

    resultado = np.where(
        anterior != 0,
        ((nuevo - anterior) / anterior) * 100,
        np.where(nuevo != 0, 100, 0)
    )

    return pd.Series(
        resultado,
        index=anterior.index
    )


def categorizar(var, umbral_subida, umbral_bajada):
    if var >= umbral_subida:
        return "🔴 Incremento Crítico"
    if var <= umbral_bajada:
        return "🔵 Disminución Crítica"
    return "🟢 Estable"


# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================

def main():
    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader(
        "Sube tus Forecasts mensuales y tu BOM "
        "para analizar variaciones consolidadas"
    )

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

    # Dropdown de selección de bloques/meses
    st.sidebar.markdown("---")
    st.sidebar.header("📅 Filtro de Bloques / Meses")
    
    meses_disponibles = [
        "01-ene", "01-feb", "01-mar", "01-abr", "01-may", "01-jun",
        "01-jul", "01-ago", "01-sep", "01-oct", "01-nov", "01-dic"
    ]
    
    bloques_seleccionados = st.sidebar.multiselect(
        "Selecciona los meses para el comparativo:",
        options=meses_disponibles,
        default=["01-ene", "01-feb"]
    )

    st.sidebar.markdown("---")
    st.sidebar.header("📥 Descarga de Plantillas")
    st.sidebar.write("Descarga los formatos para preparar tus datos:")

    # URLs de las plantillas en GitHub
    base_github_url = "https://raw.githubusercontent.com/tony-vargas/mi-reto/main/assets/"
    
    templates = {
        "Plantilla BOM": "plantilla_bom.xlsx",
        "Plantilla Forecast": "plantilla_forecast.xlsx",
        "Plantilla Lead Time": "plantilla_lead_time.xlsx"
    }

    for label, filename in templates.items():
        try:
            url = base_github_url + filename
            with urllib.request.urlopen(url) as response:
                file_data = response.read()
            st.sidebar.download_button(
                label=f"⬇️ {label}",
                data=file_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.sidebar.warning(f"No se pudo cargar {filename}")

    st.write("### 📂 Carga de Archivos de Planificación")

    use_demo = st.checkbox(
        "Usar datos simulados de demostración (BOM + Forecasts)",
        value=False
    )

    if use_demo:
        df_fc_ant = pd.DataFrame({
            "Producto": [
                "Producto A",
                "Producto B",
                "Producto C"
            ],
            "01-ene": [1000, 500, 300],
            "01-feb": [1100, 400, 350]
        })

        df_fc_nuevo = pd.DataFrame({
            "Producto": [
                "Producto A",
                "Producto B",
                "Producto C"
            ],
            "01-ene": [1200, 300, 300],
            "01-feb": [1500, 200, 400]
        })

        df_bom = pd.DataFrame({
            "Producto": [
                "Producto A",
                "Producto A",
                "Producto B",
                "Producto C"
            ],
            "Componente": [
                "Componente A",
                "Componente B",
                "Componente A",
                "Componente C"
            ],
            "Cantidad requerida": [5, 2, 3, 4]
        })
        st.success("Cargados datos de demostración.")

    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            file_ant = st.file_uploader(
                "1. Forecast Anterior (Prod. Terminado)",
                type=["csv", "xlsx", "xls"],
                key="forecast_anterior"
            )
        with col2:
            file_nuevo = st.file_uploader(
                "2. Forecast Nuevo (Prod. Terminado)",
                type=["csv", "xlsx", "xls"],
                key="forecast_nuevo"
            )
        with col3:
            file_bom = st.file_uploader(
                "3. Estructura BOM (Componentes)",
                type=["csv", "xlsx", "xls"],
                key="bom"
            )

        if not (file_ant and file_nuevo and file_bom):
            st.info("Por favor, sube los tres archivos requeridos o descarga las plantillas de la barra lateral.")
            return

        try:
            df_fc_ant = leer_archivo(file_ant)
            df_fc_nuevo = leer_archivo(file_nuevo)
            df_bom = leer_archivo(file_bom)
            st.success("¡Archivos cargados con éxito!")
        except Exception as e:
            st.error(f"Error al leer los archivos: {e}")
            return

    try:
        df_bom_clean = preparar_bom(df_bom)

        df_fc_ant_clean = obtener_demanda(
            df_fc_ant,
            "Demanda_Ant",
            meses_seleccionados=bloques_seleccionados
        )

        df_fc_nuevo_clean = obtener_demanda(
            df_fc_nuevo,
            "Demanda_Nueva",
            meses_seleccionados=bloques_seleccionados
        )

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

        dtl_ant = merged_ant.groupby(
            ["Material", "Producto"],
            as_index=False
        )["Demanda_Comp_Ant"].sum()

        dtl_nuevo = merged_nuevo.groupby(
            ["Material", "Producto"],
            as_index=False
        )["Demanda_Comp_Nueva"].sum()

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

        tot_ant = merged_ant.groupby(
            "Material",
            as_index=False
        )["Demanda_Comp_Ant"].sum()

        tot_nuevo = merged_nuevo.groupby(
            "Material",
            as_index=False
        )["Demanda_Comp_Nueva"].sum()

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

        merged_tot["Variación % Total"] = (
            calcular_porcentaje_variacion(
                merged_tot["Demanda_Comp_Ant"],
                merged_tot["Demanda_Comp_Nueva"]
            )
        )

        final_df = pd.merge(
            merged_dtl,
            merged_tot[
                [
                    "Material",
                    "Var_Abs_Total",
                    "Variación % Total"
                ]
            ],
            on="Material",
            how="left"
        )

        final_df["% Influencia en Variación"] = np.where(
            final_df["Var_Abs_Total"] != 0,
            (
                final_df["Var_Abs_Prod"]
                / final_df["Var_Abs_Total"]
            ) * 100,
            0.0
        )

        final_df["Impacto Componente"] = (
            final_df["Variación % Total"].apply(
                lambda var: categorizar(
                    var,
                    umbral_subida,
                    umbral_bajada
                )
            )
        )

        st.write("### 📈 Resumen de Impacto Global de Componentes")

        merged_tot["Impacto"] = (
            merged_tot["Variación % Total"].apply(
                lambda var: categorizar(
                    var,
                    umbral_subida,
                    umbral_bajada
                )
            )
        )

        totales = merged_tot["Impacto"].value_counts()

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Incrementos Críticos (Alerta Roja)",
            totales.get("🔴 Incremento Crítico", 0)
        )
        m2.metric(
            "Disminuciones Críticas (Alerta Azul)",
            totales.get("🔵 Disminución Crítica", 0)
        )
        m3.metric(
            "Materiales Estables",
            totales.get("🟢 Estable", 0)
        )

        st.write(
            "### 🔍 Desglose de Componentes Explosionados "
            "y su Influencia por Producto"
        )

        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=[
                "🔴 Incremento Crítico",
                "🔵 Disminución Crítica",
                "🟢 Estable"
            ],
            default=[
                "🔴 Incremento Crítico",
                "🔵 Disminución Crítica",
                "🟢 Estable"
            ]
        )

        df_filtrado = final_df[
            final_df["Impacto Componente"].isin(filtro_impacto)
        ].sort_values(
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
        st.error(
            f"Ha ocurrido un error al procesar los archivos: {e}"
        )


if __name__ == "__main__":
    main()