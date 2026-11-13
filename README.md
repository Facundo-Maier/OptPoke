# Opt. Poke

Organizador local de Living Shiny Dex, objetivos Bank y cacerías.
Python 3.11+ y navegador; FastAPI, SQLite y JavaScript sin compilación.
Versión de desarrollo: **0.1.99**. Shiny Dex y Living Dex son las secciones
funcionales verificadas. Bank, Cacerías, Comparador y otras herramientas son
provisionales: contienen bases de implementación o placeholders y todavía
no se presentan como funciones completas.

## Instalación

```bash
git clone https://github.com/Facundo-Maier/OptPoke.git
cd OptPoke
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000. En PowerShell, activar con
`.venv\Scripts\Activate.ps1` y usar `python` en lugar de `python3`.
La base personal se conserva en `~/.optpoke/optpoke.db` o en `OPTPOKE_DATA_DIR`.
No se importa progreso automáticamente. Servicio local, sin autenticación:
no exponer el puerto a Internet.

## Demo ficticia

Con las dependencias instaladas:

```bash
python -m app.demo
```

Abrir http://127.0.0.1:8001. Incluye ejemplos inventados de colección, Bank y
cacerías, y un aviso visible de DEMO. Cada ejecución usa una carpeta temporal
nueva, incluso si `OPTPOKE_DATA_DIR` estaba configurado. Nunca lee la base
personal; al cerrar normalmente se eliminan los datos temporales. Para reiniciar
los ejemplos, cerrar con Ctrl+C y volver a ejecutar. No importar datos personales
en una sesión que se vaya a mostrar a otras personas.

## Progreso y actualización

Importación XLSX desde Configuración, con vista previa y confirmación separada
para Shiny y Living. `NOT` indica OT ajeno, no captura; `EVO` se advierte y omite.
La exportación JSON permite respaldar progreso; restaurar reemplaza los datos.
Guardá los respaldos y Excel fuera del repositorio.

Para actualizar: detener el servidor, ejecutar `git pull --ff-only`, instalar
`pip install -r requirements.txt` y volver a iniciarlo. No reemplazar la base ni
restaurar un respaldo antiguo. Antes de actualizar, exportar un respaldo propio.

## Desarrollo

```bash
pip install -r requirements-dev.txt
pytest -q
node --test tests/test_*.cjs
python scripts/check_public.py
```

Node 22 para las pruebas JavaScript. Los tests habituales usan datos sintéticos;
no se necesitan archivos personales para ejecutar la suite.
CI ejecuta las pruebas en Python 3.11 y 3.12 y revisa los archivos versionados.
No hay bundle frontend que compilar: HTML, CSS y JS se sirven directamente.

## Publicación y licencia

- [Proceso de releases y SemVer](docs/RELEASING.md)
- [Cambios](CHANGELOG.md) y [roadmap](docs/ROADMAP.md)
- Código propio: **MIT**, Copyright (c) 2026 Facundo Maier. Conservar LICENSE.
- [Atribuciones y condiciones de terceros](THIRD_PARTY_NOTICES.md).

Las distribuciones no incluyen bases personales, respaldos, Excel ni sprites.
