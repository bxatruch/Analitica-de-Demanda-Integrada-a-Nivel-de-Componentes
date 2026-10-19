# Especificación · Explosión y Comparador de Demandas con BOM

> Una buena especificación es la que otro asistente de IA podría construir sin haceros preguntas. Rellenadla en la semana 2 y usadla como prompt principal con vuestro asistente o agente. De ella sale la ficha del **hito de la semana 2**.

## 1. Problema y usuario

- **Quién tiene el problema:** Analistas de Planificación de Demanda, Compradores de Materiales y Directores de Operaciones/Supply Chain en empresas manufactureras.
- **Cómo lo resuelve hoy:** Utilizando hojas de cálculo complejas de Excel mediante la combinación de fórmulas `VLOOKUP`/`BUSCARV` manuales y macros frágiles para relacionar el pronóstico de demanda de producto terminado con las listas de materiales (BOM).
- **Qué le molesta de cómo lo hace hoy:** El proceso toma mucho tiempo, es propenso a errores de referencia, las macros se rompen al cambiar la estructura de la base de datos, no se alinean fácilmente desfases temporales ni discrepancias menores de nomenclatura y requiere de un esfuerzo repetitivo cada mes para detectar variaciones.
- **Qué parte resuelve la IA:** El motor realiza la alineación automática de fechas (forecast vs real), gestiona de manera inteligente la asignación de sinónimos para encabezados con discrepancias menores de forma guiada por UI y procesa la explosión recursiva multinivel de la estructura de materiales de forma automatizada.

## 2. Qué hace el producto

1. **Explosor de BOM Recursivo:** Desglosa de forma recursiva y multinivel toda la estructura de materias primas y subensambles a partir de la demanda de producto terminado.
2. **Alineador Temporal Inteligente:** Une y empareja las series temporales de la demanda proyectada y el consumo real bajo un horizonte común (llenando vacíos con cero), manejando automáticamente rangos inconsistentes.
3. **Mapeo de Columnas Dinámico:** Permite seleccionar e identificar manualmente las columnas críticas mediante menús desplegables (`st.selectbox`) cuando el mapeo automático falla o detecta discrepancias de sinonimia.

## 3. Entradas y salidas

| El usuario da… | La app devuelve… | Ejemplo |
|---|---|---|
| Dos archivos CSV/XLSX (Previsión de Demanda y Datos Reales de Consumo) y un archivo CSV/XLSX con la estructura de la lista de materiales (BOM). | Un dashboard interactivo en Streamlit con métricas clave de variación, tablas de explosión detalladas y alertas visuales de componentes con mayor desviación. | Subir `BOM.xlsx` y demandas, y obtener un análisis donde el componente 'Tornillo M6' muestra una variación del +100% de uso imprevisto por ser un componente nuevo. |

## 4. La pieza de IA

- **Opción elegida:** API de un LLM (Gemini) en conjunto con lógica determinista en Pandas para el procesamiento estructurado.
- **Por qué:** Permite resolver dinámicamente el mapeo inteligente de sinónimos de columnas no estandarizadas, y asiste en la interpretación cualitativa de anomalías de inventario o desviaciones críticas de demanda.
- **Instrucciones para el modelo (system prompt):** No aplica un modelo generativo directo de lenguaje para el cálculo aritmético, pero la IA auxiliar para mapeo debe actuar de manera precisa, identificando columnas candidatas de texto que representen conceptos de 'fecha', 'cantidad', 'código de producto' y 'padre/hijo' de manera técnica y concisa.

## 5. Flujo del usuario

1. El usuario entra en la app y visualiza una barra lateral con parámetros y la sección de carga de archivos en el panel principal.
2. Sube los archivos de Pronóstico, Real y Estructura de BOM. El sistema intenta mapear las columnas.
3. Si hay dudas con los nombres de las columnas, la UI le pide confirmación interactiva. Tras procesar, recibe el análisis con la explosión de materiales y un listado de alertas de desviación según el umbral configurado globalmente en el slider.

## 6. Restricciones

- Coste cero: capa gratuita de la API y despliegue gratuito (ruta A o B).
- La clave de la API va en secretos, nunca en el código.
- Sin datos personales reales.
- Lenguaje sencillo, para alguien sin conocimientos técnicos en programación.
- El cálculo de porcentajes para componentes nuevos o descontinuados debe forzarse artificialmente a `+100%` y `-100%` respectivamente para evitar errores de división por cero.
- El control de alertas por desviación se configura mediante un único umbral global interactivo en la barra lateral.

## 7. Criterios de aceptación

La app está bien si:

| Entrada | Resultado esperado |
|---|---|
| Archivos perfectamente alineados con columnas estándar. | Procesa la explosión recursiva inmediatamente y muestra las tablas sin intervenciones. |
| Archivos con nombres de columnas inconsistentes (ej. 'SKU' en uno y 'Cod_Prod' en otro). | Lanza la UI de mapeo interactivo para que el usuario asocie las columnas y luego procesa con normalidad. |
| Archivos con componentes nuevos que no tienen histórico en uno de los periodos. | Muestra la desviación de dichos elementos con un valor fijo de `+100.0%` o `-100.0%` sin romper el código. |
| Intento de procesar datos y se alcanza el límite de cuota o de carga. | Muestra un banner visual claro con la advertencia: "No se pudo procesar la solicitud debido a límites del servicio. Por favor, reintente en unos minutos." |

## 8. Fuera de alcance (por ahora)

- Segmentación ABC compleja para múltiples sliders de umbrales prioritarios en la barra lateral.
- Integración directa vía API con sistemas ERP (SAP, Oracle, Odoo, etc.).
- Optimización automatizada de stock de seguridad integrada dentro de la misma interfaz.

## 9. Despliegue

- **Ruta:** A (Streamlit Community Cloud)