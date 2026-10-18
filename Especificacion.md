# Especificación de la Aplicación: Explosión y Comparador de Demandas con BOM

## 📝 Descripción del Proyecto
Esta aplicación web, desarrollada con **Streamlit**, está diseñada para los **Purchasing Planners** (Planificadores de Compras). Su objetivo principal es automatizar y acelerar la comparación de dos lanzamientos (releases) de demanda de producto terminado, realizando una explosión de materiales (BOM) en tiempo real para identificar de forma visual e inmediata qué componentes sufrirán un impacto crítico (incrementos o disminuciones agresivos).

---

## 👤 Perfil del Usuario y Problema
* **Usuario Objetivo**: Purchasing Planners.
* **El Problema**: Anteriormente, el tiempo transcurrido desde la carga de una nueva demanda hasta que se reflejaban los requerimientos explotados de materiales causaba cuellos de botella. Los planificadores debían esperar pasivamente la actualización del sistema y luego reaccionar ante los cambios, perdiendo un tiempo valioso para negociar con proveedores o ajustar planes de suministro.
* **La Solución**: Una interfaz ágil que permite subir los archivos de planificación, configurar umbrales de alerta y obtener al instante el desglose de variación por componente y su nivel de influencia.

---

## 🚀 Funcionalidades Clave

1. **Carga Dinámica de Archivos**:
   * Soporte para Forecast Anterior (Producto Terminado) en formato `.csv` o `.xlsx`.
   * Soporte para Forecast Nuevo (Producto Terminado) en formato `.csv` o `.xlsx`.
   * Carga de Estructura de Lista de Materiales (BOM) para mapear productos a componentes.
   * Opción de simulación con datos de demostración integrados.

2. **Motor de Explosión y Consolidación (BOM Engine)**:
   * Estandarización de nombres de columnas de manera flexible (búsqueda de sinónimos como *material*, *componente*, *cant*, *qty*, etc.).
   * Agrupación y suma mensual/anual de demandas basada en reconocimiento de nombres de meses.
   * Cálculo exacto del requerimiento del componente multiplicando la demanda del producto terminado por el factor de la BOM.

3. **Análisis de Desviaciones y Alertas**:
   * **Panel de Configuración Lateral**: Deslizadores para fijar el umbral de incremento crítico (ej. +30%) y disminución crítica (ej. -30%).
   * **Métricas Clave (KPIs)**: Tarjetas visuales con el conteo de materiales en estado *Alerta Roja* (Incremento Crítico), *Alerta Azul* (Disminución Crítica) y *Estables*.

4. **Visualización y Filtros Interactivos**:
   * Filtro multidireccional por categoría de impacto.
   * Tabla interactiva formateada con estilos condicionales y porcentajes de influencia del producto sobre la variación del componente.

---

## 🛠️ Arquitectura Técnica y Tecnologías
* **Lenguaje**: Python 3.x
* **Framework Principal**: Streamlit (para la interfaz de usuario interactiva y el despliegue rápido).
* **Procesamiento de Datos**: Pandas y NumPy (para la manipulación, alineación de índices, agregaciones y operaciones vectoriales).
* **Despliegue**: Streamlit Community Cloud sincronizado con GitHub.

---

## 📊 Estructura de Datos Esperada

### 1. Forecast (Anterior y Nuevo)
Debe contener una columna para el identificador del producto y columnas con datos numéricos de demanda (por ejemplo, columnas de meses como `01-ene`, `01-feb` o una columna general de `Demanda`).
| Producto | 01-ene | 01-feb |
| :--- | :--- | :--- |
| Producto A | 1000 | 1100 |

### 2. Estructura BOM
Debe contener la relación entre el producto final, el componente intermedio y la cantidad necesaria.
| Producto | Componente | Cantidad requerida |
| :--- | :--- | :--- |
| Producto A | Componente A | 5 |

---

## 📈 Próximos Pasos / Roadmap
* [ ] Implementar exportación directa de los resultados consolidados a formato Excel.
* [ ] Añadir gráficos interactivos de barras para los top 10 componentes con mayor variación absoluta.
* [ ] Integración con modelos de IA / LLMs para generar explicaciones textuales automáticas sobre las causas raíz de las desviaciones detectadas.
