"""
wizard.py - Interfaz de usuario del wizard de 5 pasos
"""

import os
import yaml
import streamlit as st
from typing import Dict, Optional

from core.generator import PromptGenerator
from core.document_processor import DocumentProcessor
from core.rate_limiter import SessionRateLimiter


def _cargar_motores() -> Dict:
    """
    Carga los motores desde config/engines.yaml
    
    Returns:
        Diccionario con configuración de motores
    """
    ruta = os.path.join(os.path.dirname(__file__), "..", "config", "engines.yaml")

    try:
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("motores", {})
    except Exception as e:
        st.warning(f"⚠️ Error cargando engines.yaml: {e}")

    # Fallback: retornar estructura mínima
    return {
        "texto": {
            "nombre": "📝 Generación de Texto",
            "herramientas": ["ChatGPT"],
            "parametros": {"tipo": {"label": "Tipo", "opciones": ["Artículo"]}}
        }
    }


def _inicializar_session_state() -> None:
    """Inicializa variables de session_state del wizard"""
    if "paso_wizard" not in st.session_state:
        st.session_state.paso_wizard = 1

    if "datos_wizard" not in st.session_state:
        st.session_state.datos_wizard = {
            "motor": None,
            "motor_key": None,
            "herramienta": None,
            "idea": "",
            "parametros": {},
            "documentos": "",
            "notas": "",
            "idioma": "Español",
        }

    if "rate_limiter" not in st.session_state:
        st.session_state.rate_limiter = SessionRateLimiter(limite_por_sesion=30)


def mostrar_wizard_streamlit() -> None:
    """Función principal que renderiza el wizard de 5 pasos"""

    _inicializar_session_state()
    motores = _cargar_motores()
    rate_limiter = st.session_state.rate_limiter

    # Mostrar progreso
    progress = st.session_state.paso_wizard / 5
    st.progress(progress, text=f"Paso {st.session_state.paso_wizard}/5")

    # ====================================================================
    # PASO 1: Motor objetivo
    # ====================================================================
    if st.session_state.paso_wizard == 1:
        _paso_1_motor_objetivo(motores)

    # ====================================================================
    # PASO 2: Herramienta
    # ====================================================================
    elif st.session_state.paso_wizard == 2:
        _paso_2_herramienta(motores)

    # ====================================================================
    # PASO 3: Idea
    # ====================================================================
    elif st.session_state.paso_wizard == 3:
        _paso_3_idea()

    # ====================================================================
    # PASO 4: Parámetros + Documentos
    # ====================================================================
    elif st.session_state.paso_wizard == 4:
        _paso_4_parametros_documentos(motores)

    # ====================================================================
    # PASO 5: Resultado
    # ====================================================================
    elif st.session_state.paso_wizard == 5:
        _paso_5_resultado(rate_limiter)


def _paso_1_motor_objetivo(motores: Dict) -> None:
    """Paso 1: Seleccionar motor objetivo"""
    st.markdown("## Paso 1: ¿Cuál es tu objetivo?")
    st.markdown("Selecciona para qué quieres crear el prompt")

    cols = st.columns(3)
    motores_lista = list(motores.items())

    for idx, (clave, motor) in enumerate(motores_lista):
        with cols[idx % 3]:
            if st.button(motor["nombre"], use_container_width=True, key=f"motor_{clave}"):
                st.session_state.datos_wizard["motor"] = motor["nombre"]
                st.session_state.datos_wizard["motor_key"] = clave
                st.session_state.paso_wizard = 2
                st.rerun()


def _paso_2_herramienta(motores: Dict) -> None:
    """Paso 2: Seleccionar herramienta específica"""
    motor_key = st.session_state.datos_wizard.get("motor_key")
    motor_info = motores[motor_key]

    st.markdown(f"## Paso 2: Herramienta")
    st.markdown(f"Motor: **{motor_info['nombre']}**")

    herramienta = st.selectbox(
        "¿Cuál herramienta?",
        motor_info["herramientas"],
        key="select_herramienta",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Atrás", use_container_width=True):
            st.session_state.paso_wizard = 1
            st.rerun()

    with col2:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            st.session_state.datos_wizard["herramienta"] = herramienta
            st.session_state.paso_wizard = 3
            st.rerun()


def _paso_3_idea() -> None:
    """Paso 3: Describir idea"""
    st.markdown("## Paso 3: Tu Idea")
    st.markdown("Describe qué quieres crear (con el máximo detalle posible)")

    idea = st.text_area(
        "Tu idea:",
        value=st.session_state.datos_wizard.get("idea", ""),
        height=150,
        placeholder="Describe tu idea con tantos detalles como puedas...",
        key="input_idea",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Atrás", use_container_width=True):
            st.session_state.paso_wizard = 2
            st.rerun()

    with col2:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            if idea.strip():
                st.session_state.datos_wizard["idea"] = idea
                st.session_state.paso_wizard = 4
                st.rerun()
            else:
                st.error("Describe tu idea")


def _paso_4_parametros_documentos(motores: Dict) -> None:
    """Paso 4: Parámetros y documentos"""
    motor_key = st.session_state.datos_wizard.get("motor_key")
    motor_info = motores[motor_key]

    st.markdown("## Paso 4: Parámetros y Documentación")

    # Parámetros
    parametros = st.session_state.datos_wizard.get("parametros", {})

    for param_key, param_config in motor_info["parametros"].items():
        label = param_config.get("label", param_key.title())
        opciones = param_config.get("opciones", [])

        valor = st.selectbox(
            f"**{label}**",
            opciones,
            key=f"param_{param_key}",
        )
        parametros[param_key] = valor

    st.session_state.datos_wizard["parametros"] = parametros

    # DOCUMENTOS
    st.markdown("---")
    st.markdown("### 📎 Adjuntar documentación")
    st.info("Carga PDF, TXT, DOCX, imágenes. **ChatGPT analizará automáticamente y alimentará el prompt final.**")

    archivos = st.file_uploader(
        "Sube archivos:",
        accept_multiple_files=True,
        type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
        key="wizard_files",
    )

    # Procesar archivos
    texto_docs = ""
    if archivos:
        st.success(f"✅ {len(archivos)} archivo(s) - Serán procesados con ChatGPT")
        processor = DocumentProcessor()
        texto_docs = processor.procesar_archivos(archivos)

    st.session_state.datos_wizard["documentos"] = texto_docs

    # Notas
    st.markdown("---")
    notas = st.text_area(
        "Notas/especificaciones adicionales (opcional):",
        value=st.session_state.datos_wizard.get("notas", ""),
        height=80,
        placeholder="Ej: Debe incluir referencias a X, evitar Y, enfatizar Z...",
        key="input_notas",
    )
    st.session_state.datos_wizard["notas"] = notas

    # Idioma
    idioma = st.selectbox(
        "Idioma del prompt generado:",
        ["Español", "English", "Français", "Deutsch", "Português"],
        key="select_idioma",
    )
    st.session_state.datos_wizard["idioma"] = idioma

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Atrás", use_container_width=True):
            st.session_state.paso_wizard = 3
            st.rerun()

    with col2:
        if st.button("Generar Prompt →", use_container_width=True, type="primary"):
            st.session_state.paso_wizard = 5
            st.rerun()


def _paso_5_resultado(rate_limiter: SessionRateLimiter) -> None:
    """Paso 5: Mostrar resultado"""
    st.markdown("## Paso 5: Tu Prompt Profesional")
    st.markdown("Copia-pega este prompt en tu herramienta de IA")

    # Mostrar widget de rate limiter
    rate_limiter.mostrar_widget_streamlit()

    if not rate_limiter.puede_generar():
        st.error("❌ Has alcanzado el límite de prompts por sesión")
        if st.button("🔄 Cerrar sesión y reiniciar", use_container_width=True):
            rate_limiter.reiniciar_contador()
            st.rerun()
        return

    # Obtener API key desde variable de ambiente
    import os
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        api_key = st.text_input(
            "🔑 API Key de OpenAI",
            type="password",
            placeholder="sk-...",
            key="wizard_api_key",
        )
    else:
        st.info("🔐 Usando API key centralizada de GIRO")

    if st.button("🚀 Generar Prompt (con análisis de documentos)", use_container_width=True, type="primary"):
        if not api_key:
            st.error("API key no disponible. Contacta al administrador.")
        else:
            with st.spinner("Analizando documentos y generando prompt..."):
                gen = PromptGenerator(api_key)
                resultado = gen.generar(st.session_state.datos_wizard)

            if resultado["exito"]:
                rate_limiter.incrementar()
                st.success("✅ Prompt generado exitosamente")

                # Mostrar información extraída de documentos
                if resultado["info_documentos"]:
                    with st.expander("📊 Información extraída de documentos"):
                        st.markdown(resultado["info_documentos"])

                # Métricas
                col_costo, col_tiempo = st.columns(2)
                with col_costo:
                    st.metric("Costo est.", f"${resultado['costo']:.4f}")
                with col_tiempo:
                    st.metric("Tiempo", f"{resultado['tiempo']:.1f}s")

                # MOSTRAR PROMPT GENERADO
                st.markdown("### 📋 Tu Prompt (listo para copiar-pegar)")
                st.markdown("---")
                st.code(resultado["prompt"], language="text")
                st.markdown("---")

                # Acciones
                col_copy, col_download = st.columns(2)
                with col_copy:
                    if st.button("📋 Copiar al portapapeles", use_container_width=True):
                        st.info("✅ Selecciona todo (Ctrl+A) y copia (Ctrl+C)")

                with col_download:
                    st.download_button(
                        label="⬇️ Descargar como TXT",
                        data=resultado["prompt"],
                        file_name=f"prompt_{int(__import__('time').time())}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

                st.markdown("---")
                st.info(f"💡 **Próximos pasos:**\n1. Copia el prompt arriba\n2. Pégalo en {st.session_state.datos_wizard['herramienta']}\n3. ¡Obtén resultados profesionales!")

                st.markdown("---")
                if st.button("🔄 Crear otro prompt", use_container_width=True):
                    st.session_state.paso_wizard = 1
                    st.session_state.datos_wizard = {
                        "motor": None,
                        "motor_key": None,
                        "herramienta": None,
                        "idea": "",
                        "parametros": {},
                        "documentos": "",
                        "notas": "",
                        "idioma": "Español",
                    }
                    st.rerun()
            else:
                st.error(f"❌ Error: {resultado['error']}")
