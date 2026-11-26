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
| **Vinculada a Shiny/Living Dex** | Guarda un vínculo opcional y explícito con especie, forma y colección |

Al crear una tarea, el tipo por defecto es **Solo Bank**. También es el tipo de
todas las tareas importadas previamente mediante Excel.

Para vincular una tarea, marcá «Relacionar con un objetivo de la Pokédex»,
buscá por Pokémon o número de Pokédex, elegí la forma y guardá. El selector
utiliza solo objetivos existentes y no permite mezclar una tarea normal con
un objetivo shiny ni enlazar otra especie. Podés desmarcarlo para desvincular
sin borrar la tarea ni la entrada de la Pokédex.

**El vínculo por sí solo no implica transferencia.** Las tareas «Solo Bank» no
cambian la Dex. Las vinculadas acreditan los ejemplares que realmente se
marcan **En HOME** cuando su OT es **propio**, o cuando es **ajeno** y el objetivo
está explícitamente marcado «No obtenible con mi OT». Con OT «Sin indicar» no
se acreditan ejemplares; los capturados que no llegaron a HOME tampoco cuentan.

La conciliación registra créditos por tarea y calcula el progreso visible de
la Dex como el mínimo entre el objetivo y la cantidad manual previa más los
créditos transferidos. Guardar dos veces no duplica; corregir, desvincular o
borrar una tarea recalcula los créditos; dos tareas pueden contribuir al
mismo objetivo sin superar su cantidad necesaria. Al completar se retira EVO.

**Se separan dos conceptos:** en Dex, «¿Se puede obtener con mi OT?» tiene
los estados Sin verificar / Sí / No; NOT («OT ajeno») sigue siendo una marca
independiente que **no implica poseerlo**. En Bank, el OT del ejemplar puede
ser Sin indicar / Propio / Ajeno. La disponibilidad con OT propio aún es una
selección manual por objetivo, no una inferencia por juego ni por partida.

Las tareas importadas anteriormente **no se sincronizan retroactivamente** al
actualizar la base de datos. Si querés reducir manualmente HOME por debajo
de créditos de Bank vigentes, primero corregí las tareas Bank. El Excel de
AustinJohn sigue prevaleciendo en los campos que actualiza y reinicia
los créditos anteriores de esa forma sin tocar el historial de Bank.

## Persistencia y compatibilidad

- La migración agrega de forma segura `bank_tasks.save_id` (perfil de partida opcional) y `bank_tasks.goal_id`, referencia opcional
  a `goals.id` con `ON DELETE SET NULL`. Las tareas previas reciben `NULL`.
- El respaldo JSON conserva el vínculo, el OT y los créditos. Los respaldos
  antiguos reciben valores seguros y no se interpretan como transferencias nuevas.
- La importación inicial `26Febrero27.xlsx` conserva el comportamiento actual,
  con identificadores de filas de origen y protección contra duplicados.
- Los cambios se prueban primero en la rama derivada de `develop`, en una base
  local, antes de integrarlos a `develop`. No publicar los Excel o DB privados.

## Limitación

Esta etapa concilia **cantidades declaradas por el usuario**, no lee partidas
ni Pokémon HOME. La identidad de cada ejemplar y la obtención legítima según
juego y partida deberán modelarse y verificarse más adelante.
