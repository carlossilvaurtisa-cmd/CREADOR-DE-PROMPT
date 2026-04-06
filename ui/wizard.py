"""
wizard.py - Interfaz de usuario del wizard de 5 pasos (v3.2.1 - Fix reinicio + docs)
"""

import os
import yaml
import streamlit as st
from typing import Dict, Optional, List

from core.generator import PromptGenerator
from core.document_processor import DocumentProcessor
from core.rate_limiter import SessionRateLimiter


def _cargar_motores() -> Dict:
    """Carga los motores desde config/engines.yaml"""
    ruta = os.path.join(os.path.dirname(__file__), "..", "config", "engines.yaml")

    try:
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("motores", {})
    except Exception as e:
        st.warning(f"⚠️ Error cargando engines.yaml: {e}")

    return {
        "texto": {
            "nombre": "📝 Generación de Texto",
            "herramientas": ["ChatGPT"],
            "parametros": {"tipo": {"label": "Tipo", "opciones": ["Artículo"]}}
        }
    }


def _cargar_tags() -> Dict:
    """Carga los tags desde config/tags.yaml"""
    ruta = os.path.join(os.path.dirname(__file__), "..", "config", "tags.yaml")

    try:
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("tags", {})
    except Exception as e:
        st.warning(f"⚠️ Error cargando tags.yaml: {e}")

    return {
        "estilo": ["Profesional", "Moderno"],
        "prensa": ["Comunicado de prensa", "Objetivo/Neutral"]
    }


def _limpiar_wizard() -> None:
    """Limpia completamente el wizard incluyendo keys de widgets"""
    # Resetear paso y datos
    st.session_state.paso_wizard = 1
    st.session_state.datos_wizard = {
        "motor": None,
        "motor_key": None,
        "herramienta": None,
        "idea": "",
        "parametros": {},
        "palabras_clave": "",
        "documentos": "",
        "notas": "",
        "idioma": "Español",
    }

    # Limpiar resultado guardado
    if "ultimo_resultado" in st.session_state:
        del st.session_state["ultimo_resultado"]

    # Limpiar TODAS las keys de widgets para evitar conflicto
    keys_a_limpiar = [k for k in st.session_state.keys() if k.startswith((
        "tag_", "param_", "input_", "select_", "wizard_files",
        "wizard_api_key", "select_herramienta", "select_idioma",
    ))]
    for key in keys_a_limpiar:
        del st.session_state[key]


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
            "palabras_clave": "",
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

    if st.session_state.paso_wizard == 1:
        _paso_1_motor_objetivo(motores)
    elif st.session_state.paso_wizard == 2:
        _paso_2_herramienta(motores)
    elif st.session_state.paso_wizard == 3:
        _paso_3_idea()
    elif st.session_state.paso_wizard == 4:
        _paso_4_parametros_documentos(motores)
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


def _es_separador(texto: str) -> bool:
    """Detecta si un item de herramientas es un separador visual"""
    return texto.startswith("──")


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

    # Validar que no sea un separador
    es_sep = _es_separador(herramienta)
    if es_sep:
        st.warning("⬆️ Esa es una categoría, selecciona una herramienta de la lista.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Atrás", use_container_width=True):
            st.session_state.paso_wizard = 1
            st.rerun()

    with col2:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            if es_sep:
                st.error("Selecciona una herramienta válida, no una categoría.")
            else:
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
    """Paso 4: Parámetros, palabras clave y documentos"""
    motor_key = st.session_state.datos_wizard.get("motor_key")
    motor_info = motores[motor_key]

    st.markdown("## Paso 4: Parámetros, Palabras Clave y Documentos")

    # ===== PARÁMETROS =====
    st.markdown("### 📊 Parámetros Técnicos")
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

    # ===== PALABRAS CLAVE =====
    st.markdown("---")
    st.markdown("### 🔑 Palabras Clave")
    st.info("Las palabras clave mejoran significativamente la calidad del prompt final. Selecciona o escribe las tuyas.")

    tags = _cargar_tags()
    palabras_seleccionadas = []

    tab_names = list(tags.keys())
    tabs = st.tabs([f"{name.title()}" for name in tab_names])

    for tab_idx, (categoria, items) in enumerate(tags.items()):
        with tabs[tab_idx]:
            cols = st.columns(2)
            for idx, tag in enumerate(items):
                with cols[idx % 2]:
                    if st.checkbox(tag, key=f"tag_{categoria}_{tag}"):
                        palabras_seleccionadas.append(tag)

    st.markdown("**O escribe tus propias palabras clave:**")
    palabras_custom = st.text_area(
        "Palabras personalizadas (separa con comas):",
        value=st.session_state.datos_wizard.get("palabras_clave", ""),
        placeholder="ej: minimalista, futurista, tecnología, neon",
        height=60,
        key="input_palabras"
    )

    todas_palabras = palabras_seleccionadas + [p.strip() for p in palabras_custom.split(",") if p.strip()]
    palabras_texto = ", ".join(todas_palabras)
    st.session_state.datos_wizard["palabras_clave"] = palabras_texto

    if todas_palabras:
        st.success(f"✅ {len(todas_palabras)} palabras clave seleccionadas")

    # ===== DOCUMENTOS =====
    st.markdown("---")
    st.markdown("### 📎 Documentación (Opcional)")
    st.info("Carga PDF, TXT, DOCX, imágenes. ChatGPT analizará automáticamente e incorporará en el prompt.")

    archivos = st.file_uploader(
        "Sube archivos:",
        accept_multiple_files=True,
        type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
        key="wizard_files",
    )

    texto_docs = ""
    if archivos:
        st.success(f"✅ {len(archivos)} archivo(s) - Serán procesados con ChatGPT")
        # Obtener API key para el procesador
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            cliente = OpenAI(api_key=api_key)
            processor = DocumentProcessor(cliente_openai=cliente)
        else:
            processor = DocumentProcessor()
        texto_docs = processor.procesar_archivos(archivos)

    st.session_state.datos_wizard["documentos"] = texto_docs

    # ===== NOTAS ADICIONALES =====
    st.markdown("---")
    st.markdown("### 📝 Notas Adicionales")
    notas = st.text_area(
        "Especificaciones adicionales (opcional):",
        value=st.session_state.datos_wizard.get("notas", ""),
        height=80,
        placeholder="Ej: Debe incluir referencias a X, evitar Y, enfatizar Z...",
        key="input_notas",
    )
    st.session_state.datos_wizard["notas"] = notas

    # ===== IDIOMA =====
    st.markdown("---")
    idioma = st.selectbox(
        "Idioma del prompt generado:",
        ["Español", "English", "Français", "Deutsch", "Português"],
        key="select_idioma",
    )
    st.session_state.datos_wizard["idioma"] = idioma

    # ===== NAVEGACIÓN =====
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
    """Paso 5: Mostrar resultado y generar prompt"""
    st.markdown("## Paso 5: Tu Prompt Profesional")
    st.markdown("Copia-pega este prompt en tu herramienta de IA")

    rate_limiter.mostrar_widget_streamlit()

    if not rate_limiter.puede_generar():
        st.error("❌ Has alcanzado el límite de prompts por sesión")
        if st.button("🔄 Reiniciar sesión", use_container_width=True):
            rate_limiter.reiniciar_contador()
            st.rerun()
        return

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

    # ===== GENERAR PROMPT (guarda resultado en session_state) =====
    if st.button("🚀 Generar Prompt (con análisis de documentos)", use_container_width=True, type="primary"):
        if not api_key:
            st.error("API key no disponible. Contacta al administrador.")
        else:
            with st.spinner("Analizando documentos, palabras clave e integrando para máxima calidad..."):
                gen = PromptGenerator(api_key)
                resultado = gen.generar(st.session_state.datos_wizard)

            # Guardar resultado en session_state para que persista
            st.session_state.ultimo_resultado = resultado

            if resultado["exito"]:
                rate_limiter.incrementar()

            # Rerun para mostrar resultado desde session_state
            st.rerun()

    # ===== MOSTRAR RESULTADO (desde session_state, independiente del botón) =====
    if "ultimo_resultado" in st.session_state:
        resultado = st.session_state.ultimo_resultado

        if resultado["exito"]:
            st.success("✅ Prompt generado exitosamente")

            if resultado["info_documentos"]:
                with st.expander("📊 Información extraída de documentos"):
                    st.markdown(resultado["info_documentos"])

            palabras = st.session_state.datos_wizard.get("palabras_clave", "")
            if palabras:
                with st.expander("🔑 Palabras clave incorporadas"):
                    st.markdown(f"**{palabras}**")

            col_costo, col_tiempo = st.columns(2)
            with col_costo:
                st.metric("Costo est.", f"${resultado['costo']:.4f}")
            with col_tiempo:
                st.metric("Tiempo", f"{resultado['tiempo']:.1f}s")

            st.markdown("### 📋 Tu Prompt (listo para copiar-pegar)")
            st.markdown("---")
            st.code(resultado["prompt"], language="text")
            st.markdown("---")

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

            herramienta = st.session_state.datos_wizard.get("herramienta", "tu herramienta")
            st.info(f"""
            💡 **Próximos pasos:**
            1. Copia el prompt arriba
            2. Pégalo en **{herramienta}**
            3. ¡Obtén resultados profesionales!
            """)

            st.markdown("---")

            # BOTÓN INICIAR NUEVO PROMPT - AHORA FUERA DEL BLOQUE DEL BOTÓN GENERAR
            if st.button("🔄 INICIAR NUEVO PROMPT", use_container_width=True, type="primary"):
                _limpiar_wizard()
                st.rerun()

        else:
            st.error(f"❌ Error: {resultado['error']}")

            # Permitir reintentar o volver
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Volver a editar", use_container_width=True):
                    if "ultimo_resultado" in st.session_state:
                        del st.session_state["ultimo_resultado"]
                    st.session_state.paso_wizard = 4
                    st.rerun()
            with col2:
                if st.button("🔄 INICIAR NUEVO PROMPT", use_container_width=True):
                    _limpiar_wizard()
                    st.rerun()
