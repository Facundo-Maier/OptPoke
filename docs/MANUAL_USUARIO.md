# Manual de uso — Opt. Poke (rama develop)

Esta guía describe las funciones presentes en `develop`. La versión publicada v0.1.99 puede tener una interfaz y funciones distintas. La aplicación guarda el progreso en SQLite local; no lee partidas ni Pokémon HOME.

## Juegos y partidas

En **Juegos y partidas**, marcá como disponibles los títulos que tenés. En instalaciones nuevas comienzan desmarcados; los títulos se muestran por generación. Podés crear varias partidas por juego y marcar Shiny Charm por separado en cada una. No se crean partidas automáticamente.

Al crear una tarea Bank, elegí una partida configurada. Las tareas anteriores sin partida siguen existiendo y muestran «Sin partida asignada» hasta que las edites. No se puede eliminar una partida con tareas asignadas: primero reasignalas o desvinculalas.

En las Pokédex aparece «Solo mostrar Pokémon obtenibles en mis juegos» como opción deshabilitada. Aún faltan datos verificados de disponibilidad por juego, especie y forma; activar un juego no determina por sí solo si un objetivo es obtenible con tu OT.

## Shiny Dex y Living Dex

Cada objetivo registra una cantidad deseada y cuántos ejemplares están **En HOME**. Se pueden editar los objetivos y marcar uno de un solo ejemplar desde la lista. La marca **EVO** indica una evolución pendiente: no cuenta como En HOME y se retira al completar el objetivo.

**NOT / OT ajeno** es una marca independiente; no indica posesión. «¿Se puede obtener con mi OT?» tiene los estados **Sin verificar**, **Sí** y **No**, y por ahora se establece manualmente. Un candado shiny tampoco cambia el progreso por sí solo.

## Tareas Bank y progreso de la Pokédex

**Plan Bank** es una lista editable de tareas. Cada tarea registra requeridos, capturados y transferidos a HOME, con la relación `0 ≤ En HOME ≤ capturados ≤ requeridos`. Se puede filtrar por juego, partida y tareas pendientes; eliminar una tarea requiere confirmación.

Una tarea puede quedar **Solo Bank** o vincularse explícitamente a un objetivo existente de Shiny o Living Dex. El vínculo por sí solo no suma progreso. Una transferencia declarada **En HOME** en Bank se acredita en la Pokédex cuando la tarea está vinculada y el OT de la tarea es:

- **Propio**; o
- **Ajeno**, si el objetivo está marcado explícitamente «No obtenible con mi OT».

Con OT **Sin indicar**, las transferencias no se acreditan; tampoco cuentan los ejemplares solo capturados. La Pokédex combina el progreso marcado manualmente y las transferencias elegibles de Bank, sin superar la cantidad objetivo. Corregir, desvincular o borrar una tarea recalcula ese aporte. Si querés bajar el progreso de la Pokédex por debajo de un aporte activo, corregí primero la tarea Bank.

Las tareas antiguas no se acreditan retroactivamente al actualizar la aplicación. La conciliación usa cantidades declaradas por el usuario: no verifica la identidad de cada Pokémon ni consulta partidas o HOME.

## Importación y respaldos

En **Configuración** se importan por separado los archivos XLSX de Shiny y Living, siempre con vista previa y confirmación. En las filas incluidas, el Excel prevalece para HOME y EVO: `0` marca un ejemplar En HOME; `1` y `EVO` dejan cero. `NOT` marca OT ajeno, sin afirmar posesión. Los objetivos ausentes no se modifican. La importación puede reiniciar aportes Bank de las filas cuyo HOME sobrescribe; revisá la vista previa antes de confirmar.

La exportación JSON guarda el progreso, y **restaurar reemplaza los datos actuales**. Guardá una copia fuera del repositorio antes de restaurar o actualizar. Los respaldos anteriores se aceptan sin inventar partidas ni transferencias nuevas.

## Imágenes

Los sprites se cargan cuando se necesitan y quedan en caché local. Una forma o variante sin imagen exacta muestra un marcador; no se sustituye deliberadamente por otra forma o color. «Sin comprobar» indica que aún quedan fuentes por consultar, no que el sprite no exista. Si vas a revisar la caché o sus fuentes, consultá la [guía técnica de auditoría](SPRITES.md).
