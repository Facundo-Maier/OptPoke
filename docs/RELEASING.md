# Releases de Opt. Poke

La primera release pública, **[v0.1.99](https://github.com/Facundo-Maier/OptPoke/releases/tag/v0.1.99)**, se publicó el 13 de noviembre de 2026 con ZIP y `SHA256SUMS`. No se deben volver a crear ni mover esa etiqueta.

Usamos versiones tipo SemVer: MAJOR para incompatibilidades de contratos estables, MINOR para funciones nuevas compatibles y PATCH para correcciones. Durante `0.x`, el proyecto todavía está en desarrollo. La siguiente entrega funcional prevista será `v0.2.0` cuando cumpla los objetivos de [ROADMAP](ROADMAP.md).

## Flujo de trabajo de cambios

1. Crear una rama desde `main`, implementar cambios y ejecutar las pruebas documentadas en [README](../README.md).
2. Abrir un Pull Request hacia `main`, revisar el diff (en particular privacidad/licencias) y comprobar el resultado de GitHub Actions.
3. Integrar el PR cuando esté listo. **Esto no crea automáticamente una nueva release**.
4. Para una versión nueva, actualizar número de versión de proyecto/interfaz/API y `CHANGELOG.md` según corresponda, con un commit específico.
5. Una vez en `main`, crear y subir una **etiqueta anotada nueva** (sin reutilizar las existentes):

```bash
git switch main
git pull --ff-only
git tag -a v0.2.0 -m "Opt. Poke 0.2.0"
git push origin v0.2.0
```

6. El workflow de release valida el tag, genera el paquete y checksum y crea una release en borrador. Revisar los adjuntos y las notas antes de publicarla.

No incluir SQLite, Excel, respaldos, cachés de sprites ni archivos personales en commits o distribuciones. Comprobar también las capturas. `git archive` solo empaqueta archivos versionados; los workflows tienen exclusiones adicionales, pero **la revisión humana sigue siendo necesaria**.

Las correcciones de documentación/auditoría que no requieren modificar el producto pueden entrar por PR sin mover la etiqueta v0.1.99 ni publicar una nueva release.
