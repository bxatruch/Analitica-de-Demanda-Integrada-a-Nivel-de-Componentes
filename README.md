# Especificación · [Explosión y Comparador de Demandas con BOM]

> Tiempo demorado entre la carga de una nueva demanda hasta que es explosionado en los requerimientos de los materiales

## 1. Problema y usuario

- **Quién tiene el problema:** [Purchasing planners o Buyers de empresas]
- **Cómo lo resuelve hoy:** [a mano, con análisis en Excel y cruzando informaciones con planners de otras áreas]
- **Qué le molesta de cómo lo hace hoy:** [tiempo invertido en el análisis, errores que a veces obtienen y desfase de informaciones.
- **Qué parte resuelve la IA:** [resuelve los tres puntos, el tiempo invertido, los errores en los cálculos y el desfase de informaciones.]

## 2. Qué hace el producto


1. Permitirá identificar de forma inmediata el impacto que tendrá cada componente con la nueva proyección de ventas.
2. Permitirá comprender de forma inmediata el porcentaje de influencia que esta teniendo cada producto terminado en la variación del componente.
3. permitirá ajustar los criterios de criticidad para obtener un análisis más dinámico.

## 3. Entradas y salidas

El usuario sube 4 archivos, compuestos por demanda anterior, demanda nueva, BOM y Lead Times, cada uno en formato csv. La aplicación corre el análisis y devuelve una tabla con la variación de cada componente (en valor y porcentual), el porcentaje de influencia que cada producto tuvo en dicha variación y la categoría en que dependiendo del porcentaje de variación.


## 4. La pieza de IA

- **Opción elegida:** API de Gemini
- **Por qué:** la app gana una interfaz que cuenta con un SDK completo y con herramientas para detección y corrección de errores.
- **Instrucciones para el modelo (system prompt):** debe tener una visual simple, tabular y de fácil interpretación.

## 5. Flujo del usuario

1. El usuario abre el app y ve las instrucciones sobre los 4 archivos que debe subir, así como también los 4 botones para cargar sus archivos.
2. Luego, el usuario sube los archivos.
3. Recibe luego el resultado del análisis con una tabla resumen con los materiales impactados.

## 6. Restricciones

- Coste cero: capa gratuita de la API y despliegue gratuito (ruta A o B).
- La clave de la API va en secretos, nunca en el código.
- Sin datos personales reales.
- Lenguaje sencillo, para alguien sin conocimientos técnicos.
- Los archivos deben cargarse bajo el formato solicitado.

## 7. Criterios de aceptación

La app está bien si:

| Entrada | Resultado esperado |
|---|---|
| [caso normal] | [la app debe correr el reporte y mostrar la tabla con los resultados] |
| [caso límite: texto vacío, pregunta fuera de tema…] | [no debe pasar nada] |
| [error: algún archivo subido no estaba en el formato solicitado.

## 8. Fuera de alcance (por ahora)

- [Un campo de texto donde el app sugiera acciones inmediatas para componentes dentro del umbral en la configuración de alertas. Adicionalmente, agregar una opción para que el app pueda calcular impactos para what if scenarios]

## 9. Despliegue

- **Ruta:** [A (Streamlit Community Cloud)]
