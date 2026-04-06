"""
document_processor.py - Extracción de contenido de documentos con fallbacks
"""

import base64
import io
from typing import Optional, Tuple
from pathlib import Path
import streamlit as st


class DocumentProcessor:
    """Procesador de documentos con soporte para múltiples formatos"""

    # Límites de seguridad
    MAX_CARACTERES_POR_DOCUMENTO = 50_000
    MAX_DOCUMENTOS_SIMULTANEOS = 10

    def __init__(self, cliente_openai=None):
        """
        Inicializa el procesador de documentos
        
        Args:
            cliente_openai: Cliente OpenAI para vision (opcional)
        """
        self.cliente = cliente_openai
        
        # Si no se proporciona cliente, intentar crear uno
        if self.cliente is None:
            try:
                import os
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.cliente = OpenAI(api_key=api_key)
            except Exception:
                pass

    def procesar_archivos(self, archivos_streamlit: list) -> str:
        """
        Procesa múltiples archivos y retorna texto combinado
        
        Args:
            archivos_streamlit: Lista de objetos de archivo de Streamlit
            
        Returns:
            Texto combinado de todos los documentos
        """
        if not archivos_streamlit:
            return ""

        if len(archivos_streamlit) > self.MAX_DOCUMENTOS_SIMULTANEOS:
            st.warning(f"⚠️ Máximo {self.MAX_DOCUMENTOS_SIMULTANEOS} documentos a la vez")
            archivos_streamlit = archivos_streamlit[:self.MAX_DOCUMENTOS_SIMULTANEOS]

        texto_combinado = ""

        for archivo in archivos_streamlit:
            try:
                contenido = self._procesar_archivo_individual(archivo)
                if contenido:
                    texto_combinado += contenido
            except Exception as e:
                st.warning(f"⚠️ Error procesando {archivo.name}: {str(e)}")

        # Limitar caracteres totales
        if len(texto_combinado) > self.MAX_CARACTERES_POR_DOCUMENTO:
            texto_combinado = texto_combinado[:self.MAX_CARACTERES_POR_DOCUMENTO]
            st.info(f"📌 Documentos truncados a {self.MAX_CARACTERES_POR_DOCUMENTO} caracteres")

        return texto_combinado

    def _procesar_archivo_individual(self, archivo) -> str:
        """
        Procesa un archivo individual según su tipo
        
        Args:
            archivo: Objeto de archivo de Streamlit
            
        Returns:
            Contenido extraído del archivo
        """
        mime_type = archivo.type
        contenido = f"\n--- Archivo: {archivo.name} ---\n"

        if mime_type == "text/plain":
            contenido += self._procesar_txt(archivo)
        elif mime_type == "application/pdf":
            contenido += self._procesar_pdf(archivo)
        elif "word" in mime_type or "wordprocessingml" in mime_type:
            contenido += self._procesar_docx(archivo)
        elif mime_type in ["image/png", "image/jpeg", "image/jpg"]:
            contenido += self._procesar_imagen(archivo)
        else:
            contenido += f"[Formato no soportado: {mime_type}]"

        return contenido

    def _procesar_txt(self, archivo) -> str:
        """Procesa archivos de texto plano"""
        try:
            return archivo.read().decode("utf-8")
        except UnicodeDecodeError:
            return "[No se pudo decodificar el archivo TXT]"

    def _procesar_pdf(self, archivo) -> str:
        """
        Procesa PDFs con fallback a visión si falla extracción de texto
        """
        contenido = ""

        # Intentar con PyPDF2 primero
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(archivo)
            for page_num, page in enumerate(pdf_reader.pages[:10], 1):
                texto = page.extract_text()
                if texto.strip():
                    contenido += f"\n[Página {page_num}]\n{texto}\n"

            if contenido.strip():
                return contenido
        except Exception:
            pass

        # Fallback: intentar con pdfplumber
        try:
            import pdfplumber
            archivo.seek(0)
            with pdfplumber.open(archivo) as pdf:
                for page_num, page in enumerate(pdf.pages[:10], 1):
                    texto = page.extract_text()
                    if texto.strip():
                        contenido += f"\n[Página {page_num}]\n{texto}\n"

            if contenido.strip():
                return contenido
        except Exception:
            pass

        # Fallback final: si es PDF escaneado, usar visión de GPT-4
        if self.cliente and contenido == "":
            return self._procesar_pdf_con_vision(archivo)

        return "[No se pudo extraer texto del PDF. Intenta convertirlo a imágenes.]"

    def _procesar_pdf_con_vision(self, archivo) -> str:
        """
        Procesa PDF escaneado usando visión de GPT-4o-mini
        """
        try:
            import PyPDF2
            from pdf2image import convert_from_bytes

            # Convertir PDF a imágenes
            archivo.seek(0)
            imagenes = convert_from_bytes(archivo.read())

            contenido = "[PDF escaneado - procesado con visión]\n"

            for idx, imagen in enumerate(imagenes[:5], 1):
                # Convertir imagen a base64
                buffered = io.BytesIO()
                imagen.save(buffered, format="PNG")
                base64_image = base64.b64encode(buffered.getvalue()).decode()

                # Enviar a GPT-4 vision
                try:
                    response = self.cliente.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                                    },
                                    {"type": "text", "text": "Extrae y resume el contenido de texto visible en esta imagen."},
                                ],
                            }
                        ],
                        max_tokens=500,
                    )
                    contenido += f"\n[Página {idx}]\n{response.choices[0].message.content}\n"
                except Exception as e:
                    contenido += f"\n[Error en página {idx}: {str(e)}]\n"

            return contenido
        except ImportError:
            return "[pdf2image no instalado. Instala con: pip install pdf2image]"
        except Exception as e:
            return f"[Error procesando PDF con visión: {str(e)}]"

    def _procesar_docx(self, archivo) -> str:
        """Procesa archivos DOCX"""
        try:
            from docx import Document
            doc = Document(archivo)
            contenido = ""
            for parrafo in doc.paragraphs[:50]:
                if parrafo.text.strip():
                    contenido += parrafo.text + "\n"
            return contenido if contenido else "[DOCX vacío]"
        except ImportError:
            return "[python-docx no instalado]"
        except Exception as e:
            return f"[Error leyendo DOCX: {str(e)}]"

    def _procesar_imagen(self, archivo) -> str:
        """
        Procesa imágenes usando visión de GPT-4o-mini
        """
        if not self.cliente:
            return "[Imagen adjunta como referencia visual]"

        try:
            archivo.seek(0)
            base64_image = base64.b64encode(archivo.read()).decode()

            response = self.cliente.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/{archivo.type.split('/')[-1]};base64,{base64_image}"},
                            },
                            {
                                "type": "text",
                                "text": "Describe brevemente el contenido y elementos visibles en esta imagen. Sé conciso.",
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            return f"[Análisis de imagen]\n{response.choices[0].message.content}"
        except Exception as e:
            return f"[Imagen adjunta - Error en análisis: {str(e)}]"

    @staticmethod
    def obtener_tamano_mb(archivo) -> float:
        """Obtiene el tamaño del archivo en MB"""
        archivo.seek(0, 2)
        tamaño_bytes = archivo.tell()
        archivo.seek(0)
        return tamaño_bytes / (1024 * 1024)
