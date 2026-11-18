# v0.2 — Vinculación segura entre Bank y Pokédex

## Primera entrega: propuestas sin efectos secundarios

En `Plan Bank`, Opt. Poke consulta `GET /api/bank/reconciliation`
y muestra qué objetivo de la Pokédex podría corresponder a cada tarea importada.
Por ahora **ninguna coincidencia está confirmada**: no se guarda un enlace y
no se modifica `in_home` en ninguna de las dos tablas.

La previsualización solo considera objetivos incluidos en el catálogo
`goals`, con su condición shiny (shiny y normal nunca se mezclan).

| Estado | Significado |
| --- | --- |
| `suggested` | La especie/forma/tipo tienen una sola coincidencia posible; sugerencia pendiente de confirmar |
| `ambiguous` | Bank no identifica la variante y hay varios objetivos compatibles |
| `unmatched` | No existe la especie/forma exacta en esa colección; no se inventa equivalencia |

Se comparan especies y formas ignorando acentos, mayúsculas y espacios
duplicados. La ausencia de forma solo se interpreta como unívoca **si esa
especie tiene exactamente un objetivo en esa colección**; en especies con
múltiples formas, la selección debe ser explícita. La marca de No OT/NOT
no afecta la identidad ni indica posesión.

## Reglas de seguridad

- El contador de Bank (`bank_tasks.in_home`) y el de la Pokédex
  (`goals.in_home`) **son datos independientes** hasta que se confirme
  explícitamente cómo se relacionan los ejemplares.
- No sumar `Bank.in_home + Dex.in_home`: podrían describir el mismo Pokémon.
- Una coincidencia exacta de especie y forma **no demuestra** que se trata
  del mismo ejemplar transferido a HOME.
- Las tareas ambiguas o sin coincidencia nunca actualizan la Pokédex.
- Esta etapa no añade columnas ni requiere migración o nueva copia del Excel.

## Próximos pasos para completar la v0.2

1. Revisar las sugerencias y las tareas ambiguas a partir de una base **local**;
   no publicar en GitHub el Excel de Bank ni la base privada.
2. Definir cómo registrar una confirmación explícita de vínculo y cómo
   deshacerla sin borrar el historial.
3. Acordar qué registro de ejemplar es la única fuente de verdad para HOME.
4. Incorporar después la actualización cruzada con una transacción,
   pruebas de cantidades y protección contra doble conteo.
5. Mejorar filtros y seguimiento por juego, incluida la distinción
   «capturado» frente a «transferido a HOME».

## Comprobación manual

Abrir `Plan Bank` en el navegador y revisar el resumen de sugerencias.
Para inspeccionar el JSON sin modificar datos, consultar en la instancia local:

```bash
curl -s http://127.0.0.1:8000/api/bank/reconciliation
```

Las pruebas automatizadas en `tests/test_bank_reconcile.py` usan únicamente
datos sintéticos, incluyendo una tarea con un ejemplar en Bank y cero en
Pokédex, para verificar que la previsualización nunca modifique el progreso.
