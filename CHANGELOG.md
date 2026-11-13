## Sin publicar

- Demo ficticia temporal y aislada del progreso personal.
- CI ampliado y releases en borrador con etiquetas SemVer y checksums.
- Licencia MIT, atribuciones y copia pública sin respaldos ni capturas heredadas.

## 0.1.99 — 2026-11-13

### Mantenimiento antes de v0.2: paginación por rangos e importación actualizada

- El selector directo muestra página y rango de resultados filtrados (por ejemplo `2 · 73–144`).
- Soporte para los dos **archivos separados** de AustinJohn con selectores, vistas previas y confirmaciones independientes.
- Lectura automática de `S-LivingFormLITE` (shiny) y `LivingFormLITE` (normal), sin requerir ambas hojas en el mismo Excel; se conserva compatibilidad con la plantilla anterior.
- `NOT` continúa significando **No OT**, nunca un resultado de posesión. `EVO` se advierte y se omite sin tocar el progreso.
- Se ignoran separadores `Gen` y se incorpora Floette Eternal Flower, presente en ambas planillas actualizadas, al catálogo (1.214 shiny, 1.284 normales).
- Probados ambos archivos reales de AustinJohn con un directorio de datos aislado, sin alterar la colección local. Documentación, pruebas y capturas de paginación/importación actualizadas.
- No se incluyen hojas de progreso personales en el proyecto publicable ni se altera la base de datos existente al actualizar el código.

## 0.1.9 — 2026-11-13

### Navegación directa, animación ligera e importación segura desde AustinJohn

- Selector de página en Shiny/Living Dex (además de Anterior y Siguiente).
- Movimiento suave (solo sprite ampliado seleccionado, animación CSS de `transform`), respeta `prefers-reduced-motion`.
- Importación local del XLSX actualizado de AustinJohn (hojas `S-LivingFormLITE` y `LivingFormLITE`) con vista previa y confirmación; compara por especie, forma, número y keyword, sin depender del orden de filas.
- Interpretación confirmada: `NOT` significa **No OT**, no "no aplicable" ni "obtenido"; únicamente activa el indicador OT ajeno y no modifica HOME.
- `0` significa al menos un ejemplar: no completa automáticamente objetivos de varias copias. `1` puede preservar progreso local o restablecer a pendiente si se elige explícitamente el modo de igualación.
- Ningún progreso personal se incluye en el código publicable. No se modifica el Excel original ni las tareas Bank y cacerías.
- Pruebas de interpretación NOT, preservación de cantidades y particularidades de formas; documentación y capturas actualizadas.

# Historial de cambios

## 0.1.8 — 2026-11-12

### Panel izquierdo persistente y presentación más plana

- El panel del sprite ampliado se fija debajo de la cabecera persistente durante el desplazamiento de Shiny Dex y Living Dex.
- La altura de la cabecera se mide mediante `ResizeObserver` para evitar superposiciones al cambiar el tamaño de ventana o zoom; se desconecta al cambiar de sección.
- Menos apariencia de tarjetas: se eliminan contenedores y fondos extra, se conservan divisores de filas y selección lima, y los paneles auxiliares usan separadores discretos.
- Sin cambios en SQLite, las cantidades, los candados, el OT, las cacerías, la API ni el sistema de sprites.
- Capturas actualizadas y verificaciones de desplazamiento (escritorio y vista estrecha), pruebas de estructura de interfaz y regresión.


## 0.1.7 — 2026-11-12

### Navegación de Pokédex con cabecera persistente

- Título de Pokédex Nacional, progreso, búsqueda y filtros fijos arriba mediante `position: sticky`, sin scroll interior ni paneles flotantes adicionales.
- Icono de búsqueda reemplazado por lupa SVG centrada verticalmente respecto del input, corrigiendo la posición que dependía de la fuente usada.
- Ajuste de paginación para colocar los resultados debajo de la cabecera persistente.
- Verificación de desplazamiento, paginación, búsqueda, vista normal/shiny y diseño estrecho en navegador aislado; capturas `docs/` actualizadas, incluida `screenshot-sticky.png`.
- Sin modificaciones de SQLite ni del progreso personal; instalación por ZIP completo sobre versiones anteriores.

## 0.1.6 — 2026-11-12

### Teselia/Unova, marca OT y navegación corregida

- Paleta grafito y verde inspirada en la Pokédex de Negro/Blanco, filas de índice más claras, detalles lima, bordes rectos y menos tarjetas.
- Sprites de escritorio ampliados a 82 px; el tamaño de los renders de vista previa también crece.
- Eliminado el comportamiento `sticky` en la vista previa, manteniendo un único scroll vertical del documento. Al navegar entre páginas se vuelve a mostrar la cabecera; se verificó poder bajar y subir hasta el inicio de la página.
- Marcador **OT ajeno** separado por objetivo y por tipo (normal/shiny): botón en cada fila, casilla en el editor, resumen y filtro de categoría. Sin autocompletar excepciones sin fuentes verificadas.
- Migración incremental de SQLite mediante `ALTER TABLE`, conservando contadores, capturas y cacerías. Exportación JSON ampliada y compatibilidad con respaldos antiguos sin el campo de OT.
- Capturas actualizadas en `docs/screenshot-pokedex.png`, `docs/screenshot-living.png` y `docs/screenshot-mobile.png`, con datos de demostración y sprites ausentes por modo sin conexión en el entorno de pruebas.
- Pruebas Python, JavaScript y comprobación visual con navegador aislado.


## 0.1.5 — 2026-11-12

### Pokédex Nacional y edición rápida

- Shiny Dex y Living Dex pasan a un índice de filas inspirado en la Pokédex clásica, con menos recuadros, encabezado unificado y barra de progreso compacta.
- Sprites ampliados (70 px en lista, 150 px en el panel de selección de escritorio) y mayor contraste entre número, nombre, forma y estado.
- Al pulsar el estado de un objetivo de **un ejemplar**, `Pendiente` pasa a `En HOME` y viceversa, persistiendo en SQLite sin abrir el editor.
- Para varios ejemplares, el estado abre el editor de cantidades y evita marcar todos como obtenidos de forma accidental; los Pokémon con candado no se actualizan con el cambio rápido.
- La selección de la fila permite previsualizar la forma y acceder al editor; en pantallas estrechas abre directamente el editor.
- Se conservaron filtros, paginación, caché de imágenes y base de datos. No hay migración ni necesidad de restaurar respaldos.
- Pruebas de vista, estados, edición y validación del backend; CI actualizado para ejecutar los tests de la Pokédex.


## 0.1.4 — 2026-11-12

### Pokédex en lista

- Las secciones **Shiny Dex** y **Living Dex** ahora muestran una fila compacta por objetivo, en lugar de tarjetas.
- Cada fila muestra número nacional, sprite, nombre, forma, estado (pendiente / en HOME / candado) y ejemplares en HOME.
- La fila completa sigue abriendo el editor de objetivos; la búsqueda, los filtros, los candados y la paginación mantienen su comportamiento.
- Vista adaptable a pantallas más estrechas, y pruebas JavaScript para el listado y los estados.
- No se modifica el esquema SQLite, los datos ni el caché de sprites.


## 0.1.3 — 2026-11-12

### Caché local persistente y modo offline

- Los sprites (PNG, GIF y renders HOME) se descargan solo al necesitarlos y se guardan en `~/.optpoke/sprites/` para reutilizarlos en futuras ejecuciones.
- Las imágenes y consultas de variedades de PokéAPI pasan por el servidor local; el navegador ya no solicita imágenes directamente a terceros.
- Recordatorio persistente de imágenes inexistentes (404/410), pausa de 15 minutos para errores temporales, límite de 3 descargas simultáneas y lista cerrada de orígenes autorizados.
- Modo estricto sin conexión `OPTPOKE_SPRITES_OFFLINE=1`, usando los sprites ya almacenados.
- Se retiró la importación de fuentes web: tipografía local del sistema para evitar consultas a Google Fonts.
- Vista de tamaño y cantidad de imágenes en Configuración; pruebas de caché, seguridad de URLs, persistencia y modo sin conexión.
- Sin migraciones de SQLite ni dependencias de terceros adicionales; el progreso existente permanece intacto.


## 0.1.2 — 2026-11-12

### Candados shiny y datos iniciales

- Corregido el filtro «Con candado» que no mostraba nada al no existir registros `locked` de inicio.
- Añadido catálogo conservador y fechado de 30 bloqueos shiny globales (no bloqueos por juego), con referencias a fuentes.
- Migración automática **de una sola ejecución** al iniciar, sin modificar estados personalizados ni los registros de progreso.
- Restaurar un respaldo anterior también aplica los candados si la migración todavía no se había ejecutado.
- Estadística «Con candado» en el panel shiny; pruebas para filtro, conteos, conservación de preferencias y respaldos antiguos.

## 0.1.1 — 2026-11-12

### Imágenes y sprites

- Respaldo escalonado para especies comunes: sprite pixelado → render 3D de Pokémon HOME → arte oficial → sprite de Showdown.
- Sprites específicos de formas/variantes desde Showdown, con render animado como alternativa.
- Consulta puntual y cacheada a PokéAPI para render de algunas variedades cuando no hay imagen en Showdown.
- Mapeo de nombres especiales (Unown, Vivillon, formas regionales, Alcremie, etc.).
- No se sustituye un shiny por un normal ni una forma alternativa por la base si no existe imagen exacta.
- Pruebas JavaScript de resolución de imágenes; sin cambios de base de datos ni dependencias de producción.

## 0.1.0 — 2026-11-12

### Primera entrega

- Esquema SQLite separado de los datos personales de los Excel.
- Catálogo inicial de 1.213 objetivos shiny y 1.283 normales.
- Reconciliación de Hoopa Unbound y Ursaluna Bloodmoon de la plantilla.
- Pokédex visual con búsqueda, filtros, objetivos extra y candados manuales.
- Importación idempotente de tareas Bank y cacerías (incluye fases sin número conocido).
- Panel Bank con estado de preparación, capturados y transferidos a HOME.
- Contador de cacerías, atajo y probabilidades acumuladas constantes.
- Selección de juegos, configuración simple de Shiny Charm.
- Respaldo JSON, pruebas y documentación para publicar el repositorio.

### Pendiente

- Importación de progreso real desde Google Sheets.
- Sprites alternativos por forma y comparador verificado de métodos.
- Reconciliación de tareas Bank con objetivos de colección.
