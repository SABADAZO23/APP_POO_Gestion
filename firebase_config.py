import os
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore, auth

logger = logging.getLogger(__name__)


def initialize_firebase() -> firebase_admin.App:
    """Inicializa la conexión con Firebase usando credenciales de cuenta de servicio.

    Busca la ruta de las credenciales en la variable de entorno
    'FIREBASE_CREDENTIALS' o 'GOOGLE_APPLICATION_CREDENTIALS'. Si ninguna está
    definida, utilizará 'ServiceAccountKey.json' en el directorio del proyecto.

    Devuelve la instancia de `firebase_admin.App` si la inicialización es exitosa.
    Lanza RuntimeError si no puede inicializarse.
    """
    cred_path = (
        os.environ.get("FIREBASE_CREDENTIALS")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or "ServiceAccountKey.json"
    )

    try:
        # Usar la API pública para comprobar si ya existe una app
        try:
            app = firebase_admin.get_app()
            logger.debug("Firebase ya estaba inicializado.")
            return app
        except ValueError:
            # No existe -> inicializar
            if not os.path.exists(cred_path):
                msg = (
                    f"Credenciales de Firebase no encontradas en '{cred_path}'. "
                    "Defina FIREBASE_CREDENTIALS o GOOGLE_APPLICATION_CREDENTIALS."
                )
                logger.error(msg)
                raise RuntimeError(msg)

            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred)
            logger.info("Firebase inicializado correctamente usando: %s", cred_path)
            return app
    except Exception as e:
        logger.exception("Error iniciando Firebase: %s", e)
        raise


def get_firestore_client():
    """Devuelve una instancia del cliente Firestore asegurando que Firebase esté inicializado."""
    initialize_firebase()
    return firestore.client()


def get_auth_client():
    """Devuelve el módulo de autenticación de Firebase (requiere inicialización)."""
    initialize_firebase()
    return auth
