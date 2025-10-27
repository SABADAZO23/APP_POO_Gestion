import base64
import logging
import os
from typing import Any, Dict, List, Optional

import streamlit as st

from firebase_config import get_firestore_client

logger = logging.getLogger(__name__)
db = get_firestore_client()

# Valores por defecto del tema según la paleta proporcionada por el usuario
# Background: #F2F1D9, Texto: #212A3E, Contraste: #F28C4F
DEFAULT_PALETTE = [
    '#212A3E',
    '#59788E',
    '#F28C4F',
    '#F2F1D9',
    '#44A4AA',
    '#FFFFFF',
]
DEFAULT_DARK = False

# Intentaremos usar un logo local si existe en assets/logo.png; si no, usamos un pequeño placeholder.
DEFAULT_LOGO_PATHS = [
    os.path.join(os.getcwd(), 'assets', 'logo.png'),
    os.path.join(os.getcwd(), 'assets', 'logo.jpg'),
    os.path.join(os.getcwd(), 'logo.png'),
    os.path.join(os.getcwd(), 'logo.jpg'),
]

DEFAULT_LOGO_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA'
    'A2QkAAAAAElFTkSuQmCC'
)


def save_theme(store_id: str, palette: List[str], dark_mode: bool, logo_bytes: Optional[bytes] = None) -> bool:
    """Guarda la paleta y opciones de tema en Firestore bajo collection `settings` document store_id."""
    try:
        data: Dict[str, Any] = {'palette': palette[:6], 'dark_mode': bool(dark_mode)}
        if logo_bytes:
            data['logo_b64'] = base64.b64encode(logo_bytes).decode('utf-8')
        db.collection('settings').document(store_id).set(data, merge=True)
        return True
    except Exception as e:
        logger.exception("Error guardando tema: %s", e)
        return False


def load_theme(store_id: str) -> Dict[str, Any]:
    """Carga el tema guardado para la tienda. Si no existe, devuelve los valores por defecto.

    Devuelve siempre un dict con al menos 'palette' y 'dark_mode' y opcionalmente 'logo_b64'.
    """
    try:
        doc = db.collection('settings').document(store_id).get()
        if doc.exists:
            data = doc.to_dict()
            # Normalizar y rellenar con defaults si faltan campos
            palette = data.get('palette') or DEFAULT_PALETTE
            dark = data.get('dark_mode') if 'dark_mode' in data else DEFAULT_DARK
            logo = data.get('logo_b64') if data.get('logo_b64') else None
            # Si no hay logo en Firestore, intentar leer un logo local
            if not logo:
                for p in DEFAULT_LOGO_PATHS:
                    if os.path.exists(p):
                        try:
                            with open(p, 'rb') as f:
                                logo = base64.b64encode(f.read()).decode('utf-8')
                                break
                        except Exception:
                            logger.exception("No se pudo leer logo local desde %s", p)
            if not logo:
                logo = DEFAULT_LOGO_B64
            return {'palette': palette[:6], 'dark_mode': bool(dark), 'logo_b64': logo}
        # si no existe documento, intentar cargar logo local o devolver defaults
        logo = None
        for p in DEFAULT_LOGO_PATHS:
            if os.path.exists(p):
                try:
                    with open(p, 'rb') as f:
                        logo = base64.b64encode(f.read()).decode('utf-8')
                        break
                except Exception:
                    logger.exception("No se pudo leer logo local desde %s", p)
        if not logo:
            logo = DEFAULT_LOGO_B64
        return {'palette': DEFAULT_PALETTE, 'dark_mode': DEFAULT_DARK, 'logo_b64': logo}
    except Exception as e:
        logger.exception("Error cargando tema: %s", e)
        return {'palette': DEFAULT_PALETTE, 'dark_mode': DEFAULT_DARK, 'logo_b64': DEFAULT_LOGO_B64}


def apply_theme(theme: Optional[Dict[str, Any]] = None):
    """Inyecta CSS simple en la app Streamlit usando la paleta.

    Si `theme` es None, se aplican los valores por defecto.
    """
    if theme is None:
        theme = {'palette': DEFAULT_PALETTE, 'dark_mode': DEFAULT_DARK, 'logo_b64': DEFAULT_LOGO_B64}

    palette = (theme.get('palette') or DEFAULT_PALETTE)[:6]
    dark = bool(theme.get('dark_mode', DEFAULT_DARK))
    logo_b64 = theme.get('logo_b64') or DEFAULT_LOGO_B64

    # Construir variables CSS
    css_vars = []
    for i, c in enumerate(palette, start=1):
        css_vars.append(f"--color{i}: {c};")

    background = "#121212" if dark else "#FFFFFF"
    text = "#FFFFFF" if dark else "#000000"
    css_vars.append(f"--background: {background};")
    css_vars.append(f"--text: {text};")

    css = ":root {" + " ".join(css_vars) + "}"

    # Estilos básicos para elementos comunes
    css += r"""
    .stApp { background-color: var(--background) !important; color: var(--text) !important; }
    .stApp .stButton>button { background-color: var(--color1) !important; color: var(--text) !important; }
    .stSidebar { background-color: var(--background) !important; }
    .stMarkdown, .stText, .stHeader, .stBetaContainer { color: var(--text) !important; }
    img.theme-logo { max-height: 80px; }
    """

    # Additional styling for landing and login to match the provided palette
    css += r"""
    /* Top-left fixed logo */
    .top-left-logo {
        position: fixed;
        left: 16px;
        top: 12px;
        z-index: 9999;
        max-height: 56px;
    }

    /* Landing styles */
    .landing-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 40px;
        padding-bottom: 40px;
    }
    .landing-hero {
        max-width: 720px;
        text-align: center;
        color: var(--color1);
    }
    .landing-hero h1 { font-size: 42px; color: var(--color3); margin-top: 20px; }
    .landing-hero p { font-size: 20px; color: var(--color2); }

    /* Login card */
    .login-card {
        background: rgba(255,255,255,0.6);
        border-radius: 20px;
        padding: 24px;
        max-width: 520px;
        margin: 24px auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    input[type="text"], input[type="password"] {
        background: #FDF7EA; /* light input bg */
        border-radius: 28px !important;
        padding: 12px 18px !important;
        border: 2px solid rgba(33,42,62,0.08) !important;
        color: var(--text) !important;
    }

    .stButton>button {
        border-radius: 28px !important;
        padding: 10px 24px !important;
        background: var(--color3) !important;
        color: white !important;
        font-weight: 600;
    }
    """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # Guardar logo en session_state para mostrarlo desde UI cuando se necesite
    if logo_b64:
        st.session_state['theme_logo'] = f"data:image/png;base64,{logo_b64}"
