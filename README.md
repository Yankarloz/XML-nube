# XML-nube — CRUD SOAP con XML

Pequeña app SOAP (Spyne) con frontend estático para gestionar un archivo XML de productos.

URL pública (Deploy en Render):
- https://xml-nube.onrender.com

## Requisitos
- Python 3.11
- Git
- `pip` (gestor de paquetes)
- (Opcional) `gunicorn` para producción — ya está en `requirements.txt`.

## Instalación y ejecución (Windows - PowerShell)

1. Clona el repositorio:
```powershell
git clone https://github.com/Yankarloz/XML-nube.git
cd XML-nube
```

2. Crear y activar un entorno virtual (Python 3.11):
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

3. Instalar dependencias:
```powershell
pip install -r requirements.txt
```

4. Ejecutar en local (desarrollo):
```powershell
# $env:PORT=8000    # si quieres definir el puerto en PowerShell
py -3.11 app.py
```

5. Abrir en el navegador:
- Frontend: `http://127.0.0.1:8000/`
- WSDL (SOAP): `http://127.0.0.1:8000/soap?wsdl`

También puedes ejecutar en WSL/Linux o en producción con `gunicorn`:
```bash
gunicorn app:app --bind 0.0.0.0:8000
```

## Qué contiene el proyecto
- `app.py` — servidor WSGI con Spyne (SOAP) montado en `/soap` y frontend servido en `/`.
- `front/` — archivos estáticos: `index.html`, `app.js`, `style.css`.
- `xml/datos.xml` — archivo que almacena los productos (lectura/escritura).
- `requirements.txt`, `runtime.txt`, `Procfile` — configuración para deploy en Render.

## SOAP / Frontend
- El frontend realiza llamadas SOAP a: `window.location.origin + '/soap'`.
- El WSDL público (en Render) está en: `https://xml-nube.onrender.com/soap?wsdl`.

## Notas importantes
- `xml/datos.xml` se guarda en disco; en plataformas como Render los cambios en disco no son persistentes entre deploys. Para persistencia duradera usa una base de datos o almacenamiento externo.
- `lxml` (si está en `requirements.txt`) puede requerir ruedas binarios; si la instalación falla en Windows, instala las Build Tools o utiliza WSL.
- Concurrencia: escribir simultáneamente en el XML puede corromperlo. Para producción usa DB o mecanismos de bloqueo.

## Diagrama del árbol XML (`xml/datos.xml`)

```
<?xml version="1.0" encoding="utf-8"?>
<productos>
  <producto id="1">
    <nombre>Computador</nombre>
    <precio>2500</precio>
    <cantidad>5</cantidad>
  </producto>
  <producto id="2">
    <nombre>Mouse</nombre>
    <precio>50</precio>
    <cantidad>100</cantidad>
  </producto>
  ...
</productos>
```

Estructura por nodo `producto`:
- Atributo: `id` (entero, string en XML)
- Hijos:
  - `nombre` (string)
  - `precio` (número en texto)
  - `cantidad` (número en texto)

