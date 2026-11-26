# Auditoría técnica de sprites — Opt. Poke

Esta guía permite comprobar la caché local y revisar la correspondencia de especie, forma y color. El uso normal de la aplicación y el significado de los marcadores se explican en [MANUAL_USUARIO.md](MANUAL_USUARIO.md).

Una imagen cacheada no garantiza que la forma o el color shiny sean correctos. La auditoría usa la caché de `~/.optpoke/sprites/` (o `OPTPOKE_DATA_DIR/sprites/`) y las fuentes definidas en `static/sprites.js`.

## Inventario sin conexión

Desde el repositorio:

```bash
node scripts/auditar_sprites.cjs
node scripts/auditar_sprites.cjs --solo-especiales
```

Sin `--probar-online` no hay solicitudes HTTP. Se generan informes en `reportes_sprites/`, ignorado por Git. Se puede cambiar la carpeta con `--salida DIR`.

| Archivo | Contenido |
| --- | --- |
| `resumen.json` | Totales por estado, fecha y carpeta de caché. |
| `inventario.csv` | Todos los objetivos revisados. |
| `pendientes.csv` | Objetivos sin imagen cacheada. |
| `pendientes_especiales.csv` | Formas alternativas o regionales pendientes. |

Los CSV usan punto y coma y BOM UTF-8 para facilitar su apertura en Excel.

| Estado | Interpretación |
| --- | --- |
| `cacheado_revisar_forma` | Hay un archivo; falta confirmar visualmente variante y color. |
| `sin_comprobar` | Quedan fuentes sin consultar; no equivale a «no existe imagen». |
| `sin_imagen_en_fuentes_configuradas` | Se agotaron las fuentes configuradas; puede haber otras. |
| `sin_fuente_configurada` | Falta mapear esa forma. |
| `revisar_cache` | Hay metadatos de caché inconsistentes. |

## Comprobación opcional con red

Iniciá primero el servidor local y, en otra terminal, solicitá un número limitado de consultas:

```bash
python -m uvicorn app.main:app --reload
node scripts/auditar_sprites.cjs --solo-especiales --probar-online 20
```

`20` limita consultas a la API local, no Pokémon; el valor aceptado es de 1 a 30. La API puede consultar proveedores autorizados para imágenes todavía no cacheadas. No hay comprobaciones automáticas en segundo plano.

## Revisión y corrección

1. Revisá primero `pendientes_especiales.csv` y después los archivos cacheados cuya forma/color faltan por confirmar.
2. Comprobá especie, forma, variante y condición shiny. Priorizá Unown, Vivillon, Alcremie, Pikachu con gorra, Tauros de Paldea, flores de Flabébé/Floette/Florges y Minior.
3. Si falta una imagen, revisá los alias y fuentes en `static/sprites.js`; ante la duda, conservá el marcador de ausencia.
4. Si cambiás un mapeo, agregá una regresión en `tests/test_sprites.cjs`. Una fuente nueva requiere revisar seguridad y atribución en `app/sprite_cache.py`.
5. Si una fuente que devolvió 404 vuelve a funcionar, invalidá solo el marcador de esa ruta, no toda la caché.

La auditoría de una instalación depende de su caché real: los archivos del repositorio por sí solos no prueban qué imágenes tiene cada usuario. Los resultados de auditorías pasadas quedan resumidos en [CHANGELOG.md](../CHANGELOG.md) y [ROADMAP.md](ROADMAP.md).
