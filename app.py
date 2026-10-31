import datetime
import os
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st

try:
    from google import genai
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai"])
    from google import genai

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Explosión y Comparador de Demanda",
    layout="wide"
)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def normalizar_texto(texto):
    """Normaliza texto para comparar encabezados sin acentos ni mayúsculas."""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    return texto

def buscar_columna(df, palabras, descripcion):
    """Busca una columna por palabras clave."""
    if df is None or len(df.columns) == 0:
        raise ValueError(f"El archivo no contiene columnas para identificar '{descripcion}'.")

    palabras = [normalizar_texto(p) for p in palabras]
    for columna in df.columns:
        nombre = normalizar_texto(columna)
        if any(palabra in nombre for palabra in palabras):
            return columna

    columnas = ", ".join(str(c) for c in df.columns)
    raise ValueError(f"No se encontró la columna '{descripcion}'. Encabezados encontrados: {columnas}")

def leer_archivo(archivo):
    """Lee archivos de datos de Excel o CSV."""
    nombre = archivo.name.lower()
    if nombre.endswith(".csv"):
        return pd.read_csv(archivo)
    if nombre.endswith(Tuple := (".xlsx", ".xls")):
        return pd.read_excel(archivo)
    raise ValueError(f"Formato no soportado: {archivo.name}")

# ============================================================
# DETECCIÓN DE COLUMNAS DE FECHAS / MESES
# ============================================================
M_ESES_LIST = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]

def es_columna_mes(columna):
    """Detecta si un encabezado corresponde a un periodo mensual."""
    if isinstance(columna, (datetime.datetime, datetime.date, pd.Timestamp, np.datetime64)):
        return True
    texto = normalizar_texto(columna)
    if any(mes in texto for mes in M_ESES_LIST):
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
# PROCESAMIENTO DE ARCHIVOS
# ============================================================
def obtener_demanda(df, nombre_demanda, meses_filtrados=None):
    """Consolida la demanda mensual o totaliza de acuerdo al formato del archivo y meses seleccionados."""
    df = df.copy()
    if df.empty or len(df.columns) == 0:
        raise ValueError("El Forecast está vacío o no tiene encabezados.")

    col_producto = buscar_columna(
        df,
        ["producto", "prod", "item", "codigo", "código"],
        "Producto"
    )

    # Identificar todas las columnas que corresponden a meses
    columnas_meses_detectadas = [
        columna for columna in df.columns
        if columna != col_producto and es_columna_mes(columna)
    ]

    if columnas_meses_detectadas:
        # Si el usuario seleccionó un subconjunto de meses específicos, filtramos por ellos
        if meses_filtrados is not None:
            columnas_a_sumar = [c for c in columnas_meses_detectadas if c in meses_filtrados]
            if not columnas_a_sumar:
                # Si por alguna razón la intersección es vacía, sumamos cero para evitar errores
                df[nombre_demanda] = 0.0
                df.rename(columns={col_producto: "Producto"}, inplace=True)
                df["Producto"] = df["Producto"].astype("string").str.strip()
                return df[["Producto", nombre_demanda]]
        else:
            columnas_a_sumar = columnas_meses_detectadas

        valores = df[columnas_a_sumar].apply(pd.to_numeric, errors="coerce").fillna(0)
        df[nombre_demanda] = valores.sum(axis=1)
    else:
        col_demanda = buscar_columna(
            df,
            ["demanda", "cantidad", "cant", "volumen", "vol", "total", "qty"],
            "Demanda o Cantidad"
        )
        df[nombre_demanda] = pd.to_numeric(df[col_demanda], errors="coerce").fillna(0)

    df.rename(columns={col_producto: "Producto"}, inplace=True)
    df["Producto"] = df["Producto"].astype("string").str.strip()
    df = df.dropna(subset=["Producto"])
    return df[["Producto", nombre_demanda]]

def preparar_bom(df):
    """Limpia y estandariza la estructura del Árbol de Materiales (BOM)."""
    df = df.copy()
    if df.empty or len(df.columns) == 0:
        raise ValueError("La BOM está vacía o no tiene encabezados.")

    col_producto = buscar_columna(df, ["producto", "prod", "parent", "padre"], "Producto terminado")
    col_material = buscar_columna(df, ["material", "componente", "part_number", "part number", "comp"], "Material o Componente")
    col_cantidad = buscar_columna(df, ["cantidad requerida", "cantidad", "cant", "qty", "factor", "uso"], "Cantidad requerida")

    if len({col_producto, col_material, col_cantidad}) != 3:
        raise ValueError("La BOM debe tener columnas distintas para Producto, Componente y Cantidad.")

    df = df.rename(columns={
        col_producto: "Producto",
        col_material: "Material",
        col_cantidad: "Cantidad_BOM"
    })

    for col in ["Producto", "Material"]:
        df[col] = df[col].astype("string").str.strip()

    df["Cantidad_BOM"] = pd.to_numeric(df["Cantidad_BOM"], errors="coerce").fillna(0)
    df = df.dropna(subset=["Producto", "Material"])
    return df[["Producto", "Material", "Cantidad_BOM"]]

def calcular_porcentaje_variacion(anterior, nuevo):
    """Calcula la variación de forma segura evitando división por cero."""
    anterior = pd.to_numeric(anterior, errors="coerce").fillna(0)
    nuevo = pd.to_numeric(nuevo, errors="coerce").fillna(0)
    return np.where(
        anterior != 0,
        ((nuevo - anterior) / anterior) * 100,
        np.where(nuevo != 0, 100.0, 0.0)
    )

def categorizar(var, umbral_subida, umbral_bajada):
    if var >= umbral_subida:
        return "🔴 Incremento Crítico"
    if var <= umbral_bajada:
        return "🔵 Disminución Crítica"
    return "🟢 Estable"

# ============================================================
# INTERFAZ Y LÓGICA PRINCIPAL
# ============================================================
def main():
    st.title("📊 Explosión y Comparador de Demandas con BOM")
    st.subheader("Sube tus Forecasts mensuales y tu BOM para analizar variaciones consolidadas")

    st.sidebar.header("⚙️ Configuración de Alertas")
    umbral_subida = st.sidebar.slider("Umbral de Incremento Crítico (%)", 10, 200, 30, 5)
    umbral_bajada = st.sidebar.slider("Umbral de Disminución Crítica (%)", -200, -10, -30, 5)

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
            st.info("Por favor, carga los tres archivos requeridos para iniciar el cálculo de la explosión.")
            return

        try:
            df_fc_ant = leer_archivo(file_ant)
            df_fc_nuevo = leer_archivo(file_nuevo)
            df_bom = leer_archivo(file_bom)
            st.success("¡Archivos cargados con éxito!")
        except Exception as e:
            st.error(f"Error al leer los archivos: {e}")
            return

    # --- FILTRO LATERAL DE BLOQUES DE MESES ---
    # Detectar dinámicamente qué columnas son meses
    col_producto_ant = buscar_columna(df_fc_ant, ["producto", "prod", "item", "codigo", "código"], "Producto")
    columnas_meses_detectadas = [
        columna for columna in df_fc_ant.columns
        if columna != col_producto_ant and es_columna_mes(columna)
    ]

    meses_seleccionados = None
    if columnas_meses_detectadas:
        st.sidebar.markdown("--- ")
        st.sidebar.header("📅 Filtro de Periodos")
        meses_seleccionados = st.sidebar.multiselect(
            "Selecciona los meses a visualizar en el análisis:",
            options=columnas_meses_detectadas,
            default=columnas_meses_detectadas
        )
        if not meses_seleccionados:
            st.warning("⚠️ Por favor selecciona al menos un mes en el menú lateral para realizar el cálculo.")
            return

    try:
        df_bom_clean = preparar_bom(df_bom)
        df_fc_ant_clean = obtener_demanda(df_fc_ant, "Demanda_Ant", meses_seleccionados)
        df_fc_nuevo_clean = obtener_demanda(df_fc_nuevo, "Demanda_Nueva", meses_seleccionados)

        # Explosión Anterior
        merged_ant = pd.merge(df_bom_clean, df_fc_ant_clean, on="Producto", how="inner")
        merged_ant["Demanda_Comp_Ant"] = merged_ant["Demanda_Ant"] * merged_ant["Cantidad_BOM"]

        # Explosión Nueva
        merged_nuevo = pd.merge(df_bom_clean, df_fc_nuevo_clean, on="Producto", how="inner")
        merged_nuevo["Demanda_Comp_Nueva"] = merged_nuevo["Demanda_Nueva"] * merged_nuevo["Cantidad_BOM"]

        if merged_ant.empty and merged_nuevo.empty:
            st.warning("No se encontraron coincidencias de códigos entre los Forecasts y la BOM.")
            return

        # Detalles por componente y producto parent
        dtl_ant = merged_ant.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Ant"].sum()
        dtl_nuevo = merged_nuevo.groupby(["Material", "Producto"], as_index=False)["Demanda_Comp_Nueva"].sum()
        merged_dtl = pd.merge(dtl_ant, dtl_nuevo, on=["Material", "Producto"], how="outer").fillna(0)
        merged_dtl["Var_Abs_Prod"] = merged_dtl["Demanda_Comp_Nueva"] - merged_dtl["Demanda_Comp_Ant"]

        # Totales consolidados por material
        tot_ant = merged_ant.groupby("Material", as_index=False)["Demanda_Comp_Ant"].sum()
        tot_nuevo = merged_nuevo.groupby("Material", as_index=False)["Demanda_Comp_Nueva"].sum()
        merged_tot = pd.merge(tot_ant, tot_nuevo, on="Material", how="outer").fillna(0)
        merged_tot["Var_Abs_Total"] = merged_tot["Demanda_Comp_Nueva"] - merged_tot["Demanda_Comp_Ant"]
        merged_tot["Variación % Total"] = calcular_porcentaje_variacion(merged_tot["Demanda_Comp_Ant"], merged_tot["Demanda_Comp_Nueva"])

        # Combinación final
        final_df = pd.merge(merged_dtl, merged_tot[["Material", "Var_Abs_Total", "Variación % Total"]], on="Material", how="left")
        final_df["% Influencia en Variación"] = np.where(
            final_df["Var_Abs_Total"] != 0,
            (final_df["Var_Abs_Prod" ] / final_df["Var_Abs_Total"]) * 100,
            0.0
        )
        final_df["Impacto Componente"] = final_df["Variación % Total"].apply(lambda x: categorizar(x, umbral_subida, umbral_bajada))

        # Resumen visual métricas
        st.write("### 📈 Resumen de Impacto Global de Componentes")
        merged_tot["Impacto"] = merged_tot["Variación % Total"].apply(lambda x: categorizar(x, umbral_subida, umbral_bajada))
        totales = merged_tot["Impacto"].value_counts()

        m1, m2, m3 = st.columns(3)
        m1.metric("Incrementos Críticos (Alerta Roja)", totales.get("🔴 Incremento Crítico", 0))
        m2.metric("Disminuciones Críticas (Alerta Azul)", totales.get("🔵 Disminución Crítica", 0))
        m3.metric("Materiales Estables", totales.get("🟢 Estable", 0))

        # Visualización de datos
        st.write("### 🔍 Desglose de Componentes Explosionados y su Influencia por Producto")
        filtro_impacto = st.multiselect(
            "Filtrar por categoría de Impacto:",
            options=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"],
            default=["🔴 Incremento Crítico", "🔵 Disminución Crítica", "🟢 Estable"]
        )

        df_filtrado = final_df[final_df["Impacto Componente"].isin(filtro_impacto)].sort_values(by=["Material", "Var_Abs_Prod"], ascending=[True, False])

        st.dataframe(
            df_filtrado.rename(columns={
                "Demanda_Comp_Ant": "Demanda Requerida Ant (Prod)",
                "Demanda_Comp_Nueva": "Demanda Requerida Nueva (Prod)",
                "Var_Abs_Prod": "Variación Requerida (Abs)",
                "Var_Abs_Total": "Variación Total Componente",
                "Variación % Total": "Variación % Total Componente",
                "Impacto Componente": "Impacto del Componente"
            }).style.format({
                "Demanda Requerida Ant (Prod)": "{:.0f}",
                "Demanda Requerida Nueva (Prod)": "{:.0f}",
                "Variación Requerida (Abs)": "{:+,.0f}",
                "Variación Total Componente": "{:+,.0f}",
                "Variación % Total Componente": "{:+,.1f}%",
                "% Influencia en Variación": "{:+,.1f}%"
            }),
            use_container_width=True
        )

        # ============================================================
        # CHAT BOT INTEGRADO CON GEMINI AI
        # ============================================================
        st.markdown("--- ")
        st.subheader("💬 Consulta Inteligente con Gemini AI")

        # Validación unificada de la API Key en Streamlit y Colab
        gemini_api_key = ""
        if "GEMINI_API_KEY" in st.secrets:
            gemini_api_key = st.secrets["GEMINI_API_KEY"]
        elif os.getenv("GEMINI_API_KEY"):
            gemini_api_key = os.getenv("GEMINI_API_KEY")
        else:
            try:
                from google.colab import userdata
                gemini_api_key = userdata.get("GEMINI_API_KEY")
            except Exception:
                pass

        if not gemini_api_key:
            st.warning("⚠️ No se encontró la clave de API 'GEMINI_API_KEY' en la configuración de secretos o variables de entorno.")
        else:
            try:
                client = genai.Client(api_key=gemini_api_key)
                if "chat_history" not in st.session_state:
                    st.session_state["chat_history"] = []

                for chat in st.session_state["chat_history"]:
                    with st.chat_message(chat["role"]):
                        st.write(chat["text"])

                if prompt := st.chat_input("Escribe tu pregunta sobre los resultados de materiales aquí..."):
                    st.session_state["chat_history"].append({"role": "user", "text": prompt})
                    with st.chat_message("user"):
                        st.write(prompt)

                    resumen_materiales = merged_tot.to_string(index=False)
                    contexto_completo = (
                        f"Actúas como un experto Planner de compras de producción.\n"
                        f"Aquí tienes el resultado de la explosión de materiales y su variación de demanda:\n"
                        f"{resumen_materiales}\n\n"
                        f"Responde de forma concisa, profesional y en español a la siguiente pregunta: {prompt}"
                    )

                    with st.chat_message("assistant"):
                        with st.spinner("Pensando..."):
                            response = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=contexto_completo,
                            )
                            st.write(response.text)
                            st.session_state["chat_history"].append({"role": "assistant", "text": response.text})
            except Exception as gem_error:
                st.error(f"Error en el asistente virtual de Gemini: {gem_error}")

    except Exception as e:
        st.error(f"Error durante el procesamiento: {e}")

if __name__ == "__main__":
    main()