# Plan: [nombre del cambio]

## Especificación relacionada

- `spec.md`

## Enfoque

[Resume la solución y por qué respeta el alcance, las medidas y las restricciones de seguridad.]

## Archivos y áreas afectadas

- Crear: [rutas previstas.]
- Modificar: [rutas previstas.]
- Escenas/assets/medidas: [rutas o `No aplica`.]
- Pruebas/validadores/evidencia: [rutas o `No aplica`.]

## Fases

1. [Preparar o documentar el contrato.]
2. [Implementar el cambio mínimo.]
3. [Ejecutar validaciones y obtener evidencia.]
4. [Revisar diff y preparar la PR.]

## Validaciones

- `git diff --check`.
- [Validación determinista relacionada, o explicación de `No aplica`.]
- [Apertura, dimensiones, unidades, medidas, viewport/render, export o coste cuando aplique.]
- [Revisión de secretos, archivos pesados y licencia de assets cuando aplique.]

Los controles no disponibles se registran como `PENDIENTE DE INFRAESTRUCTURA`; no se sustituyen por checks artificiales.

## Estrategia de reversión y compatibilidad

[Explica cómo volver al estado anterior, preservar la escena canónica y mantener compatibilidad con medidas, scripts, assets o exports. Para T1 indica `Reversión mediante Git y/o variante separable`; para T2 detalla la estrategia.]

## Dependencias externas

[Lista herramientas, assets, licencias o servicios externos requeridos. Si no hay, indica `Ninguna`; no instalar dependencias sin autorización.]
