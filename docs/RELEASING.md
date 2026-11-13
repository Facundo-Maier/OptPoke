# Releases

El mecanismo está preparado; no se ha creado ninguna etiqueta ni release remota.
Primera etiqueta prevista: `v0.1.99`, conservando la versión de origen. La próxima
versión funcional podrá ser `v0.2.0` cuando alcance los objetivos del roadmap.

Usar SemVer: MAJOR para incompatibilidades de la API/formatos estables, MINOR
para funciones compatibles y PATCH para correcciones. Durante 0.x la API sigue
en desarrollo; documentar cualquier incompatibilidad y las migraciones.

1. Revisar privacidad del diff y ejecutar CI localmente (README).
2. Actualizar `pyproject.toml`, versión FastAPI e interfaz; registrar CHANGELOG.
3. Subir los cambios revisados y esperar CI verde en GitHub.
4. Crear y subir la etiqueta anotada correspondiente, por ejemplo:

```bash
git tag -a v0.1.99 -m "Opt. Poke 0.1.99"
git push origin v0.1.99
```

5. El workflow vuelve a ejecutar CI, valida versión/tag/changelog y crea una
   **release en borrador** con código versionado y SHA256SUMS. Revisar notas y
   adjuntos antes de publicarla desde GitHub Releases.

No mover etiquetas publicadas: crear una nueva versión para corregir errores.
No incluir bases de datos, exportaciones, Excel, cachés, sprites ni capturas con
progreso. `git archive` solo empaqueta archivos versionados; CI aplica además
una lista de exclusiones. Una revisión manual del contenido sigue siendo necesaria.

Para activar: GitHub → Settings → Actions → General debe permitir GitHub Actions.
El job de release declara `contents: write`; no necesita un token personal.
La ejecución real en GitHub solo se verifica después del primer push autorizado.
