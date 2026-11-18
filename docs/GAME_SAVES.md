# Mis juegos y partidas — v0.2 en desarrollo

La sección **Juegos y partidas** contiene un catálogo predefinido de juegos de Pokémon.
No se escribe el nombre de cada juego manualmente: se marca **Disponible** y se
agregan una o más **partidas** con nombres distintos (por ejemplo, Principal,
Segunda partida), cada una con su estado de **Shiny Charm** independiente.

Los juegos y preferencias que ya existían se conservan durante la migración.
En versiones anteriores todos los juegos se creaban como disponibles por
defecto: desmarcá los que no tengas. Una partida no se crea automáticamente,
porque el sistema no puede inferir cuántos archivos de guardado utilizás.

## Pokémon Bank

Al crear una tarea de Bank se elige una **partida ya configurada**, no se escribe
el juego a mano. Se guarda \`save_id\`, y el juego se deriva de esa partida.
El selector permite filtrar tareas por juego o por partida.

Las tareas creadas o importadas antes de esta función **no se eliminan ni se
asignan automáticamente**: siguen mostrando su juego original y la leyenda
«Sin partida asignada». Se pueden editar para elegir la partida correcta.
La posibilidad de tareas **Solo Bank** o vinculadas explícitamente con Shiny/Living
Dex se conserva; ninguna asociación modifica contadores de HOME.

Para evitar pérdida de referencias, no se permite eliminar una partida
que todavía tenga tareas Bank asignadas. Primero hay que reasignarlas o
desvincularlas.

## Datos, migración y respaldo

- Tabla nueva \`game_saves\`, con \`id\`, \`game\`, \`name\` y \`shiny_charm\`.
- Migración aditiva: \`bank_tasks.save_id\` es opcional, y las tareas antiguas
  comienzan con \`NULL\`.
- Los nuevos respaldos JSON incluyen partidas y asignaciones de tareas.
- Respaldos antiguos que no tienen estos campos se restauran sin inventar
  partidas ni modificar el progreso de la colección.
- El menú lateral puede plegarse desde el botón de la barra superior para
  utilizar más ancho de pantalla. La preferencia visual se guarda en el
  navegador, no en SQLite.

La aplicación funciona en local y no requiere conexión con la cuenta de Nintendo.
