"""Compatibilidad: módulo `modules.authentication` que re-exporta la clase
`AuthenticationSystem` desde `modules.autenticacion`.

Algunos archivos (por ejemplo `app.py`) importan `modules.authentication` mientras
que el módulo fuente se llama `autenticacion.py`. Este shim evita errores
ModuleNotFoundError manteniendo compatibilidad de nombres.
"""
from .autenticacion import AuthenticationSystem

__all__ = ["AuthenticationSystem"]
