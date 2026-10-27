# 📊 Explosión y Comparador de Demandas con BOM

[![Streamlit App](https://static.streamlit.io/badge-branded.svg)](https://mi-reto-mdfxvvzdhjdyfeu6cbphmu.streamlit.app/)

Esta aplicación web interactiva ayuda a los **Purchasing Planners** (Planificadores de Compras) a identificar de forma visual, ágil e inmediata el impacto que tienen los nuevos lanzamientos (*releases*) de demanda sobre los componentes individuales mediante una **explosión de materiales (BOM)** en tiempo real.

---

## 🔍 El Problema y la Solución

* **El Problema:** El desfase de tiempo entre la carga de una nueva demanda en los sistemas corporativos y su correspondiente explosión de materiales retrasaba la toma de decisiones, obligando a los planificadores a reaccionar tarde ante los cambios críticos de suministro.
* **La Solución:** Esta app automatiza el proceso de explosión de forma instantánea al subir los forecasts (anterior y nuevo) junto con la estructura de la lista de materiales (BOM), visualizando desviaciones con códigos de color de alerta personalizables.

---

## ✨ Características Clave

* **Carga de Datos Flexible:** Soporte para archivos `.xlsx` para el forecast anterior, forecast nuevo y estructura BOM.
* **Modo de Demostración:** Incluye datos simulados interactivos para probar la lógica de inmediato sin subir archivos propios.
* **Estandarización Inteligente:** Mapeo automático de nombres de columnas (detectando sinónimos de productos, componentes y cantidades).
* **Alertas Personalizables:** Deslizadores dinámicos para ajustar los umbrales de incrementos críticos (Rojo) y disminuciones críticas (Azul).
* **Cálculo de Influencia:** Muestra exactamente qué producto final es el responsable del cambio de volumen del componente.

---

## 🛠️ Instalación y Uso Local

Si deseas ejecutar esta aplicación de manera local en tu ordenador, sigue estos sencillos pasos:

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

### 2. Instalar dependencias
Asegúrate de tener Python instalado y ejecuta:
```bash
pip install streamlit pandas numpy openpyxl
```

### 3. Iniciar la aplicación
```bash
streamlit run app.py
```

---

## 📊 Requisitos de los Archivos de Entrada

Para que la herramienta funcione correctamente con tus propios datos, asegúrate de que los archivos contengan las siguientes referencias:

1. **Forecast (Anterior y Nuevo):** Debe incluir una columna con el nombre del producto (por ejemplo, `Producto`) y columnas con volúmenes de demanda mensuales o anuales.
2. **Estructura BOM:** Debe contener las columnas que vinculen el producto con sus componentes y la cantidad necesaria (por ejemplo, `Producto`, `Componente`, `Cantidad requerida`).
