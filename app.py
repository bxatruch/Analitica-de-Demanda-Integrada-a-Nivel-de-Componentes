import datetime
import os  # <--- IMPORTANTE: Agregado aquí para que funcione os.getenv()
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
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Explosión y Comparador de Demanda",
    layout="wide"
)

# ... (tus funciones auxiliares y de procesamiento se mantienen igual) ...

        # ----------------------------------------------------
        # CHAT BOX INTEGRADO CON GEMINI
        # ----------------------------------------------------
        st.markdown("--- ")
        st.subheader("💬 Consulta Inteligente con Gemini AI")
        st.write("Realiza preguntas y solicita estrategias basadas en el resultado de la explosión y cálculo de variaciones:")
        
        # Buscar llave API en secrets, variables de entorno o Colab
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
            st.warning("⚠️ No se encontró la clave de API 'GEMINI_API_KEY' en los secretos de configuración o variables de entorno.")
        else:
            try:
                client = genai.Client(api_key=gemini_api_key)
                
                if "chat_history" not in st.session_state:
                    st.session_state["chat_history"] = []

                for chat in st.session_state["chat_history"]:
                    with st.chat_message(chat["role"]):
                        st.write(chat["text"])

                if prompt := st.chat_input("¿Qué materiales de incremento crítico representan mayor riesgo financiero?"):
                    st.session_state["chat_history"].append({"role": "user", "text": prompt})
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    resumen_materiales = merged_tot.to_string(index=False)
                    
                    contexto_completo = (
                        "Actúas como un experto Planner de compras de producción.\n"
                        "Aquí tienes el resultado de la explosión de materiales y su variación de demanda:\n"
                        f"{resumen_materiales}\n\n"
                        f"Responde de forma concisa y profesional a la siguiente pregunta del usuario: {prompt}"
                    )
                    
                    with st.chat_message("assistant"):
                        with st.spinner("Pensando..."):
                            # CORREGIDO: Se usa el modelo oficial válido ("gemini-2.5-flash")
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=contexto_completo,
                            )
                            st.write(response.text)
                            st.session_state["chat_history"].append({"role": "assistant", "text": response.text})
            except Exception as gem_error:
                st.error(f"Error al conectar con la API de Gemini: {gem_error}")
