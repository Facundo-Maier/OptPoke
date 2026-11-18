# Plan Pokémon Bank — Lista de tareas (v0.2 en desarrollo)

Bank es una **TODO list editable**, no un segundo Living Dex. Una tarea puede
existir **solo en Bank**, incluso si su Pokémon no figura como objetivo en las
hojas de Shiny/Living Dex.

## Administrar tareas

En **Plan Bank**:

- **Agregar tarea:** elegir una partida configurada en [Juegos y partidas](GAME_SAVES.md), Pokémon, forma (si aplica), shiny/normal,
  notas, cantidad requerida, capturados y enviados a HOME.
- **Editar:** permite cambiar todos esos datos, incluida la partida y la asociación. Las tareas antiguas sin partida siguen siendo editables.
  Los campos de cantidades deben cumplir `0 ≤ en HOME ≤ capturados ≤ requeridos`.
- **Eliminar:** requiere confirmación y solo borra esa tarea de Bank.
- La edición rápida de capturados/HOME sigue disponible en las filas.
- Los filtros por juego, por partida y por tareas pendientes/completadas siguen funcionando.

La lista no está limitada a los Pokémon del catálogo. Podés registrar cualquier
objetivo operativo o de transferencia, tanto de la Shiny Dex como fuera de ella.

## Tipo de tarea

Cada tarea se clasifica explícitamente:

| Tipo | Funcionamiento |
| --- | --- |
| **Solo Bank** | No tiene ningún objetivo asociado en Shiny/Living Dex |
| **En Pokédex** | Guarda el vínculo seleccionado a un objetivo existente (especie, forma y tipo shiny/normal) |

Al crear una tarea, el tipo por defecto es **Solo Bank**. También es el tipo de
todas las tareas importadas previamente mediante Excel.

Para vincular una tarea, marcá «Relacionar con un objetivo de la Pokédex»,
buscá por Pokémon o número de Pokédex, elegí la forma y guardá. El selector
utiliza solo objetivos existentes y no permite mezclar una tarea normal con
un objetivo shiny ni enlazar otra especie. Podés desmarcarlo para desvincular
sin borrar la tarea ni la entrada de la Pokédex.

**Un vínculo es únicamente una referencia, no una transferencia.** La cantidad
`bank_tasks.in_home` sigue siendo el registro de esa tarea; `goals.in_home`
sigue siendo el progreso de la colección. La aplicación **no suma los contadores
ni sincroniza automáticamente** porque podrían referirse al mismo ejemplar.

## Persistencia y compatibilidad

- La migración agrega de forma segura `bank_tasks.save_id` (perfil de partida opcional) y `bank_tasks.goal_id`, referencia opcional
  a `goals.id` con `ON DELETE SET NULL`. Las tareas previas reciben `NULL`.
- Las copias JSON nuevas exportan la asociación; al restaurar respaldos antiguos
  sin el campo, las tareas quedan como Solo Bank.
- La importación inicial `26Febrero27.xlsx` conserva el comportamiento actual,
  con identificadores de filas de origen y protección contra duplicados.
- Los cambios se prueban primero en la rama derivada de `develop`, en una base
  local, antes de integrarlos a `develop`. No publicar los Excel o DB privados.

## Siguiente etapa de la v0.2

Si se decide automatizar el reflejo de transferencias, primero hay que
determinar cómo identificar ejemplares concretos y cuál será la única fuente
de verdad del progreso en HOME. **No se hará sincronización por el solo hecho
de asociar una tarea**. La TODO list ya puede gestionarse de forma independiente.
