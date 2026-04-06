"""
generator.py - Motor de generación de prompts con ChatGPT (v3.3 - Manual de marca + Refinamiento)
"""

import time
import os
from typing import Dict, Optional
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Instala openai: pip install openai>=1.30")

from core.document_processor import DocumentProcessor


class PromptGenerator:
    """Generador de prompts profesionales con análisis de documentos y manual de marca"""

    def __init__(self, api_key: str, cliente_openai: Optional[OpenAI] = None):
        self.api_key = api_key
        self.cliente = cliente_openai or self._crear_cliente(api_key)
        self.document_processor = DocumentProcessor(cliente_openai=self.cliente)
        self.system_prompt = self._cargar_system_prompt()
        self.template_generacion = self._cargar_template_generacion()

    def _crear_cliente(self, api_key: str) -> OpenAI:
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            raise Exception(f"Error al conectar con OpenAI: {str(e)}")

    def _cargar_system_prompt(self) -> str:
        ruta = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "system_prompt.txt")
        try:
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            st.warning(f"⚠️ Error cargando system_prompt.txt: {e}")

        return """Eres un EXPERTO PROMPT ENGINEER especializado en crear prompts profesionales, 
extensos y altamente optimizados. Tu objetivo es generar el mejor 
PROMPT POSIBLE que el usuario pueda usar directamente."""

    def _cargar_template_generacion(self) -> str:
        ruta = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "generation_template.txt")
        try:
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            st.warning(f"⚠️ Error cargando generation_template.txt: {e}")

        return """CREA UN PROMPT PROFESIONAL para: {herramienta}
INFORMACIÓN: {idea}
PARÁMETROS: {parametros}
DOCUMENTOS: {informacion_documentos}
MARCA: {info_marca}
Genera un prompt completo y optimizado."""

    def procesar_documentos(self, texto_documentos: str, motor: str, herramienta: str, idea: str) -> str:
        """Procesa documentos con ChatGPT para extraer información ACCIONABLE"""
        if not texto_documentos or not texto_documentos.strip():
            return "No hay documentos adjuntos."

        try:
            prompt_analisis = f"""Eres un analista experto. El usuario quiere crear un prompt para {herramienta} ({motor}).
Su idea es: "{idea}"

Ha adjuntado documentos con información REAL de su proyecto/empresa.
Tu tarea: extraer TODOS los datos concretos y accionables que sirvan para personalizar el prompt.

EXTRAE OBLIGATORIAMENTE (si existen en el documento):

📌 IDENTIDAD:
- Nombre de empresa/marca/proyecto
- Slogan, tagline o frase clave
- Misión, visión, valores
- Año de fundación, ubicación

📌 OFERTA:
- Productos o servicios específicos (lista completa)
- Público objetivo / cliente ideal
- Diferenciadores / propuesta de valor única
- Precios, planes o paquetes (si aplica)

📌 ESTILO Y TONO:
- Tono de comunicación (formal, cercano, técnico, etc.)
- Colores de marca, tipografías, estilo visual
- Personalidad de marca
- Referencias o ejemplos de estilo

📌 DATOS DUROS:
- Cifras relevantes (ventas, usuarios, años, porcentajes)
- Logros, premios, certificaciones
- Estadísticas o métricas importantes
- Casos de éxito o testimonios

📌 CONTEXTO:
- Industria o sector
- Competidores mencionados
- Situación actual o problema a resolver
- Objetivos específicos del proyecto

DOCUMENTOS:
{texto_documentos[:40000]}

INSTRUCCIONES:
- Extrae DATOS CONCRETOS, no generalidades
- Si el documento dice "Empresa XYZ ofrece consultoría en transformación digital", escribe exactamente eso
- NO inventes información que no esté en los documentos
- Si una categoría no tiene datos, omítela
- Prioriza lo que sea más útil para crear el prompt de {herramienta}
- Sé EXHAUSTIVO: cada nombre, cifra y dato cuenta"""

            response = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un analista de documentos. Extraes información concreta, específica y accionable. Nunca inventas datos. Siempre nombras las cosas por su nombre real."},
                    {"role": "user", "content": prompt_analisis},
                ],
                temperature=0.3,
                max_tokens=3000,
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error al procesar documentos: {str(e)}"

    def procesar_manual_marca(self, texto_manual: str) -> str:
        """
        Procesa el manual de marca y extrae directrices de estilo
        
        Args:
            texto_manual: Texto extraído del manual de marca
            
        Returns:
            Directrices de marca estructuradas
        """
        if not texto_manual or not texto_manual.strip():
            return ""

        try:
            prompt_marca = f"""Eres un experto en branding y diseño de marca.
Analiza este manual de marca y extrae TODAS las directrices que deben aplicarse 
a cualquier pieza de comunicación, diseño o contenido de esta marca.

EXTRAE OBLIGATORIAMENTE:

🎨 IDENTIDAD VISUAL:
- Colores principales (hex, RGB o nombres exactos)
- Colores secundarios y de acento
- Colores prohibidos o a evitar
- Logo: variantes permitidas, espacio de protección, usos incorrectos

🔤 TIPOGRAFÍA:
- Fuente principal (títulos)
- Fuente secundaria (cuerpo)
- Fuentes alternativas
- Tamaños y jerarquía tipográfica

🗣️ TONO DE VOZ:
- Personalidad de marca (adjetivos que la definen)
- Tono de comunicación (formal/informal, cercano/distante)
- Palabras o frases que SÍ usar
- Palabras o frases que NO usar
- Ejemplos de mensajes correctos vs incorrectos

📐 ESTILO VISUAL:
- Estilo fotográfico (tipo de imágenes, filtros, mood)
- Estilo de ilustración (si aplica)
- Iconografía (estilo de íconos)
- Uso de espacios en blanco
- Grid o retícula

🚫 RESTRICCIONES:
- Usos incorrectos del logo
- Combinaciones de color prohibidas
- Estilos visuales a evitar
- Cualquier "no hacer" explícito

MANUAL DE MARCA:
{texto_manual[:40000]}

INSTRUCCIONES:
- Extrae directrices CONCRETAS y APLICABLES
- Si dice "color principal: #F32624", escribe exactamente eso
- Organiza todo como instrucciones que se puedan seguir directamente
- NO inventes directrices que no estén en el manual
- Si una categoría no tiene datos, omítela"""

            response = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en branding. Extraes directrices de marca concretas y aplicables de manuales de marca. Nunca inventas directrices."},
                    {"role": "user", "content": prompt_marca},
                ],
                temperature=0.2,
                max_tokens=3000,
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error al procesar manual de marca: {str(e)}"

    def refinar(self, prompt_actual: str, instruccion: str, datos_originales: Dict) -> Dict:
        """
        Refina un prompt existente basándose en instrucciones del usuario
        
        Args:
            prompt_actual: El prompt generado actualmente
            instruccion: Qué cambiar o mejorar
            datos_originales: Datos del wizard para contexto
            
        Returns:
            Dict con prompt refinado, costo, tiempo, éxito
        """
        resultado = {
            "exito": False,
            "prompt": "",
            "costo": 0.0,
            "tiempo": 0.0,
            "error": None,
        }

        inicio = time.time()

        try:
            herramienta = datos_originales.get("herramienta", "IA")

            prompt_refinamiento = f"""Eres un EXPERTO PROMPT ENGINEER. 
El usuario ya tiene un prompt generado para {herramienta} pero quiere mejorarlo.

PROMPT ACTUAL:
--- INICIO ---
{prompt_actual}
--- FIN ---

INSTRUCCIÓN DE MEJORA DEL USUARIO:
{instruccion}

REGLAS:
1. Mantén TODA la información existente del prompt (datos de empresa, cifras, nombres, etc.)
2. Aplica SOLO los cambios solicitados por el usuario
3. No reduzcas el largo a menos que se pida explícitamente
4. Mantén el formato profesional y la estructura
5. Si se pide más detalle, agrégalo sin eliminar lo existente
6. Si se pide alinear con manual de marca, refuerza colores, tono y estilo visual
7. El resultado debe seguir siendo un prompt listo para copiar-pegar en {herramienta}

GENERA EL PROMPT MEJORADO AHORA.
Responde SOLO con el prompt refinado, sin explicaciones."""

            response = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en refinar y mejorar prompts profesionales. Mantienes toda la información existente y aplicas los cambios solicitados con precisión."},
                    {"role": "user", "content": prompt_refinamiento},
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            resultado["prompt"] = response.choices[0].message.content
            resultado["exito"] = True
            resultado["costo"] = 0.008

        except Exception as e:
            resultado["error"] = f"Error: {str(e)}"

        finally:
            resultado["tiempo"] = time.time() - inicio

        return resultado

    def generar(self, datos: Dict) -> Dict:
        """Genera prompt profesional extenso con soporte de manual de marca"""
        resultado = {
            "exito": False,
            "prompt": "",
            "info_documentos": "",
            "info_marca": "",
            "costo": 0.0,
            "tiempo": 0.0,
            "error": None,
        }

        if not self.cliente:
            resultado["error"] = "Cliente OpenAI no disponible"
            return resultado

        inicio = time.time()

        try:
            # PASO 1: Procesar documentos si existen
            texto_documentos = datos.get("documentos", "")
            info_documentos = ""

            if texto_documentos.strip():
                st.info("📄 Analizando documentos: extrayendo nombres, servicios, cifras y contexto...")
                info_documentos = self.procesar_documentos(
                    texto_documentos,
                    datos["motor"],
                    datos["herramienta"],
                    datos["idea"],
                )
                resultado["info_documentos"] = info_documentos
                st.success("✅ Documentos analizados: información clave extraída")
            else:
                info_documentos = "No hay documentos adjuntos."

            # PASO 2: Procesar manual de marca si existe
            texto_marca = datos.get("manual_marca", "")
            info_marca = ""

            if texto_marca.strip():
                st.info("🎨 Analizando manual de marca: extrayendo colores, tipografía, tono y estilo...")
                info_marca = self.procesar_manual_marca(texto_marca)
                resultado["info_marca"] = info_marca
                st.success("✅ Manual de marca procesado: directrices de estilo extraídas")
            else:
                info_marca = "No se adjuntó manual de marca."

            # PASO 3: Preparar parámetros
            params_texto = "\n".join(
                [f"  • {k.replace('_', ' ').title()}: {v}" for k, v in datos.get("parametros", {}).items()]
            )

            # PASO 4: Preparar palabras clave
            palabras_clave = datos.get("palabras_clave", "")
            if not palabras_clave:
                palabras_clave = "No se especificaron palabras clave"

            # PASO 5: Preparar notas
            notas = datos.get("notas", "")
            notas_seccion = f"NOTAS ADICIONALES DEL USUARIO:\n{notas}\n" if notas else "Sin notas adicionales."

            # PASO 6: Construir prompt final
            prompt_usuario = self.template_generacion.format(
                herramienta=datos["herramienta"],
                motor=datos["motor"],
                idea=datos["idea"],
                parametros=params_texto,
                palabras_clave=palabras_clave,
                informacion_documentos=info_documentos,
                info_marca=info_marca,
                notas_seccion=notas_seccion,
                idioma=datos.get("idioma", "Español"),
            )

            # PASO 7: Llamar a ChatGPT
            st.info("✨ Generando prompt profesional con toda la información integrada...")
            response = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_usuario},
                ],
                temperature=0.9,
                max_tokens=4000,
            )

            resultado["prompt"] = response.choices[0].message.content
            resultado["exito"] = True

            # Costo estimado: 2 llamadas base + marca si aplica
            llamadas = 2
            if texto_marca.strip():
                llamadas += 1
            resultado["costo"] = llamadas * 0.008

        except Exception as e:
            resultado["error"] = f"Error: {str(e)}"

        finally:
            resultado["tiempo"] = time.time() - inicio

        return resultado
