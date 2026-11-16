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
- [ ] Ejecutar el informe en la instalación WSL real, porque la caché personal no está en GitHub.
- [ ] Revisar manualmente las formas especiales y corregir alias/imágenes exactas con sus pruebas.
- [ ] Registrar los casos sin fuente válida sin reemplazarlos por formas o colores incorrectos.

## v0.2 — Progreso y Pokémon Bank

- [ ] Aclarar el valor `EVO` en AustinJohn; actualmente se omite en las importaciones.
- [ ] Vincular cada tarea de Bank a la forma correspondiente de la Pokédex con coincidencias verificadas.
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
