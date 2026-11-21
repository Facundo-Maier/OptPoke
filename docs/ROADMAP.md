# Hoja de ruta — Opt. Poke

**Referencia:** v0.1.99 (noviembre de 2026). Este documento recoge el trabajo pendiente; el historial de versiones está en [CHANGELOG](../CHANGELOG.md).

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

## v0.2 — Progreso y Pokémon Bank

- [x] Menú lateral plegable con control fijo en el borde izquierdo, disponible incluso al desplazarse.
- [x] Catálogo de juegos disponibles con varias partidas por juego y Shiny Charm independiente por partida, desmarcados de forma predeterminada.
- [x] Selector de partidas configuradas al agregar tareas Bank; las anteriores se conservan sin partida asignada.
- [x] Migración SQLite y respaldo compatibles con perfiles nuevos y datos anteriores.
- [x] Mostrar en ambas Pokédex la opción de filtro por juegos disponibles como **próximamente** (deshabilitada).
- [ ] Implementar el filtro con datos verificados de disponibilidad por especie y forma en cada juego.

- [x] Bank como TODO list editable: agregar, modificar, eliminar tareas y mantener cantidades de captura/HOME.
- [x] Distinguir tareas «Solo Bank» de tareas asociadas explícitamente a Shiny/Living Dex, con vínculo reversible.
- [x] Migración aditiva y respaldo compatible con tareas existentes sin vínculo.
- [ ] Si fuera necesario, diseñar sincronización de ejemplares sin doble conteo (no se activa por asociar una tarea).

- [x] EVO: evolución objetivo pendiente, con importación, edición y filtro; independiente de HOME.
- [x] Paginación completa en la cabecera fija junto al buscador compacto.
- [x] Permitir vínculos **opcionales y explícitos** de tareas Bank con objetivos del catálogo, sin enlaces automáticos.
- [ ] Mantener un único progreso en HOME, sin contar dos veces ejemplares o transferencias.
- [ ] Mejorar el seguimiento de tareas y transferencias por juego.

## v0.3 — Cacerías avanzadas

- [ ] Probabilidades variables por método (SOS, cadenas, etc.).
- [ ] Sesiones, fases y contadores; tiempos por intento editables.
- [ ] Estadísticas de tiempo previsto y observado.

## v0.4 — Comparador de métodos

- [ ] Métodos versionados por juego y fuentes verificadas.
- [ ] Filtros de juegos, Shiny Charm y OT; clonación legítima dentro del juego.
- [ ] Comparación de duración prevista, requisitos y preparación.
- [ ] Incorporación verificada de nuevas especies, formas y métodos.

## Calidad y publicación

- [x] Documentación, licencia MIT del código, atribución de fuentes y demo ficticia.
- [x] GitHub Actions y release pública v0.1.99.
- [ ] Revisar licencias de nuevos recursos y que nunca se publiquen Excel, cachés, capturas con progreso ni bases privadas.

