# Proyecto — Gestor de inventario y empleados

Este repositorio contiene una aplicación pequeña construida con Streamlit y Firestore (firebase-admin) para gestionar productos, inventario, movimientos e empleados. Incluye soporte para temas por tienda (paleta de colores y logo) y un panel sencillo para propietarios y empleados.

## Contenido
- `app.py` — entrada principal de Streamlit
- `modules/` — lógica del negocio (auth, products, employees, stores, theme)
- `dashboards/` — dashboards para owner/employee
- `tools/set_store_theme.py` — script para subir logo/paleta a Firestore
- `assets/` — carpeta local para logo (puede contener `logo.png` o `logo.jpg`)

## Requisitos
- Python 3.11 (probado)
- `requirimientos.txt` contiene las dependencias principales:

```
streamlit==1.28.0
firebase-admin==6.2.0
```

Notas:
- `firebase-admin` incluye el cliente de Firestore que usa la app.
- Si quieres usar variables de entorno desde un archivo `.env`, instala opcionalmente `python-dotenv`.

## Preparar entorno (Windows PowerShell)

1. Abrir PowerShell en la carpeta del proyecto (ej. `C:\Users\Biblio\Documents\Proyecto`).
2. Crear y activar un entorno virtual:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirimientos.txt
```

3. Proveer credenciales de Firebase (una de estas opciones):

- Opción A (más segura en producción): exporta la variable de entorno apuntando al JSON del Service Account:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\ServiceAccountKey.json"
# o alternativamente
$env:FIREBASE_CREDENTIALS = "C:\path\to\ServiceAccountKey.json"
```

- Opción B (rápido en local): coloca `ServiceAccountKey.json` en la raíz del proyecto (NO lo subas a git). El repositorio ya contiene una entrada `.gitignore` para evitar subirlo.

4. (Opcional) Si usas la consola de GCP/Firebase asegúrate de que la cuenta tenga permisos para Firestore.

## Ejecutar la app

Con el entorno activado y credenciales configuradas, ejecuta:

```powershell
# Desde la raíz del proyecto
streamlit run app.py
```

Luego abre el navegador en la URL que Streamlit muestre (usualmente `http://localhost:8501`).

## Subir logo y paleta a Firestore (por tienda)

Si quieres que el logo y la paleta se apliquen a todos los usuarios de una tienda, guárdalos en Firestore `settings/{store_id}`. Hay dos modos:

1) Usar la UI de propietario dentro de la app (pestaña Tema) — requiere iniciar sesión como propietario de la tienda.

2) Usar el script que incluimos (útil desde la terminal):

```powershell
python tools\set_store_theme.py --store-id STORE_ID --logo-path "C:\Users\Biblio\Documents\logo.jpg" --palette "#212A3E,#59788E,#F28C4F,#F2F1D9,#44A4AA,#FFFFFF" --dark
```

- `--palette` es opcional; si no se pasa se usa la paleta por defecto definida en `modules/theme.py`.
- `--dark` es un flag opcional para activar el modo oscuro.

## Cambiar logo y colores localmente (rápido)

- Para cambiar el logo localmente, copia tu archivo a `assets/logo.png` o `assets/logo.jpg`. La app busca `assets/logo.*` si no hay `logo_b64` en Firestore.

```powershell
Copy-Item "C:\Users\Biblio\Documents\logo.jpg" -Destination .\assets\logo.jpg -Force
```

- Para cambiar la paleta por defecto, edita `modules/theme.py` y modifica la lista `DEFAULT_PALETTE` (hasta 6 colores hex). También puedes cambiar `DEFAULT_DARK`.

Si quieres cambiar la apariencia (tamaño del logo, bordes, posición), edita la función `apply_theme()` en `modules/theme.py` y modifica las reglas CSS bajo `css += r""" ... """`. Clases a editar:

- `.top-left-logo` — posición y margen del logo.
- `img.theme-logo` — controlar `max-height`.
- `.login-card` / `.landing-hero` — estilos de la landing/login.

Ejemplo: para hacer el logo circular y 64px:

```css
img.theme-logo { max-height: 64px; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
.top-left-logo { top: 8px; left: 12px; }
```

Coloca esas líneas dentro del bloque CSS en `apply_theme()` y recarga Streamlit.

## Troubleshooting rápido
- Error de import `modules.authentication`: se añadió un shim `modules/authentication.py` que reexporta la implementación existente.
- Si ves un error Firestore `FailedPrecondition: index required` al consultar movimientos, crea el índice compuesto en la consola de Firebase (consulta sobre `store_id` + orden por `timestamp`), o usa la solución de subcolección `stores/{store_id}/movements` (la app ya intenta un fallback cuando falta el índice).
- Si la app no carga el logo tras copiarlo a `assets/`, recarga el navegador o reinicia Streamlit.

## Seguridad y recomendaciones
- No subas `ServiceAccountKey.json` ni credenciales al repositorio. Usa variables de entorno en producción.
- Actualmente la app registra contraseñas en Firestore en texto plano (funcionalidad simple para demo). Para producción usa Firebase Authentication o guarda contraseñas hasheadas.
- Considera mover los logos a Firebase Storage si vas a alojar muchas imágenes; hoy se guardan como base64 en Firestore para simplicidad.

## Desarrollo
- Archivos principales a editar para cambios funcionales:
  - `modules/products.py` — lógica de productos/inventario/movimientos
  - `modules/employees.py` — gestión de empleados
  - `modules/theme.py` — estilos/paleta/logo
  - `dashboards/owner_dashboard.py` — UI del propietario


---
Fecha: 2025-10-27

