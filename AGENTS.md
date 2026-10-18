# 🤖 AGENTS.md - Guía de Integración para Agentes de IA

Este documento proporciona a cualquier agente de inteligencia artificial (LLM, Copilot, asistentes autónomos) el contexto, la arquitectura del código y las reglas de negocio necesarias para entender, mantener o ampliar esta aplicación de Streamlit.

---

## 🎯 Propósito del Sistema
La aplicación automatiza la **explosión de materiales (BOM)** a partir de dos versiones de forecast de Producto Terminado (Anterior vs. Nuevo) para identificar variaciones críticas de demanda a nivel de componentes individuales, facilitando el análisis de impacto para los planificadores de compras.

---

## 📂 Estructura del Proyecto y Flujo de Datos

```
📥 Entrada de Datos (Forecast Ant, Forecast Nuevo, BOM)
        │
        ▼
⚙️ Normalización Dinámica de Columnas (Pandas)
        │
        ▼
💥 Multiplicación Vectorial (Demanda Producto * Factor BOM)
        │
        ▼
📊 Agrupación y Consolidación a nivel de Componente
        │
        ▼
📈 Evaluación de Alertas (Umbrales de Variación %)
        │
        ▼
🖥️ Renderizado de Interfaz y Tablas (Streamlit)
```

---

## 🛠️ Especificaciones Técnicas para el Agente

### 1. Variables Críticas del Entorno
* **Entrada de Datos**: DataFrames de Pandas (`df_fc_ant`, `df_fc_nuevo`, `df_bom`).
* **Motor de Alertas**: 
  * `umbral_subida` (int, default: `30`): Porcentaje mínimo para clasificar un incremento como crítico.
  * `umbral_bajada` (int, default: `-30`): Porcentaje máximo para clasificar una disminución como crítica.

### 2. Lógica del Algoritmo de Explosión
Para calcular los requerimientos de un componente $C$ requerido por un producto $P$:
$$\text{Demanda\_Comp} = \text{Demanda\_Producto} \times \text{Cantidad\_BOM}$$

### 3. Reglas de Normalización de Columnas (Robustez frente a inputs sucios)
Al sugerir modificaciones en el código, asegúrate de mantener el sistema de detección de columnas tolerante a fallos:
* **Componentes / Materiales**: Busca coincidencias parciales con `["material", "componente", "part_number"]`.
* **Factores BOM**: Busca coincidencias con `["cant", "qty", "factor", "requerida"]`.
* **Periodos Temporales**: Detecta meses automáticamente usando la lista de abreviaturas en español e inglés (`palabras_mes`).

---

## 🚨 Directrices para Modificación del Código
Cuando un usuario te pida modificar o corregir el código de esta app, sigue estrictamente estas reglas:
1. **Preservar el Modo Demo**: No elimines el interruptor `use_demo` que genera DataFrames de prueba, ya que es crucial para pruebas rápidas de usuarios que no disponen de archivos inmediatos.
2. **Compatibilidad Excel/CSV**: Cualquier función de lectura de archivos cargados (`st.file_uploader`) debe contemplar tanto `.csv` como `.xlsx` mediante validaciones condicionales.
3. **Manejo de División por Cero**: Al calcular variaciones porcentuales, usa `np.where` o `.replace([np.inf, -np.inf], np.nan).fillna(0)` para evitar errores aritméticos cuando la demanda anterior sea cero.
4. **Estilo Streamlit**: Mantener el uso de layouts fluidos (`layout="wide"`) y el uso de `st.dataframe` con estilización condicional para mejorar la legibilidad visual de los planificadores.
