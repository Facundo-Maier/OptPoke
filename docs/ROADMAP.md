# Hoja de ruta

## v0.1 — Base funcional (este paquete)

- [x] Catálogo LITE shiny y normal reconciliado
- [x] Pokédex con búsqueda, ordenación, filtros y objetivos extra
- [x] Candado manual / estado sin verificar
- [x] SQLite local con separación de progreso
- [x] Importación inicial de tareas Bank y ShinyHunts por CLI
- [x] Panel Bank con cantidades capturadas / en HOME
- [x] Contador de cacerías, fases y probabilidad fija
- [x] Lista de juegos disponibles + Shiny Charm
- [x] Copias JSON exportables e importables
- [x] Pruebas básicas y documentación

## v0.1.1 — Imágenes y formas (implementado parcialmente)

- [x] Sprites de formas regionales y variantes desde Showdown
- [x] Respaldo a modelos renderizados de Pokémon HOME para formas base
- [x] Imágenes animadas de algunas formas específicas (incluido Alcremie)
- [ ] Verificar uno a uno los casos especiales que todavía carezcan de imagen

## v0.2 — Progreso real y tareas Bank

- [x] Importadores para las dos copias actualizadas de Google Sheets (XLSX separados Shiny/Living), con vista previa y aplicación local confirmada
- [ ] Revisar y definir el estado `EVO` antes de importarlo
- [ ] Vinculación confirmada Bank → forma del catálogo
- [ ] Unificar progreso transferido a HOME sin duplicarlo
- [ ] Control más cómodo de transferencias por partida
- [ ] Completar / validar sprites shiny de variantes sin cobertura

## v0.3 — Cacerías avanzadas

- [ ] Calculadora modular para probabilidades variables
- [ ] Registro de sesiones, fases especiales y cronómetro
- [ ] Personalizar tiempos por método y juego
- [ ] Análisis de duración estimada vs. observada

## v0.4 — Comparador inteligente

- [ ] Métodos versionados por juego, con fuentes y fecha
- [ ] Filtros de OT propio / excepciones inevitables
- [ ] Reglas de legalidad y clonación dentro del juego
- [ ] Comparación por tiempo esperado, con requisitos y preparación
- [ ] Revisión de Pokémon y formas de juegos nuevos

## Para publicar

- [ ] Generar nuevas capturas de la demo; las capturas heredadas no se distribuyen
- [x] Demo con datos ficticios que no revele progreso personal
- [x] Pipeline CI preparado (ejecución remota pendiente del primer push)
- [x] Flujo de releases y etiquetas semánticas preparado (sin publicar)
- [x] Avisos de atribución de datos/sprites y licencia de código propia

**Estado v0.1.2:** candados shiny globales iniciales implementados; pendiente automatizar verificación de cambios de disponibilidad en próximos juegos y eventos.
