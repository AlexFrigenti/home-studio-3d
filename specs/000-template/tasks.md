# Tareas: [nombre del cambio]

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` validada · `[!]` bloqueada.

| Estado | Tarea verificable | Validación asociada |
| --- | --- | --- |
| `[ ]` | Confirmar clasificación, alcance, exclusiones y criterios de aceptación. | Revisión de `spec.md`. |
| `[ ]` | Completar `spec.md` y `plan.md` con decisiones, invariantes y riesgos aplicables. | Revisión de artefactos T1/T2. |
| `[ ]` | Añadir o actualizar pruebas deterministas, o justificar por qué no aplican. | Test relacionado o justificación `NO APLICA`. |
| `[ ]` | Implementar el cambio mínimo dentro de la rama del objetivo. | Diff dentro del alcance aprobado. |
| `[ ]` | Ejecutar los gates aplicables y registrar evidencia real. | Gates de `.quality/QUALITY.md`. |
| `[ ]` | Verificar medidas, unidades, transformaciones, escena, exports o coste cuando corresponda. | Comprobación numérica, de unidades, apertura, export o rendimiento. |
| `[ ]` | Obtener e inspeccionar viewport o render cuando el cambio sea visual. | Captura/render y revisión visual explícita. |
| `[ ]` | Revisar procedencia/licencia de assets y detectar secretos o archivos pesados accidentales. | Revisión de procedencia, licencia, secretos y tamaños. |
| `[ ]` | Revisar el diff completo y confirmar que no hay cambios fuera de alcance. | `git diff --check` y revisión completa. |
| `[ ]` | Abrir la Pull Request con criterios, validaciones, riesgos y limitaciones. | Checklist de PR y checks reales. |

No convertir cada microtarea en un subagente: la ejecución agentic debe seguir la política proporcional de `AGENTS.md`.
