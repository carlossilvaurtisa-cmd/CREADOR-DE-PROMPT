"""
rate_limiter.py - Control de límite de prompts por sesión
"""

import streamlit as st
from datetime import datetime


class SessionRateLimiter:
    """Gestor de límite de prompts por sesión"""

    def __init__(self, limite_por_sesion: int = 30):
        """
        Inicializa el rate limiter
        
        Args:
            limite_por_sesion: Número máximo de prompts por sesión (default: 30)
        """
        self.limite = limite_por_sesion
        self._inicializar_session_state()

    def _inicializar_session_state(self) -> None:
        """Inicializa contadores en session_state si no existen"""
        if "prompts_generados" not in st.session_state:
            st.session_state.prompts_generados = 0
        if "timestamp_inicio_sesion" not in st.session_state:
            st.session_state.timestamp_inicio_sesion = datetime.now()

    def obtener_contador(self) -> int:
        """
        Obtiene el contador actual de prompts generados
        
        Returns:
            Número de prompts generados en esta sesión
        """
        return st.session_state.get("prompts_generados", 0)

    def obtener_restantes(self) -> int:
        """
        Obtiene cuántos prompts faltan para alcanzar el límite
        
        Returns:
            Número de prompts restantes
        """
        return max(0, self.limite - self.obtener_contador())

    def puede_generar(self) -> bool:
        """
        Verifica si se puede generar otro prompt
        
        Returns:
            True si hay prompts disponibles, False si se alcanzó el límite
        """
        return self.obtener_contador() < self.limite

    def incrementar(self) -> None:
        """Incrementa el contador de prompts generados"""
        st.session_state.prompts_generados += 1

    def obtener_progreso_porcentaje(self) -> int:
        """
        Obtiene el porcentaje de uso del límite
        
        Returns:
            Porcentaje de 0 a 100
        """
        if self.limite == 0:
            return 0
        return min(100, int((self.obtener_contador() / self.limite) * 100))

    def mostrar_widget_streamlit(self) -> None:
        """Muestra un widget de progreso en Streamlit"""
        contador = self.obtener_contador()
        restantes = self.obtener_restantes()
        porcentaje = self.obtener_progreso_porcentaje()

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.progress(porcentaje / 100, text=f"Límite de prompts por sesión")

        with col2:
            st.metric("Generados", f"{contador}/{self.limite}")

        with col3:
            if restantes > 0:
                st.success(f"✅ {restantes} restantes", help="Prompts disponibles en esta sesión")
            else:
                st.error("❌ Límite alcanzado", help="Se alcanzó el límite de prompts por sesión")

    def reiniciar_contador(self) -> None:
        """Reinicia el contador (uso administrativo)"""
        st.session_state.prompts_generados = 0
        st.session_state.timestamp_inicio_sesion = datetime.now()
