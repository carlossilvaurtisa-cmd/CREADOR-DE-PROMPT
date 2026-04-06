"""
wizard.py - Interfaz de usuario del wizard de 5 pasos (v3.3 - Manual de marca + Refinamiento)
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


def _es_separador(texto: str) -> bool:
    """Detecta si un item de herramientas es un separador visual"""
    return texto.startswith("──")


def _limpiar_wizard() -> None:
    """Limpia completamente el wizard incluyendo keys de widgets"""
    st.session_state.paso_wizard = 1
    st.session_state.datos_wizard = {
        "motor": None,
        "motor_key": None,
        "herramienta": None,
        "idea": "",
        "parametros": {},
        "palabras_clave": "",
        "documentos": "",
        "manual_marca": "",
        "notas": "",
        "idioma": "Español",
    }

    # Limpiar resultado y refinamiento
    for key in ["ultimo_resultado", "modo_refinamiento", "historial_refinamiento"]:
        if key in st.session_state:
            del st.session_state[key]

    # Limpiar TODAS las keys de widgets
    keys_a_limpiar = [k for k in st.session_state.keys() if k.startswith((
        "tag_", "param_", "input_", "select_", "wizard_files",
        "wizard_api_key", "select_herramienta", "select_idioma",
        "wizard_brand_", "refine_",
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
            "manual_marca": "",
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
    """Paso 4: Parámetros, palabras clave, manual de marca y documentos"""
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

    # ===== MANUAL DE MARCA =====
    st.markdown("---")
    st.markdown("### 🎨 Manual de Marca (Opcional)")
    st.info("Si adjuntas un manual de marca, se usará como **guía de estilo obligatoria**: colores, tipografías, tono de voz, logo y personalidad de marca se integrarán en el prompt final.")

    archivo_marca = st.file_uploader(
        "Sube el manual de marca:",
        accept_multiple_files=False,
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="wizard_brand_file",
    )

    texto_marca = ""
    if archivo_marca:
        st.success(f"✅ Manual de marca: {archivo_marca.name}")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            cliente = OpenAI(api_key=api_key)
            processor = DocumentProcessor(cliente_openai=cliente)
        else:
            processor = DocumentProcessor()
        texto_marca = processor.procesar_archivos([archivo_marca])

    st.session_state.datos_wizard["manual_marca"] = texto_marca

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
    """Paso 5: Mostrar resultado, evaluar y refinar prompt"""
    st.markdown("## Paso 5: Tu Prompt Profesional")

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

    # ===== GENERAR PROMPT (primera vez) =====
    if "ultimo_resultado" not in st.session_state:
        if st.button("🚀 Generar Prompt (con análisis de documentos)", use_container_width=True, type="primary"):
            if not api_key:
                st.error("API key no disponible. Contacta al administrador.")
            else:
                with st.spinner("Analizando documentos, manual de marca e integrando para máxima calidad..."):
                    gen = PromptGenerator(api_key)
                    resultado = gen.generar(st.session_state.datos_wizard)

                st.session_state.ultimo_resultado = resultado
                st.session_state.historial_refinamiento = []

                if resultado["exito"]:
                    rate_limiter.incrementar()

                st.rerun()
        return

    # ===== MOSTRAR RESULTADO =====
    resultado = st.session_state.ultimo_resultado

    if not resultado["exito"]:
        st.error(f"❌ Error: {resultado['error']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Volver a editar", use_container_width=True):
                del st.session_state["ultimo_resultado"]
                st.session_state.paso_wizard = 4
                st.rerun()
        with col2:
            if st.button("🔄 INICIAR NUEVO PROMPT", use_container_width=True):
                _limpiar_wizard()
                st.rerun()
        return

    # --- Resultado exitoso ---
    st.success("✅ Prompt generado exitosamente")

    # Mostrar info de documentos y marca
    if resultado.get("info_documentos"):
        with st.expander("📊 Información extraída de documentos"):
            st.markdown(resultado["info_documentos"])

    if resultado.get("info_marca"):
        with st.expander("🎨 Manual de marca aplicado"):
            st.markdown(resultado["info_marca"])

    palabras = st.session_state.datos_wizard.get("palabras_clave", "")
    if palabras:
        with st.expander("🔑 Palabras clave incorporadas"):
            st.markdown(f"**{palabras}**")

    # Historial de refinamientos
    historial = st.session_state.get("historial_refinamiento", [])
    if historial:
        with st.expander(f"🔄 Historial de mejoras ({len(historial)} refinamiento(s))"):
            for i, ref in enumerate(historial, 1):
                st.markdown(f"**Mejora {i}:** {ref}")

    col_costo, col_tiempo = st.columns(2)
    with col_costo:
        st.metric("Costo est.", f"${resultado['costo']:.4f}")
    with col_tiempo:
        st.metric("Tiempo", f"{resultado['tiempo']:.1f}s")

    st.markdown("### 📋 Tu Prompt")
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

    # ===== EVALUACIÓN Y REFINAMIENTO =====
    st.markdown("---")
    st.markdown("### 🔍 ¿Cómo quedó tu prompt?")

    col_ok, col_mejorar = st.columns(2)

    with col_ok:
        if st.button("✅ Mi prompt está OK", use_container_width=True, type="primary"):
            st.session_state.modo_refinamiento = False
            herramienta = st.session_state.datos_wizard.get("herramienta", "tu herramienta")
            st.balloons()
            st.success(f"""
            🎉 **¡Listo!**
            1. Copia el prompt arriba
            2. Pégalo en **{herramienta}**
            3. ¡Obtén resultados profesionales!
            """)

    with col_mejorar:
        if st.button("🔧 Deseo mejorarlo", use_container_width=True):
            st.session_state.modo_refinamiento = True
            st.rerun()

    # ===== PANEL DE REFINAMIENTO =====
    if st.session_state.get("modo_refinamiento", False):
        st.markdown("---")
        st.markdown("### 🔧 Mejorar Prompt")

        # Menú desplegable con mejoras predefinidas
        mejoras_predefinidas = [
            "-- Selecciona una mejora --",
            "📏 Hacerlo más largo y detallado",
            "✂️ Hacerlo más corto y conciso",
            "🎯 Más específico y menos genérico",
            "💼 Tono más formal y profesional",
            "😊 Tono más cercano y conversacional",
            "📊 Agregar más datos y cifras concretas",
            "🎨 Más énfasis en lo visual y estético",
            "⚡ Más directo, menos introducciones",
            "🔑 Enfatizar más las palabras clave",
            "📄 Integrar más información de los documentos adjuntos",
            "🎨 Alinear más con el manual de marca",
            "🧩 Mejorar la estructura y organización",
            "🚫 Agregar más restricciones de lo que NO hacer",
            "💡 Agregar ejemplos o referencias concretas",
            "🌍 Adaptar mejor al idioma/cultura objetivo",
        ]

        mejora_seleccionada = st.selectbox(
            "Mejoras sugeridas:",
            mejoras_predefinidas,
            key="refine_select",
        )

        # Input para cambios personalizados
        cambio_custom = st.text_area(
            "O escribe tus cambios específicos:",
            placeholder="Ej: Agrega una sección sobre sostenibilidad, cambia el público a millennials, incluye más datos de ventas del PDF...",
            height=80,
            key="refine_custom",
        )

        if st.button("🚀 Aplicar mejora", use_container_width=True, type="primary"):
            # Determinar qué mejora aplicar
            instruccion_mejora = ""

            if mejora_seleccionada != "-- Selecciona una mejora --":
                instruccion_mejora = mejora_seleccionada

            if cambio_custom.strip():
                if instruccion_mejora:
                    instruccion_mejora += f"\n\nAdemás: {cambio_custom.strip()}"
                else:
                    instruccion_mejora = cambio_custom.strip()

            if not instruccion_mejora:
                st.error("Selecciona una mejora o escribe tus cambios.")
            elif not api_key:
                st.error("API key no disponible.")
            else:
                with st.spinner("Refinando prompt..."):
                    gen = PromptGenerator(api_key)
                    resultado_refinado = gen.refinar(
                        prompt_actual=resultado["prompt"],
                        instruccion=instruccion_mejora,
                        datos_originales=st.session_state.datos_wizard,
                    )

                if resultado_refinado["exito"]:
                    rate_limiter.incrementar()

                    # Actualizar resultado
                    st.session_state.ultimo_resultado["prompt"] = resultado_refinado["prompt"]
                    st.session_state.ultimo_resultado["costo"] += resultado_refinado["costo"]
                    st.session_state.ultimo_resultado["tiempo"] += resultado_refinado["tiempo"]

                    # Guardar en historial
                    historial = st.session_state.get("historial_refinamiento", [])
                    historial.append(instruccion_mejora)
                    st.session_state.historial_refinamiento = historial

                    st.session_state.modo_refinamiento = False
                    st.rerun()
                else:
                    st.error(f"Error al refinar: {resultado_refinado['error']}")

    # ===== BOTÓN NUEVO PROMPT (siempre visible) =====
    st.markdown("---")
    if st.button("🔄 INICIAR NUEVO PROMPT", use_container_width=True):
        _limpiar_wizard()
        st.rerun()
