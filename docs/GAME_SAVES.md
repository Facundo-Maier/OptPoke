# Mis juegos y partidas — v0.2 en desarrollo

La sección **Juegos y partidas** contiene un catálogo predefinido de juegos de Pokémon, ordenado por generación (de la I a la IX), no alfabéticamente. El mismo orden se aplica a los selectores de Bank.
No se escribe el nombre de cada juego manualmente: se marca **Disponible** y se
agregan una o más **partidas** con nombres distintos (por ejemplo, Principal,
Segunda partida), cada una con su estado de **Shiny Charm** independiente.

En una instalación nueva los juegos comienzan **no disponibles**: activá
únicamente los que realmente tenés. En instalaciones antiguas, si los juegos
siguen exactamente con el estado inicial anterior (todos disponibles,
sin Shiny Charm ni partidas configuradas), se desmarcan una sola vez.
Las selecciones ya personalizadas y cualquier partida guardada se preservan.
No se generan partidas automáticamente.

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
- El menú lateral se abre desde un botón fijo al borde izquierdo de la pantalla,
  también accesible al desplazarse por la Pokédex. No depende de la barra superior.
  Su preferencia se guarda en el navegador, no en SQLite.
- Shiny y Living Dex muestran una opción deshabilitada para filtrar Pokémon
  obtenibles según los juegos disponibles. El filtro todavía no funciona:
  necesita datos fiables por juego, especie y forma, que se investigarán
  posteriormente.

La aplicación funciona en local y no requiere conexión con la cuenta de Nintendo.
