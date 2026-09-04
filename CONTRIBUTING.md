# Contribuir a Home Studio 3D

Este proyecto adopta la filosofía común de `AlexFrigenti/project-quality` mediante el perfil Blender/3D de `.quality/QUALITY.md`. La arquitectura y los controles concretos siguen siendo propios de este repositorio.

## Antes de empezar

- Parte de `main` actualizada.
- Comprueba la raíz del repositorio, la rama actual, el working tree y el estado ahead/behind frente a `origin/main`.
- Lee `README.md`, `PROJECT_CONTEXT.md`, `.quality/QUALITY.md`, `AGENTS.md` y este `CONTRIBUTING.md`.
- Revisa la implementación, escenas, medidas, assets, scripts y validaciones relacionadas cuando existan.
- Define un único objetivo pequeño y verificable.
- No uses secretos, credenciales, datos personales, planos o fotografías reales fuera del alcance aprobado.

## Flujo obligatorio

1. Partir de `main` actualizada.
2. Comprobar repo, rama y working tree.
3. Leer la documentación de contexto y las reglas indicadas arriba.
4. Clasificar el cambio como T0, T1 o T2.
5. Definir objetivo, alcance, exclusiones y criterios de aceptación.
6. Para T1/T2, crear los artefactos en `specs/NNN-feature-name/`: `spec.md`, `plan.md` y `tasks.md`.
7. Crear una rama con un único objetivo.
8. Implementar de forma incremental y dentro del alcance aprobado.
9. Ejecutar los gates aplicables de `.quality/QUALITY.md`, registrando `PASS`, `FAIL`, `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO` con evidencia real.
10. Revisar el diff completo, incluidos archivos binarios, pesados, configuración local y documentación.
11. Abrir una Pull Request que indique qué cambia, por qué, qué queda fuera, cómo se validó y qué riesgos o limitaciones persisten.
12. Fusionar solo con los checks verdes, las validaciones no aplicables explicadas y autorización explícita.
13. Usar merge commit; no usar squash ni rebase salvo cambio explícito de política.
14. Verificar `main` después del merge.
15. Eliminar la rama remota cuando corresponda.

## Flujo reducido T0

Un T0 puede omitir los artefactos T1/T2, pero conserva un alcance breve, una revisión del diff y una validación proporcional. Si el cambio afecta comportamiento, contratos, datos, seguridad o integraciones, debe elevarse a T1 o T2.

## Artefactos T1/T2

Las plantillas de `specs/000-template/` se adaptan a cada cambio. No se crean `research.md`, diagramas o checklists adicionales salvo que aporten información real. Cada criterio de aceptación debe relacionarse con una prueba determinista, un gate concreto o una revisión manual explícita.

Cuando exista lógica comprobable, se prioriza escribir o actualizar una prueba, verificar el fallo esperado cuando corresponda, implementar el cambio mínimo y ejecutar la regresión relevante. Cuando Blender no esté disponible, la validación de Blender queda pendiente de infraestructura; no se inventa un resultado.

## Pull Request

La PR debe incluir:

- clasificación T0/T1/T2;
- objetivo, alcance y exclusiones;
- ruta de `spec.md`, `plan.md` y `tasks.md` cuando existan;
- criterios de aceptación y su evidencia;
- gates ejecutados y resultado de cada uno;
- controles `NO APLICA`, `PENDIENTE DE INFRAESTRUCTURA` o `NO EJECUTADO` con explicación;
- riesgos, limitaciones y baseline relevante;
- confirmación de revisión del diff completo;
- evidencia visual para cambios de escena, materiales, iluminación, cámara o composición.

## Cambios sensibles

Eleva a T2 cualquier modificación de medidas canónicas, unidades o coordenadas globales, MCP, seguridad, ejecución privilegiada de Python, operaciones destructivas, arquitectura de assets, Git LFS, import/export o cambios masivos. No instales herramientas o dependencias únicamente para que una plantilla parezca completa.

## Revisión final

Antes de solicitar revisión:

- confirma que no hay archivos fuera de alcance;
- revisa secretos, datos privados, archivos locales y binarios inesperados;
- verifica dimensiones, unidades y correspondencia con `measurements/` cuando aplique;
- inspecciona viewport o render para cambios visuales;
- comprueba que la documentación coincide con el comportamiento;
- deja anotados riesgos, limitaciones y próximos pasos;
- no hagas merge, push ni cambios directos en `main` sin autorización explícita.
