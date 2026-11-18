# Releases de Opt. Poke

La primera release pública, **[v0.1.99](https://github.com/Facundo-Maier/OptPoke/releases/tag/v0.1.99)**, se publicó el 13 de noviembre de 2026 con ZIP y `SHA256SUMS`. No se deben volver a crear ni mover esa etiqueta.

Usamos versiones tipo SemVer: MAJOR para incompatibilidades de contratos estables, MINOR para funciones nuevas compatibles y PATCH para correcciones. Durante `0.x`, el proyecto todavía está en desarrollo. La siguiente entrega funcional prevista será `v0.2.0` cuando cumpla los objetivos de [ROADMAP](ROADMAP.md).

## Flujo de trabajo de cambios

1. Crear una rama `feat/...`, `fix/...` o `chore/...` desde `develop`, implementar cambios y ejecutar las pruebas documentadas en [README](../README.md).
2. Probar el cambio en su propia rama y abrir un Pull Request hacia `develop`. Revisar el diff (en particular privacidad/licencias), la interfaz cuando corresponda y GitHub Actions antes de integrar.
3. Para una versión nueva, actualizar número de versión de proyecto/interfaz/API y `CHANGELOG.md` mediante PR hacia `develop`.
4. Probar los cambios integrados en `develop` y abrir una PR de `develop` hacia `main`. Mergear únicamente la versión ya probada, con CI aprobado. Conservar la historia usando merge commit para esta PR entre ramas permanentes. **Esto no crea automáticamente una nueva release**.
5. Una vez en `main`, crear y subir una **etiqueta anotada nueva** (sin reutilizar las existentes):

```bash
git switch main
git pull --ff-only
git tag -a v0.2.0 -m "Opt. Poke 0.2.0"
git push origin v0.2.0
```

6. El workflow de release comprueba que el commit etiquetado esté incluido en el historial de `main`, valida el tag, genera el paquete y checksum y crea una release en borrador. Revisar los adjuntos y las notas antes de publicarla.

No incluir SQLite, Excel, respaldos, cachés de sprites ni archivos personales en commits o distribuciones. Comprobar también las capturas. `git archive` solo empaqueta archivos versionados; los workflows tienen exclusiones adicionales, pero **la revisión humana sigue siendo necesaria**.

Las correcciones de documentación/auditoría que no requieren modificar el producto pueden entrar por PR sin mover la etiqueta v0.1.99 ni publicar una nueva release.

## Comprobación de la rama de release

El checkout descarga el historial completo (`fetch-depth: 0`). Antes de empaquetar, se actualiza `origin/main` y `git merge-base --is-ancestor` verifica que contenga el commit etiquetado. Se admiten tanto el último commit de `main` como versiones anteriores integradas; un commit exclusivo de `develop` o de otra rama detiene el trabajo sin generar ZIP ni borrador. Si no se puede obtener `main`, el paso también falla.

Esta comprobación debe estar integrada en `main` antes de crear la siguiente etiqueta. Las etiquetas antiguas utilizan el workflow de su propio commit y no adquieren esta regla retroactivamente. Tampoco impide crear releases manuales desde GitHub. No crear etiquetas de prueba en el repositorio público: las pruebas simulan ramas y etiquetas en repositorios temporales locales.
