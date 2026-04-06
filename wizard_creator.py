#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wizard_creator.py - Motor del Wizard con PROCESAMIENTO DE DOCUMENTOS
Los documentos se procesan con ChatGPT y alimentan el prompt final
"""

import streamlit as st
import time
from typing import Dict

try:
    from openai import OpenAI
except ImportError:
    st.error("❌ Instala openai: pip install openai==1.0.0")
    st.stop()

# ============================================================================
# DEFINICIONES DE MOTORES
# ============================================================================

MOTORES_OBJETIVO = {
    "imagen": {
        "nombre": "🖼️ Generación de Imágenes",
        "herramientas": ["DALL-E 3", "Midjourney v6", "Stable Diffusion XL", "Ideogram", "Leonardo.AI"],
        "parametros": {
            "estilo": ["Realista fotográfico", "Ilustración digital", "Anime/Manga", "3D CGI", "Pintura óleo", "Abstracto"],
            "mood": ["Alegre/Positivo", "Oscuro/Dramático", "Neutral/Profesional", "Épico/Heroico", "Melancólico", "Futurista"],
            "resolucion": ["1024x1024", "1920x1080", "1080x1920", "768x1024", "4K+"],
            "detalles": ["Minimalista", "Moderado", "Hyper-detallado"]
        }
    },
    "texto": {
        "nombre": "📝 Generación de Texto",
        "herramientas": ["ChatGPT", "Claude", "Gemini", "Perplexity", "Llama"],
        "parametros": {
            "tipo": ["Artículo/Blog", "Email", "Comunicado", "Guion", "Código", "Análisis"],
            "tono": ["Formal", "Casual", "Creativo", "Técnico", "Humorístico"],
            "largo": ["Corto (200-500)", "Medio (500-1500)", "Largo (1500+)"],
            "estructura": ["Narrativa", "Bullet points", "Q&A", "Paso-a-paso"]
        }
    },
    "musica": {
        "nombre": "🎵 Generación de Música",
        "herramientas": ["Suno AI", "MusicLM", "Jukebox", "Soundraw", "AIVA"],
        "parametros": {
            "genero": ["Pop", "Rock", "Hip-hop", "Electronic", "Jazz", "Clásica"],
            "mood": ["Energético", "Relajante", "Melancólico", "Alegre", "Épico"],
            "duracion": ["Corta 15-30s", "Media 30s-2m", "Larga 2-5m"],
            "uso": ["Background", "Canción completa", "Loop", "Para video"]
        }
    },
    "audio": {
        "nombre": "🎙️ Audio/Voz",
        "herramientas": ["ElevenLabs", "Google NotebookLM", "Vall-E", "Tortoise TTS"],
        "parametros": {
            "tipo": ["Narración", "Podcast", "Diálogo", "Locución", "Asistente"],
            "voz": ["Masculina", "Femenina", "Neutral", "Infantil"],
            "velocidad": ["Lenta", "Normal", "Rápida"],
            "tono": ["Formal", "Amigable", "Entusiasta", "Dramático"]
        }
    },
    "video": {
        "nombre": "🎬 Generación de Video",
        "herramientas": ["Runway Gen-3", "Pika Labs", "Synthesia", "HeyGen"],
        "parametros": {
            "tipo": ["Video corto", "Video medio", "Animación 2D", "Avatar"],
            "estilo": ["Realista", "Animado", "Mixto", "Película"],
            "uso": ["Social media", "YouTube", "Presentación", "Publicidad"],
            "duracion": ["5-15s", "15-60s", "1-3min", "3+min"]
        }
    },
    "archivos": {
        "nombre": "📊 Programas/Archivos",
        "herramientas": ["Excel", "Google Docs", "Photoshop", "Blender", "VS Code"],
        "parametros": {
            "programa": ["Excel", "Docs", "Photoshop", "Blender", "VS Code"],
            "tipo": ["Fórmula", "Script", "Plugin", "Template", "Macro"],
            "complejidad": ["Simple", "Intermedio", "Avanzado"],
            "proposito": ["Automatizar", "Crear herramienta", "Procesar datos"]
        }
    }
}

# ============================================================================
# PROMPTS PARA CHATGPT
# ============================================================================

SYSTEM_PROMPT = """Eres un EXPERTO PROMPT ENGINEER especializado en crear prompts profesionales, 
extensos y altamente optimizados para herramientas de IA.

Tu ÚNICO objetivo es GENERAR el mejor PROMPT POSIBLE que el usuario pueda copiar-pegar 
directamente en sistemas de IA (Midjourney, ChatGPT, Suno, etc).

INSTRUCCIONES CRÍTICAS:
1. Genera PROMPTS EXTENSOS (mínimo 300-500 palabras)
2. Sé ESPECÍFICO y DETALLADO en cada aspecto
3. Incluye técnicas de prompt engineering:
   - Contexto claro y detallado
   - Especificaciones técnicas precisas
   - Ejemplos de estilo cuando sea relevante
   - Restricciones y límites claros
   - Formato esperado del resultado
4. Estructura el prompt de forma PROFESIONAL y CLARA
5. Adapta el lenguaje según la herramienta objetivo
6. Integra COMPLETAMENTE la información de los documentos proporcionados
7. NUNCA respondas directamente a la solicitud
8. SIEMPRE genera un PROMPT que otro usuario pueda usar

El resultado DEBE ser un prompt completo, listo para copiar-pegar."""

SYSTEM_ANALISIS_DOCS = """Eres un ANALIZADOR DE DOCUMENTOS EXPERTO.
Tu tarea es analizar documentos y extraer la información clave relevante 
para alimentar prompts de IA.

Extrae de forma clara y estructurada:
- Información técnica o de especificaciones
- Estilos, tonos, o características específicas
- Limitaciones o restricciones
- Referencias, ejemplos o benchmarks
- Cualquier dato que deba incluirse en el prompt final

Responde SOLO con los puntos clave extraídos, de forma estructurada."""

GENERATION_TEMPLATE = """CREA UN PROMPT PROFESIONAL Y EXTENSO para: {herramienta}

INFORMACIÓN DEL USUARIO:
- Motor: {motor}
- Idea/Concepto: {idea}
- Parámetros técnicos: {parametros}
- Idioma solicitado: {idioma}

INFORMACIÓN EXTRAÍDA DE DOCUMENTOS:
{informacion_documentos}

{notas_seccion}

REQUISITOS PARA EL PROMPT GENERADO:
✓ Mínimo 300-500 palabras
✓ Altamente específico y detallado
✓ Optimizado para: {herramienta}
✓ Estructura profesional y clara
✓ Listo para copiar-pegar directamente
✓ INCORPORA COMPLETAMENTE la información de los documentos
✓ Incluye detalles técnicos específicos para {herramienta}

ESTRUCTURA SUGERIDA PARA EL PROMPT:
1. Instrucción principal clara
2. Detalles y especificaciones técnicas (incluye datos de documentos)
3. Estilo, mood, o características específicas
4. Restricciones y limitaciones
5. Formato esperado del resultado
6. Ejemplos o referencias si son relevantes

GENERA AHORA EL PROMPT PROFESIONAL:
(Responde SOLO con el prompt, sin explicaciones. Es decir, el usuario debe poder 
copiar-pegar tu respuesta directamente en {herramienta})"""

# ============================================================================
# CLASE GENERADOR CON PROCESAMIENTO DE DOCUMENTOS
# ============================================================================

class PromptGenerator:
    """Genera prompts profesionales con análisis de documentos"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            self.cliente = OpenAI(api_key=api_key)
        except Exception as e:
            self.cliente = None
            self.error = str(e)
    
    def procesar_documentos(self, texto_documentos: str, motor: str, herramienta: str) -> str:
        """Procesa documentos con ChatGPT para extraer información clave"""
        
        if not texto_documentos or not self.cliente:
            return "No hay documentos adjuntos."
        
        try:
            # Prompt para analizar documentos
            prompt_analisis = f"""Analiza estos documentos y extrae información clave RELEVANTE 
para crear un prompt profesional para {herramienta} en la categoría de {motor}.

Extrae y estructura:
- Datos técnicos importantes
- Estilos, tonos o características específicas mencionadas
- Restricciones o limitaciones
- Referencias, ejemplos o benchmarks
- Cualquier especificación relevante

DOCUMENTOS:
{texto_documentos[:2000]}

Responde de forma estructurada con SOLO los puntos clave, listos para incorporar en un prompt."""

            response = self.cliente.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_ANALISIS_DOCS},
                    {"role": "user", "content": prompt_analisis}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error al procesar documentos: {str(e)}"
    
    def generar(self, datos: Dict) -> Dict:
        """Genera prompt profesional extenso"""
        
        resultado = {
            "exito": False,
            "prompt": "",
            "costo": 0.0,
            "tiempo": 0.0,
            "error": None,
            "info_documentos": ""
        }
        
        if not self.cliente:
            resultado["error"] = f"Error al conectar: {self.error}"
            return resultado
        
        inicio = time.time()
        
        try:
            # PASO 1: Procesar documentos si existen
            texto_documentos = datos.get("documentos", "")
            info_documentos = ""
            
            if texto_documentos.strip():
                st.info("📄 Procesando documentos con ChatGPT...")
                info_documentos = self.procesar_documentos(
                    texto_documentos,
                    datos["motor"],
                    datos["herramienta"]
                )
                resultado["info_documentos"] = info_documentos
                st.success("✅ Documentos procesados")
            else:
                info_documentos = "No hay documentos adjuntos. Se creará el prompt basado en la idea y parámetros."
            
            # PASO 2: Preparar parámetros de forma legible
            params_texto = "\n".join([
                f"  • {k.replace('_', ' ').title()}: {v}" 
                for k, v in datos.get("parametros", {}).items()
            ])
            
            # PASO 3: Preparar notas
            notas = datos.get("notas", "")
            notas_seccion = f"- NOTAS ADICIONALES DEL USUARIO:\n{notas}\n" if notas else ""
            
            # PASO 4: Construir prompt para generar el PROMPT final
            prompt_usuario = GENERATION_TEMPLATE.format(
                herramienta=datos["herramienta"],
                motor=datos["motor"],
                idea=datos["idea"],
                parametros=params_texto,
                informacion_documentos=info_documentos,
                notas_seccion=notas_seccion,
                idioma=datos.get("idioma", "Español")
            )
            
            # PASO 5: Llamar a ChatGPT para generar el PROMPT final
            st.info("✨ Generando prompt profesional...")
            response = self.cliente.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_usuario}
                ],
                temperature=0.9,
                max_tokens=3500
            )
            
            resultado["prompt"] = response.choices[0].message.content
            resultado["exito"] = True
            resultado["costo"] = 0.012  # Aproximación (2 llamadas a API)
            
        except Exception as e:
            resultado["error"] = f"Error: {str(e)}"
        
        finally:
            resultado["tiempo"] = time.time() - inicio
        
        return resultado

# ============================================================================
# COMPONENTES STREAMLIT
# ============================================================================

def mostrar_wizard_streamlit():
    """Wizard paso-a-paso para crear prompts profesionales"""
    
    # Inicializar estado
    if "paso_wizard" not in st.session_state:
        st.session_state.paso_wizard = 1
        st.session_state.datos_wizard = {
            "motor": None,
            "motor_key": None,
            "herramienta": None,
            "idea": "",
            "parametros": {},
            "documentos": "",
            "notas": "",
            "idioma": "Español"
        }
    
    # Mostrar progreso
    progress = st.session_state.paso_wizard / 5
    st.progress(progress, text=f"Paso {st.session_state.paso_wizard}/5")
    
    # ====================================================================
    # PASO 1: Motor objetivo
    # ====================================================================
    if st.session_state.paso_wizard == 1:
        st.markdown("## Paso 1: ¿Cuál es tu objetivo?")
        st.markdown("Selecciona para qué quieres crear el prompt")
        
        cols = st.columns(3)
        motores_lista = list(MOTORES_OBJETIVO.items())
        
        for idx, (clave, motor) in enumerate(motores_lista):
            with cols[idx % 3]:
                if st.button(motor["nombre"], use_container_width=True, key=f"motor_{clave}"):
                    st.session_state.datos_wizard["motor"] = motor["nombre"]
                    st.session_state.datos_wizard["motor_key"] = clave
                    st.session_state.paso_wizard = 2
                    st.rerun()
    
    # ====================================================================
    # PASO 2: Herramienta
    # ====================================================================
    elif st.session_state.paso_wizard == 2:
        motor_key = st.session_state.datos_wizard.get("motor_key")
        motor_info = MOTORES_OBJETIVO[motor_key]
        
        st.markdown(f"## Paso 2: Herramienta")
        st.markdown(f"Motor: **{motor_info['nombre']}**")
        
        herramienta = st.selectbox(
            "¿Cuál herramienta?",
            motor_info["herramientas"],
            key="select_herramienta"
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
    
    # ====================================================================
    # PASO 3: Idea
    # ====================================================================
    elif st.session_state.paso_wizard == 3:
        st.markdown("## Paso 3: Tu Idea")
        st.markdown("Describe qué quieres crear (con el máximo detalle posible)")
        
        idea = st.text_area(
            "Tu idea:",
            value=st.session_state.datos_wizard.get("idea", ""),
            height=150,
            placeholder="Describe tu idea con tantos detalles como puedas...",
            key="input_idea"
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
    
    # ====================================================================
    # PASO 4: Parámetros + Documentos
    # ====================================================================
    elif st.session_state.paso_wizard == 4:
        motor_key = st.session_state.datos_wizard.get("motor_key")
        motor_info = MOTORES_OBJETIVO[motor_key]
        
        st.markdown("## Paso 4: Parámetros y Documentación")
        
        # Parámetros
        parametros = st.session_state.datos_wizard.get("parametros", {})
        
        for param_key, param_opciones in motor_info["parametros"].items():
            valor = st.selectbox(
                f"**{param_key.replace('_', ' ').title()}**",
                param_opciones,
                key=f"param_{param_key}"
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
            key="wizard_files"
        )
        
        texto_docs = ""
        if archivos:
            st.success(f"✅ {len(archivos)} archivo(s) - Serán procesados con ChatGPT")
            for archivo in archivos:
                try:
                    if archivo.type == "text/plain":
                        contenido = archivo.read().decode("utf-8")
                        texto_docs += f"\n--- {archivo.name} ---\n{contenido}"
                    elif archivo.type == "application/pdf":
                        try:
                            import PyPDF2
                            pdf_reader = PyPDF2.PdfReader(archivo)
                            for page in pdf_reader.pages:
                                texto_docs += page.extract_text()
                        except:
                            st.warning(f"No se pudo leer {archivo.name}")
                    elif "word" in archivo.type:
                        try:
                            from docx import Document
                            doc = Document(archivo)
                            texto_docs += "\n".join([p.text for p in doc.paragraphs])
                        except:
                            st.warning(f"No se pudo leer {archivo.name}")
                    else:
                        texto_docs += f"\n--- {archivo.name} (imagen/referencia) ---"
                except:
                    pass
        
        st.session_state.datos_wizard["documentos"] = texto_docs
        
        # Notas
        st.markdown("---")
        notas = st.text_area(
            "Notas/especificaciones adicionales (opcional):",
            value=st.session_state.datos_wizard.get("notas", ""),
            height=80,
            placeholder="Ej: Debe incluir referencias a X, evitar Y, enfatizar Z...",
            key="input_notas"
        )
        st.session_state.datos_wizard["notas"] = notas
        
        # Idioma
        idioma = st.selectbox(
            "Idioma del prompt generado:",
            ["Español", "English", "Français", "Deutsch", "Português"],
            key="select_idioma"
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
    
    # ====================================================================
    # PASO 5: Resultado - PROMPT GENERADO CON INFORMACIÓN DE DOCUMENTOS
    # ====================================================================
    elif st.session_state.paso_wizard == 5:
        st.markdown("## Paso 5: Tu Prompt Profesional")
        st.markdown("Copia-pega este prompt en tu herramienta de IA")
        
        # Obtener API key desde variable de ambiente (Render.com)
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Si no está en variable de ambiente, permitir ingreso manual
        if not api_key:
            api_key = st.text_input(
                "🔑 API Key de OpenAI",
                type="password",
                placeholder="sk-...",
                key="wizard_api_key"
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
                    st.success("✅ Prompt generado exitosamente")
                    
                    # Mostrar información extraída de documentos
                    if resultado["info_documentos"]:
                        with st.expander("📊 Información extraída de documentos"):
                            st.markdown(resultado["info_documentos"])
                    
                    # Métricas
                    col_costo, col_tiempo = st.columns(2)
                    with col_costo:
                        st.metric("Costo", f"${resultado['costo']:.4f}")
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
                            file_name=f"prompt_{int(time.time())}.txt",
                            mime="text/plain",
                            use_container_width=True
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
                            "idioma": "Español"
                        }
                        st.rerun()
                else:
                    st.error(f"❌ Error: {resultado['error']}")
