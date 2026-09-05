# Perfil de calidad — Home Studio 3D

> Perfil específico para Blender/3D basado en el contrato común de [AlexFrigenti/project-quality](https://github.com/AlexFrigenti/project-quality). No copia controles específicos de Node.js o web.

## Propósito

Este documento adapta la filosofía común de calidad a un proyecto de reconstrucción 3D de espacios reales. El nivel de exigencia se mantiene; cambian las evidencias y los controles según haya documentación, scripts, escenas, assets, medidas o exports implicados.

Todo cambio debe ser trazable, comprobable y reversible en la medida razonable. Los cambios funcionales o estructurales se trabajan aislados y se integran mediante Pull Request. La documentación relevante se actualiza en la misma PR.

## Principios universales

- Mantener trazabilidad entre necesidad, alcance, especificación, tareas, validaciones, evidencia y PR.
- Trabajar en una rama específica por objetivo; `main` representa el estado estable.
- Revisar el diff completo y comprobar el comportamiento real, no solo la ausencia de errores de un script.
- Preferir cambios pequeños, reversibles y verificables.
- Usar tests deterministas cuando exista lógica comprobable.
- Mantener actualizados README, contexto, decisiones, limitaciones e instrucciones afectadas.
- No introducir secretos, credenciales, datos personales ni datos privados sin una decisión explícita y un tratamiento adecuado.
- Distinguir baseline, deuda preexistente y regresiones introducidas por la rama.
- No reducir el estándar global para hacer pasar un cambio aislado.

## Perfil y límites actuales

El proyecto trabaja con escenas Blender, scripts Python/`bpy`, medidas estructuradas, assets, materiales, texturas, renders y exports cuando existan. La foundation ya dispone de Blender 5.2.1, Blender MCP y Codex CLI instalados, y la comunicación live `Codex → Blender MCP → Blender` está validada. Los controles que sigan sin evidencia se registran como `Pendiente de infraestructura`, `No ejecutado` o `No aplica` según corresponda; no se simula una validación.

No se instalarán herramientas, dependencias, addons, servicios ni Git LFS solo para satisfacer una plantilla de calidad. Los workflows de Node/web del estándar común no se copian en este repositorio.

## Estados de los gates

Cada gate debe informar uno de estos estados:

- `PASS`: se ejecutó el control real y la evidencia respalda el resultado.
- `FAIL`: el control real se ejecutó y encontró un problema.
- `NO APLICA`: el cambio no activa ese control; se explica brevemente por qué.
- `PENDIENTE DE INFRAESTRUCTURA`: el control sería aplicable, pero falta una herramienta o infraestructura aprobada.
- `NO EJECUTADO`: el control es aplicable, pero aún no se ha ejecutado; no permite cerrar el cambio.

Un control no disponible debe marcarse como `NO APLICA` o `PENDIENTE DE INFRAESTRUCTURA`, según corresponda. Nunca debe aparecer como `PASS` inventado. No se deben crear herramientas artificiales, scripts vacíos o comandos ficticios solo para fabricar un check verde.

## Gates potenciales por cambio

La selección es proporcional al alcance y al riesgo:

| Gate | Cuándo aplica | Evidencia esperada |
| --- | --- | --- |
| `git diff --check` | Todo cambio | Salida real y código de retorno. |
| Revisión del diff completo | Todo cambio | Revisión de archivos, alcance y exclusiones. |
| Sintaxis de scripts Python | Scripts `.py`, validadores, presets o automatizaciones | Compilación o comprobación sintáctica real con la herramienta disponible. |
| Ejecución de scripts `bpy` | Scripts que usan Blender/`bpy` | Ejecución relacionada en Blender, con salida y artefactos comprobables. |
| Smoke de apertura de Blender/escena | Cambios de instalación, escena o plantilla cuando Blender esté disponible | Apertura real sin errores bloqueantes. |
| Escena `.blend` abrible y guardable | Creación o modificación de una escena | Archivo abierto y guardado en una ubicación controlada. |
| Dimensiones y transformaciones numéricas | Geometría, mobiliario, cámaras o luces con medidas relevantes | Valores inspeccionados y comparados con el alcance. |
| Contraste con `measurements/` | Toda geometría que represente un espacio real | Correspondencia documentada con la medida estructurada. |
| Verificación de unidades | Escenas, imports, exports o cambios de escala | Unidades explícitas y consistentes, preferentemente metros. |
| Captura de viewport o render | Cambios visuales relevantes | Captura o render identificable, con contexto suficiente. |
| Inspección visual explícita | Cambios de composición, materiales, iluminación o cámara | Observaciones concretas y desviaciones corregidas o aceptadas. |
| Procedencia y licencia de assets | Incorporación o actualización de assets externos | Fuente, licencia/condiciones y dimensiones relevantes registradas. |
| Validación de exports GLB/FBX/u otros | Pipelines o archivos exportados | Export real y comprobación de apertura, escala, materiales o contenido esperado. |
| Secretos/configuración local accidental | Todo cambio, especialmente scripts y configuración | Búsqueda razonable y revisión manual; sin credenciales ni datos privados. |
| Binarios o archivos pesados inesperados | `.blend`, renders, texturas, caches o assets grandes | Alcance, tamaño, procedencia y decisión de versionado revisados. |
| Coste y rendimiento | Cambios que puedan aumentar VRAM, RAM o tiempo de render | Preview o medición proporcional, con límites y hardware considerados. |

La existencia de un gate en esta tabla no implica que se ejecute siempre. La PR debe registrar todos los gates aplicables y explicar los que no apliquen o estén pendientes.

## Baseline y regresiones

Antes de endurecer la infraestructura se debe inventariar qué herramientas, escenas, scripts, exports y pruebas existen. La primera medición forma la baseline y debe conservar los fallos preexistentes visibles.

- Un fallo anterior a la rama se registra como deuda o baseline, no se atribuye al cambio sin evidencia.
- Un fallo nuevo o una degradación respecto a `main` se trata como regresión.
- Una validación ausente no se convierte en un resultado verde.
- Los controles añadidos progresivamente deben corresponder a necesidades reales del proyecto.

## Prioridad de riesgos

Los riesgos se priorizan así:

1. Pérdida o corrupción de escenas o datos de medidas.
2. Discrepancia entre geometría y medidas reales.
3. Operaciones destructivas o irreversibles.
4. Seguridad MCP, Python y acceso a archivos.
5. Secretos o configuración local.
6. Assets y licencias.
7. Escenas, scripts o exports inválidos.
8. Regresiones visuales.
9. Coste computacional excesivo.
10. Mantenibilidad y organización.

## Medidas y unidades

`measurements/` es la fuente de verdad del proyecto. Blender es la representación de esas medidas, no su autoridad.

- No inventar medidas faltantes ni presentarlas como reales.
- Identificar explícitamente cualquier aproximación.
- No cambiar una medida real para “hacer que se vea mejor” o para que una geometría encaje.
- Informar de toda discrepancia entre datos y escena.
- Mantener unidades explícitas y preferir metros como unidad interna de Blender.
- Definir las tolerancias geométricas definitivas antes de modelar el salón real.

## Clasificación T0 / T1 / T2

La clasificación se realiza antes de editar y se eleva si aparece un riesgo mayor durante el análisis.

### T0 — trivial

Incluye documentación, metadata y cambios triviales sin modificación de comportamiento. Requiere:

- alcance breve;
- diff revisado;
- validación proporcional y real.

Ejemplos: corrección textual menor, ajuste de etiqueta o actualización documental sin cambiar el procedimiento ni un contrato.

### T1 — funcional

Incluye scripts `bpy`, presets, materiales, organización de escena, automatización funcional, generación paramétrica, validadores y cambios funcionales reversibles.

Requiere:

- `spec.md`;
- `plan.md`;
- `tasks.md`;
- criterios de aceptación observables;
- validaciones relacionadas;
- evidencia suficiente, incluida evidencia visual cuando el cambio sea visual.

### T2 — complejo o sensible

Incluye cambios en medidas canónicas, sistema global de unidades o coordenadas, MCP, seguridad, ejecución de Python privilegiada, operaciones destructivas, arquitectura de assets, Git LFS, pipelines de import/export, cambios masivos o decisiones difíciles de revertir.

Además de los requisitos de T1, requiere:

- riesgos y mitigaciones;
- invariantes y contratos afectados;
- decisiones técnicas y alternativas descartadas;
- estrategia de reversión y compatibilidad;
- plan de validación ampliado;
- revisión especialmente cuidadosa de datos, seguridad y archivos binarios.

Los artefactos T1/T2 viven en `specs/NNN-feature-name/`. La relación que debe poder reconstruirse es:

```text
necesidad → especificación → criterio de aceptación → tarea → validación → evidencia → PR
```

## Definición de hecho

Un cambio está listo cuando permanece dentro del alcance aprobado, no añade secretos ni datos privados, tiene pruebas o una justificación clara, cumple los gates aplicables, conserva o explica la baseline, actualiza la documentación relevante y deja registrados riesgos, limitaciones y controles no aplicables.

Ningún cambio visual se considera validado solo porque un script terminó sin errores: requiere inspección visual explícita cuando el cambio lo justifique.
