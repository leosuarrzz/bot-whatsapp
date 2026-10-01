"""Configuración común de los tests.

Ningún test toca la base real ni las APIs de Meta o Gemini: las variables
de entorno se pisan con valores de prueba antes de importar el código
(load_dotenv no sobrescribe variables que ya existen).
"""
import os
import sys
import types
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.update({
    "VERIFY_TOKEN": "token-de-prueba",
    "APP_SECRET": "secreto-de-prueba",
    "WHATSAPP_TOKEN": "whatsapp-de-prueba",
    "GOOGLE_API_KEY": "google-de-prueba",
    "DATABASE_URL": "postgresql://nadie@localhost:1/ninguna",
})

# Si psycopg no se puede cargar (por ejemplo, Windows bloquea su DLL),
# lo reemplazo por un módulo vacío: los tests nunca se conectan.
try:
    import psycopg  # noqa: F401
except ImportError:
    sys.modules["psycopg"] = types.ModuleType("psycopg")
