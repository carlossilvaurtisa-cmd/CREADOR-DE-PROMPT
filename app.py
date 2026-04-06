#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CREADOR DE PROMPTS v3.0 - CON AUTENTICACIÓN
Acceso únicamente para usuarios autorizados de GIRO
"""

import streamlit as st
import os
from wizard_creator import mostrar_wizard_streamlit

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Creador de Prompts - GIRO",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .main { 
        max-width: 800px; 
        margin: 0 auto;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SISTEMA DE AUTENTICACIÓN
# ============================================================================

def mostrar_login():
    """Pantalla de login"""
    
    st.markdown("""
    # 🔐 Creador de Prompts
    ### GIRO - Herramienta Profesional
    """)
    
    st.markdown("---")
    
    with st.form("login_form"):
        usuario = st.text_input("👤 Usuario", placeholder="nombre de usuario")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="contraseña")
        submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
    
    if submit:
        # Obtener credenciales desde variables de ambiente
        USUARIO_CORRECTO = os.getenv("APP_USERNAME", "giro")
        PASSWORD_CORRECTO = os.getenv("APP_PASSWORD", "giro2024")
        
        if usuario == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
            st.session_state.autenticado = True
            st.success("✅ Bienvenido a Creador de Prompts")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    
    st.markdown("---")
    st.info("💡 Contacta al administrador si olvidaste tus credenciales")

# ============================================================================
# PANTALLA PRINCIPAL (Solo si está autenticado)
# ============================================================================

def mostrar_app_principal():
    """Pantalla principal de la app"""
    
    # Botón logout en la barra lateral
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown("""
        # ✨ Creador de Prompts
        ### Crea prompts profesionales para IA
        """)
    
    with col2:
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
    
    st.markdown("---")
    
    # Información inicial
    if "mostrar_info" not in st.session_state:
        st.session_state.mostrar_info = True
    
    if st.session_state.mostrar_info and st.session_state.get("paso_wizard", 1) == 1:
        with st.expander("📖 ¿Cómo funciona?", expanded=True):
            st.markdown("""
            ### 5 Pasos simples:
            
            1. **Motor objetivo** - ¿Para qué? (Imagen, Texto, Música, Audio, Video, Archivos)
            2. **Herramienta** - ¿Cuál? (Midjourney, ChatGPT, Suno, etc.)
            3. **Tu idea** - Describe sin tecnicismos
            4. **Parámetros + Documentos** - Estilos, parámetros, y opcionalmente sube documentos
            5. **ChatGPT genera** - Obtén tu prompt optimizado

            ### Características:
            - 🤖 Motor: 100% ChatGPT
            - 📎 Adjunta documentos (PDF, TXT, DOCX, imágenes)
            - ⚡ Súper rápido: ~2 minutos
            - 💰 API centralizada de GIRO
            """)
    
    st.markdown("")
    
    # WIZARD PRINCIPAL
    mostrar_wizard_streamlit()
    
    # FOOTER
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>✨ GIRO</p>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>Potenciado por ChatGPT</p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>v3.0</p>", unsafe_allow_html=True)
    
    with st.expander("🔒 Privacidad"):
        st.markdown("""
        - 🔐 Acceso restringido: Solo usuarios autorizados
        - 🛡️ API key: Centralizada y segura
        - 📊 Tus prompts: Generados con ChatGPT
        - 🚫 Sin tracking: No recopilamos datos personales
        """)

# ============================================================================
# LÓGICA PRINCIPAL
# ============================================================================

# Inicializar estado de autenticación
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Mostrar login o app según autenticación
if not st.session_state.autenticado:
    mostrar_login()
else:
    mostrar_app_principal()
