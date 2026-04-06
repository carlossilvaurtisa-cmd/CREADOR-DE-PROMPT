"""
generator.py - Motor de generación de prompts con ChatGPT (v3.2.1 - Docs mejorados)
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
    """Generador de prompts profesionales con análisis de documentos"""

    def __init__(self, api_key: str, cliente_openai: Optional[OpenAI] = None):
        """
        Inicializa el generador de prompts
        
        Args:
            api_key: API key de OpenAI
            cliente_openai: Cliente OpenAI (opcional, se crea si no se proporciona)
        """
        self.api_key = api_key
        self.cliente = cliente_openai or self._crear_cliente(api_key)
        self.document_processor = DocumentProcessor(cliente_openai=self.cliente)
        self.system_prompt = self._cargar_system_prompt()
        self.template_generacion = self._cargar_template_generacion()

    def _crear_cliente(self, api_key: str) -> OpenAI:
        """Crea un cliente OpenAI"""
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            raise Exception(f"Error al conectar con OpenAI: {str(e)}")

    def _cargar_system_prompt(self) -> str:
        """
        Carga el SYSTEM_PROMPT desde archivo externo
        
        Returns:
            System prompt para ChatGPT
        """
        ruta = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "system_prompt.txt")

        try:
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            st.warning(f"⚠️ Error cargando system_prompt.txt: {e}")

        # Fallback hardcodeado
        return """Eres un EXPERTO PROMPT ENGINEER especializado en crear prompts profesionales, 
extensos y altamente optimizados para herramientas de IA. Tu objetivo es generar el mejor 
PROMPT POSIBLE que el usuario pueda copiar-pegar directamente."""

    def _cargar_template_generacion(self) -> str:
        """
        Carga el GENERATION_TEMPLATE desde archivo externo
        
        Returns:
            Template para generación de prompts
        """
        ruta = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "generation_template.txt")

        try:
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            st.warning(f"⚠️ Error cargando generation_template.txt: {e}")

        # Fallback hardcodeado
        return """CREA UN PROMPT PROFESIONAL para: {herramienta}
INFORMACIÓN: {idea}
PARÁMETROS: {parametros}
DOCUMENTOS: {informacion_documentos}
Genera un prompt completo y optimizado."""

    def procesar_documentos(self, texto_documentos: str, motor: str, herramienta: str, idea: str) -> str:
        """
        Procesa documentos con ChatGPT para extraer información ACCIONABLE
        
        Args:
            texto_documentos: Texto combinado de documentos
            motor: Motor objetivo (Imagen, Texto, etc.)
            herramienta: Herramienta específica
            idea: Idea del usuario (para contextualizar la extracción)
            
        Returns:
            Información procesada extraída de documentos
        """
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

    def generar(self, datos: Dict) -> Dict:
        """
        Genera prompt profesional extenso
        
        Args:
            datos: Diccionario con:
                - motor: Motor objetivo
                - herramienta: Herramienta específica
                - idea: Descripción de la idea
                - parametros: Dict de parámetros seleccionados
                - documentos: Texto de documentos adjuntos
                - notas: Notas adicionales
                - idioma: Idioma solicitado
                - palabras_clave: Palabras clave seleccionadas
                
        Returns:
            Dict con:
                - exito: True/False
                - prompt: Prompt generado
                - info_documentos: Información extraída de docs
                - costo: Costo estimado
                - tiempo: Tiempo de generación
                - error: Mensaje de error si aplica
        """
        resultado = {
            "exito": False,
            "prompt": "",
            "info_documentos": "",
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
                info_documentos = "No hay documentos adjuntos. Genera el prompt basándote en la idea, parámetros y palabras clave del usuario."

            # PASO 2: Preparar parámetros
            params_texto = "\n".join(
                [f"  • {k.replace('_', ' ').title()}: {v}" for k, v in datos.get("parametros", {}).items()]
            )

            # PASO 3: Preparar palabras clave
            palabras_clave = datos.get("palabras_clave", "")
            if not palabras_clave:
                palabras_clave = "No se especificaron palabras clave"

            # PASO 4: Preparar notas
            notas = datos.get("notas", "")
            notas_seccion = f"NOTAS ADICIONALES DEL USUARIO:\n{notas}\n" if notas else "Sin notas adicionales."

            # PASO 5: Construir prompt para generar el PROMPT final
            prompt_usuario = self.template_generacion.format(
                herramienta=datos["herramienta"],
                motor=datos["motor"],
                idea=datos["idea"],
                parametros=params_texto,
                palabras_clave=palabras_clave,
                informacion_documentos=info_documentos,
                notas_seccion=notas_seccion,
                idioma=datos.get("idioma", "Español"),
            )

            # PASO 6: Llamar a ChatGPT para generar el PROMPT final
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
            resultado["costo"] = 0.015  # Aproximación para 2 llamadas

        except Exception as e:
            resultado["error"] = f"Error: {str(e)}"

        finally:
            resultado["tiempo"] = time.time() - inicio

        return resultado
