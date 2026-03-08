# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [1.1.0] - 2026-03-08

### Fixed
- **Desactivación de empleados**: Corregido error `AttributeError` al desactivar empleados. El modelo `Shift` usa `shift_date` en lugar de `date` como nombre de columna.

## [1.0.0] - Versión actual en producción

### Added
- Sistema inicial de gestión de empleados
- Módulo de control de asistencia y fichajes
- Sistema de gestión de nóminas
- Módulo de solicitudes de ausencias
- Dashboard de reportes
- Sistema de gestión de horarios y turnos
- Autenticación y autorización con JWT
- Sistema de gestión de días festivos
