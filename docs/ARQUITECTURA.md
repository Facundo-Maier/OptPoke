# Estructura técnica actual — Opt. Poke

Este documento describe cómo está organizado `develop` actualmente. La [arquitectura propuesta](ARQUITECTURA_PROPUESTA.md) se revisa por separado; las decisiones de producto pendientes viven en [ROADMAP.md](ROADMAP.md) y las instrucciones de uso en [MANUAL_USUARIO.md](MANUAL_USUARIO.md).

## Recorrido de los datos

El navegador carga HTML, CSS y JavaScript desde el servidor local FastAPI. La interfaz llama a `/api/...`; el servidor valida las operaciones y guarda el progreso en SQLite. El catálogo versionado se lee desde `data/` y se incorpora sin sobrescribir los objetivos personales. Las imágenes se solicitan bajo demanda a fuentes permitidas y se guardan en una caché local.

No hay cuentas ni sincronización con servicios externos. La base SQLite y la caché viven en `~/.optpoke/` o en `OPTPOKE_DATA_DIR`, fuera del repositorio. `app/demo.py` usa una carpeta temporal separada de los datos personales.

## Responsabilidades actuales

| Ruta | Responsabilidad |
| --- | --- |
| `app/main.py` | Crea la aplicación FastAPI; contiene rutas, validaciones y operaciones de Pokédex, Bank, cacerías, juegos, importación y respaldos. |
| `app/db.py` | Conexión y transacciones SQLite, esquema, migraciones aditivas e inicialización del catálogo. |
| `app/austin_import.py`, `app/importers.py`, `app/xlsx.py`, `app/cli.py` | Vista previa y aplicación de importaciones AustinJohn, importaciones originales, lectura XLSX sin ejecutar fórmulas y CLI. |
| `app/bank_links.py`, `app/math_utils.py` | Normalización de vínculos Bank y probabilidad acumulada de intentos independientes. |
| `app/sprite_cache.py` | Validación de fuentes, descarga bajo demanda, caché y modo sin conexión. |
| `static/index.html`, `static/app.js`, `static/dex-list.js`, `static/sprites.js`, `static/styles.css` | Interfaz servida directamente; navegación, pantallas, lista Pokédex, resolución de sprites y estilos. |
| `data/` | Catálogo factual y bloqueos shiny iniciales; no contiene el progreso del usuario. |
| `tests/`, `scripts/`, `.github/workflows/` | Pruebas, auditoría de sprites, controles de publicación y automatización de CI/release. |

## Persistencia y compatibilidad

`app/db.py` aplica migraciones aditivas al iniciar y conserva los datos de instalaciones anteriores. La exportación y restauración JSON se implementan en `app/main.py`; la importación AustinJohn separa la vista previa de la aplicación de cambios. Los aportes Bank → HOME se calculan al modificar tareas u objetivos vinculados; no se leen partidas ni Pokémon HOME. Las reglas visibles para el usuario se explican en el [manual](MANUAL_USUARIO.md).

## Límites estructurales actuales

`app/main.py` concentra rutas, reglas y SQL; `static/app.js` concentra la mayoría de las pantallas; `static/styles.css` reúne estilos base y ajustes posteriores. `app/db.py` combina inicialización y migraciones. Estos son puntos a evaluar en la futura reorganización; este documento registra el estado presente.
