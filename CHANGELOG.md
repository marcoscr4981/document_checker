# Changelog

Todos los cambios relevantes de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

## [1.0.0] - 2026-11-24

### Añadido

- Herramienta CLI para identificar y validar documentos españoles.
- Normalización de documentos mediante eliminación de espacios, puntos y guiones.
- Identificación y validación de DNI, NIE y CIF.
- Cálculo automático de letras de control de DNI y NIE.
- Cálculo y comprobación de controles numéricos y alfabéticos de CIF.
- Identificación del tipo de entidad de un CIF.
- Consulta de provincias mediante referencias históricas de CIF.
- Identificación y comprobación del formato de NIF especiales K, L y M.
- Advertencia cuando no se verifica el carácter de control.
- Gestión de errores mediante excepciones `ValueError`.
- Pruebas unitarias con `unittest`, incluyendo la interfaz CLI.
- Documentación de instalación, uso y limitaciones en `README.md`.
