# Hoja de ruta — Opt. Poke

**Referencia:** v0.1.99 (noviembre de 2026). Este documento recoge el trabajo pendiente; el historial de versiones está en [CHANGELOG](../CHANGELOG.md).

## Objetivo de la v1.0

Opt. Poke será una herramienta local fiable para el uso habitual de su autor: seguir la Living Dex y la Shiny Dex, organizar tareas de Pokémon Bank, registrar cacerías y comparar métodos dentro de un alcance verificado. La prioridad es conservar el progreso y representar con claridad qué datos son ciertos, cuáles faltan y qué funciones están disponibles.

La v1.0 no exige cubrir todos los juegos, especies, formas o métodos posibles, ni ofrecer instalación asistida o sincronización en la nube. El alcance realmente soportado y las limitaciones se documentarán antes de publicarla. Las versiones de abajo son hitos de trabajo; si la v0.6 cumple lo necesario, se puede pasar directamente a la v0.9 sin crear versiones 0.7 u 0.8.

## Hecho en v0.1.x

- [x] Catálogo LivingFormLITE y S-LivingFormLITE actualizado (1.284 entradas normales y 1.214 shiny).
- [x] Pokédex en lista, con progreso en HOME, edición, búsqueda, filtros, candados y marcador de OT ajeno.
- [x] Paginación por rangos, estética Teselia/Unova, cabecera y sprite seleccionado persistentes.
- [x] Persistencia SQLite local, copias de seguridad JSON y datos privados separados del código.
- [x] Caché persistente de sprites, modo offline e importadores XLSX independientes con vista previa.
- [x] Base de tareas Bank y registro de cacerías.
- [x] Pruebas Python/JavaScript, CI y primera release pública v0.1.99.

## Cierre de imágenes previo a v0.2

- [x] Herramienta reproducible de auditoría local de sprites, sin red por defecto: `scripts/auditar_sprites.cjs`.
- [x] Documentar estados y comprobación opcional por lotes: [SPRITES.md](SPRITES.md).
- [x] Ejecutar la auditoría en WSL (17/11): 638 objetivos, 631 en caché, 7 sin comprobar y 0 con fuentes agotadas.
- [x] Corregir los alias problemáticos y revisar visualmente los casos restantes (verificación visual satisfactoria informada por el usuario).
- [x] Registrar el resultado y conservar los marcadores para las formas sin fuente exacta; no se fuerzan imágenes incorrectas.

## v0.2 — Progreso, juegos y Pokémon Bank

**Objetivo:** gestionar la colección y las tareas Bank sin perder información ni confundir capturas y transferencias con el progreso de la Pokédex.

- [x] Menú lateral plegable con control fijo en el borde izquierdo, disponible incluso al desplazarse.
- [x] Catálogo de juegos disponibles con varias partidas por juego y Shiny Charm independiente por partida, desmarcados de forma predeterminada.
- [x] Selector de partidas configuradas al agregar tareas Bank; las anteriores se conservan sin partida asignada.
- [x] Migración SQLite y respaldo compatibles con perfiles nuevos y datos anteriores.
- [x] Mostrar en ambas Pokédex la opción de filtro por juegos disponibles como **próximamente** (deshabilitada).
- [ ] Implementar el filtro con datos verificados de disponibilidad por especie y forma en cada juego.

- [x] Bank como lista de tareas editable: agregar, modificar, eliminar tareas y mantener cantidades de captura/HOME.
- [x] Distinguir tareas «Solo Bank» de tareas asociadas explícitamente a Shiny/Living Dex, con vínculo reversible.
- [x] Migración aditiva y respaldo compatible con tareas existentes sin vínculo.
- [x] EVO: evolución objetivo pendiente, con importación, edición y filtro; independiente de HOME.
- [x] Paginación completa en la cabecera fija junto al buscador compacto.
- [ ] Cerrar y probar el seguimiento de tareas y transferencias por juego y partida, incluidas las tareas anteriores sin partida.
- [x] Separar disponibilidad de OT propio de la marca NOT/OT ajeno y del OT de cada tarea.
- [x] Conciliar transferencias declaradas Bank→HOME de tareas vinculadas con OT elegible, evitando duplicados y con corrección de tareas.
- [ ] Revisar visualmente los cambios con datos locales antes del merge.
- [ ] Verificar con datos sintéticos las migraciones y el ciclo exportar → restaurar, y probar manualmente los recorridos principales antes de publicar v0.2.

La conciliación actual es de cantidades declaradas por tarea. La sincronización real de ejemplares concretos y partidas sigue fuera de v1.0: necesitará una identidad por ejemplar y datos de juego verificados. La opción de filtrar la Pokédex por Pokémon obtenibles en los juegos disponibles también requiere datos verificados y se aborda en v0.4.

## v0.3 — Cacerías avanzadas

**Objetivo:** registrar el historial de una cacería y ofrecer cálculos adecuados al método utilizado.

- [ ] Sesiones, fases y contadores, conservando los intentos y las fases sin intento conocido.
- [ ] Tiempos por intento editables y estadísticas de tiempo previsto y observado, con supuestos visibles.
- [ ] Probabilidades variables por método cuando existan reglas comprobadas (por ejemplo, SOS o cadenas); indicar cuándo solo es válida la probabilidad fija.
- [ ] Probar persistencia, edición y recuperación del historial sin alterar datos de otras secciones.

## v0.4 — Comparador de métodos

**Objetivo:** comparar métodos útiles para el usuario sin presentar como comprobados datos incompletos.

- [ ] Catálogo versionado de métodos por juego, con requisitos, probabilidades y fuentes verificables.
- [ ] Filtrar por juegos y partidas disponibles, Shiny Charm, OT y condiciones del método; considerar clonación únicamente cuando el juego y el procedimiento lo permitan.
- [ ] Mostrar duración prevista, preparación y requisitos, junto con los supuestos de la comparación.
- [ ] Incorporar nuevas especies, formas y métodos solo tras comprobar sus datos; indicar «sin datos suficientes» cuando corresponda.
- [ ] Implementar el filtro de objetivos obtenibles en los juegos disponibles únicamente con correspondencias verificadas por especie y forma; si no se puede validar, mantenerlo inactivo y documentar la limitación.

## v0.5 — Integración de funciones

**Objetivo:** poder pasar de un objetivo de Pokédex a sus tareas y cacerías relacionadas, y entender su estado en cada sección.

- [ ] Revisar recorridos entre Pokédex, Bank, partidas, cacerías y comparador; añadir vínculos o accesos donde aporten utilidad.
- [ ] Mantener coherentes los nombres, estados, filtros y cantidades mostradas en las distintas secciones.
- [ ] Probar los casos con varios ejemplares, varias partidas, tareas sin vínculo y objetivos sin método disponible, sin sumar contadores HOME independientes.

## v0.6 — Interfaz

**Objetivo:** dedicar una versión a la claridad y comodidad de uso de todas las secciones ya funcionales.

- [ ] Revisar navegación, jerarquía visual, legibilidad y consistencia con la Pokédex en lista.
- [ ] Revisar escritorio y pantallas estrechas, desplazamiento, controles persistentes y diálogos.
- [ ] Mejorar estados vacíos, mensajes de error y confirmaciones para que se entienda qué acción se realizó y qué datos cambian.
- [ ] Comprobar navegación con teclado, etiquetas y foco visibles, contraste y preferencia de movimiento reducido.
- [ ] Probar visualmente los recorridos principales en esta versión antes de darla por cerrada.

## v0.9 — Versión de prueba previa a 1.0

**Objetivo:** utilizar durante un período la aplicación con una copia de los datos personales y detectar problemas del uso cotidiano antes de declarar la estabilidad.

- [ ] Crear y verificar un respaldo antes de probar migraciones o restauraciones con datos personales.
- [ ] Probar actualización desde la versión anterior, importación XLSX, exportación y restauración JSON, funcionamiento sin conexión y persistencia tras reiniciar.
- [ ] Revisar los recorridos habituales con la colección real, sin subir bases, hojas ni capturas con progreso al repositorio.
- [ ] Corregir errores que bloqueen esos recorridos, pierdan datos o muestren resultados engañosos; repetir la prueba afectada.
- [ ] Congelar el alcance funcional y documentar los límites que queden para 1.0.

## v1.0 — Versión estable para uso personal

- [ ] Pokédex, Bank, cacerías y comparador cumplen el alcance publicado y no tienen fallos conocidos que impidan su uso habitual.
- [ ] Actualización, migraciones y restauración de respaldo comprobadas; los cálculos y fuentes del comparador son trazables.
- [ ] Documentación de uso y limitaciones coherente con la aplicación; demo ficticia y distribución sin datos privados.
- [ ] Pruebas automatizadas y revisión manual de interfaz satisfactorias; publicar desde `main` según [RELEASING.md](RELEASING.md).

## Calidad transversal

- [x] Documentación, licencia MIT del código, atribución de fuentes y demo ficticia.
- [x] GitHub Actions y release pública v0.1.99.
- [ ] Para cada cambio de datos o esquema, probar migración y respaldo antes de integrar la versión.
- [ ] Revisar licencias de recursos nuevos y comprobar antes de cada release que no se publiquen Excel, cachés, capturas con progreso ni bases privadas.
- [ ] Mantener visibles las limitaciones de sprites, métodos y formas sin datos verificados; no sustituir deliberadamente una forma o color por otro.
