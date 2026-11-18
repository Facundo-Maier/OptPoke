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
para Shiny y Living. `NOT` indica OT ajeno, no captura; `EVO` marca «Por evolucionar» en la fila del objetivo (Alakazam si tenés Kadabra). No suma HOME: el Excel prevalece sobre el estado anterior: 0 pone un ejemplar en HOME; 1 y EVO ponen cero. NOT solo marca OT ajeno; no informa captura. Los objetivos ausentes del archivo no cambian. La marca puede editarse y filtrarse, y se retira al completar el objetivo.
La exportación JSON permite respaldar progreso; restaurar reemplaza los datos.
Guardá los respaldos y Excel fuera del repositorio.

Para actualizar: detener el servidor, ejecutar `git pull --ff-only`, instalar
`pip install -r requirements.txt` y volver a iniciarlo. No reemplazar la base ni
restaurar un respaldo antiguo. Antes de actualizar, exportar un respaldo propio.

## Auditoría de sprites (opcional)

Para comprobar las imágenes de tu caché local **sin acceder a Internet**:

```bash
node scripts/auditar_sprites.cjs --solo-especiales
```

Se generan informes CSV/JSON en `reportes_sprites/` (ignorados por Git).
`sin_comprobar` significa que todavía no se consultó una fuente, **no** que falte el sprite. Un archivo cacheado tampoco garantiza que su variante o color sea correcto.
La [guía de auditoría](docs/SPRITES.md) explica cómo revisar las formas y cómo ejecutar comprobaciones externas opcionales y limitadas mediante el servidor local.

## Flujo de ramas

Los cambios se implementan en **ramas nuevas creadas desde `develop`** y se proponen mediante PR hacia `develop`, con pruebas en la propia rama. Solo se integra `develop` en `main` para una versión probada y destinada a publicación; ver [Releases](docs/RELEASING.md).

La primera etapa de v0.2 convierte [Plan Bank en una TODO list editable](docs/BANK_TODO.md): se pueden crear, modificar y eliminar tareas, independientes de la Pokédex por defecto. Cada tarea puede vincularse explícitamente a un objetivo Shiny/Living; **el vínculo no sincroniza cantidades de HOME**.

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

