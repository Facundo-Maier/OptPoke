# Auditoría de sprites — Opt. Poke

## Objetivo

Identificar qué sprites de Shiny Dex y Living Dex están en la caché local, cuáles todavía no se intentaron descargar y cuáles requieren corregir la correspondencia de una forma regional o alternativa. **Un archivo cacheado no garantiza que la forma o color shiny sean correctos**: la verificación visual sigue siendo necesaria.

La aplicación guarda sprites en `~/.optpoke/sprites/` (o `$OPTPOKE_DATA_DIR/sprites/`). La auditoría reutiliza el resolvedor de `static/sprites.js`, sin descargar imágenes por defecto.

## 1. Inventario sin conexión

Desde la carpeta del repositorio en WSL:

```bash
node scripts/auditar_sprites.cjs
# Solo formas especiales:
node scripts/auditar_sprites.cjs --solo-especiales
```

Esto **no realiza solicitudes HTTP**. Genera archivos locales en `reportes_sprites/` (excluidos de Git):

| Archivo | Contenido |
| --- | --- |
| `resumen.json` | Cantidades por estado, fecha y carpeta de caché |
| `inventario.csv` | Todos los objetivos revisados (shiny y normales) |
| `pendientes.csv` | Objetivos sin imagen ya cacheada |
| `pendientes_especiales.csv` | Pendientes con forma alternativa o regional |

Los CSV usan punto y coma y BOM UTF-8 para facilitar su apertura en Excel.

### Estados

- `cacheado_revisar_forma`: existe un archivo local; falta verificar manualmente especie, variante y color.
- `sin_comprobar`: ninguna fuente probada con éxito y quedan alternativas sin consultar; **no significa que no exista sprite**.
- `sin_imagen_en_fuentes_configuradas`: las fuentes conocidas están agotadas; podría existir otra.
- `sin_fuente_configurada`: falta definir el mapeo de esa forma.
- `revisar_cache`: metadatos cacheados inconsistentes.
  
## 2. Comprobación online opcional y limitada

Si elegís hacerlo, iniciá primero la aplicación:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

En otra terminal WSL, desde el proyecto:

```bash
node scripts/auditar_sprites.cjs --solo-especiales --probar-online 20
```

`20` es el máximo de **consultas a la API local**, no de Pokémon. El límite permitido es de 1 a 30 por ejecución, con una breve pausa entre solicitudes. La API local puede consultar proveedores autorizados para archivos todavía no cacheados; las respuestas se conservan en disco. No se ejecutan comprobaciones en segundo plano. Sin `--probar-online` no hay tráfico.

También podés pasar `--salida DIR` para elegir otra carpeta de informes.

## 3. Revisión visual

Inspeccioná primero los registros de `pendientes_especiales.csv` y después los sprites cacheados que necesitan validación visual. Confirmá especie, forma, variante y color shiny/no shiny. Priorizá Unown, Vivillon, Alcremie, Pikachu con gorra, Tauros de Paldea, flores de Flabébé/Floette/Florges y Minior.

Para resolver una ausencia:

1. Revisá el nombre/alias en `static/sprites.js` (`showdownForm`, `alcremieSources`, `spriteSources`, `pokeApiVariety`).
2. Usá solo una imagen de la **forma y condición shiny correctas**; ante la duda, mantené el marcador de ausencia.
3. Si modificás el mapeo, agregá una prueba en `tests/test_sprites.cjs`.
4. No desactives las validaciones de fuentes de `app/sprite_cache.py`: cualquier fuente adicional requiere revisión de seguridad, estabilidad y atribución.
5. Si una fuente antes devolvió 404 y ahora existe, invalidá solo el marcador de ausencia correspondiente, no toda la caché.

No es necesario descargar las 2.498 entradas de la Pokédex: primero auditamos lo que ya existe y hacemos comprobaciones puntuales. La auditoría completa depende de la caché real de tu instalación WSL; **no puede inferirse únicamente del repositorio**.

## Casos resueltos a partir del informe del 16/11/2026

- Shiny Deerling y Sawsbuck, forma `Fall`: Showdown utiliza `autumn`.
- Shiny Dudunsparce, `3 Segment`: Showdown utiliza `threesegment`.
- Living Pikachu, `World Cap`: el render exacto se encuentra en `sprites/home/pikachu-world.png`.

Estos cuatro cambios usan rutas nuevas: los registros 404 de rutas anteriores no necesitan borrarse. Luego de actualizar la rama, visitar los Pokémon o ejecutar la auditoría opcional con un límite pequeño para llenar la caché; finalmente verificar visualmente las imágenes. Los demás 190 casos del informe inicial siguen **sin comprobar**, no necesariamente sin imagen.

### Segunda auditoría (16/11/2026)

Tras navegar las Pokédex, la caché pasó de **444 a 626** objetivos de formas especiales con imagen; los pendientes bajaron de 194 a 12 (1 sin comprobar, 11 sin imagen en las fuentes configuradas). Se detectaron alias adicionales que requieren usar el nombre del sprite de la forma base:

- Unown letra `a` shiny → `unown.png` (único sin comprobar, además de un 404 de una fuente).
- Oricorio `Baile Style` (normal/shiny) → `oricorio.png`.
- Minior `Red Core` (normal/shiny) → `minior.png`.

Las demás entradas con 404 del segundo informe corresponden a Deerling, Sawsbuck, Dudunsparce y Pikachu World Cap (ya incluidos en la misma corrección). Los resultados son **por colección**, por lo que una misma forma puede contarse dos veces.

Después de fusionar el PR, recorrer las variantes afectadas para que se cacheen las nuevas rutas y repetir la auditoría. No eliminar los marcadores 404 de las rutas antiguas; son distintos archivos. Que un sprite exista sigue sin sustituir la revisión visual de su variante correcta.
