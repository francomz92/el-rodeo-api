# El Rodeo API

API para la gestión ganadera y financiera de pequeños productores. Construida con **FastAPI**, **SQLAlchemy async**, **PostgreSQL** y **Redis**.

## Stack

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI + Uvicorn (async) |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Base de datos | PostgreSQL 16 |
| Cache | Redis 7 |
| Auth | JWT (PyJWT) + bcrypt |
| Background tasks | Celery + Redis |
| Validación | Pydantic v2 |
| Logging | Loguru |

## Arquitectura

Clean Architecture / Hexagonal con 4 bounded contexts:

- **auth** — Autenticación y usuarios
- **cattle** — Gestión de animales
- **finance** — Compras, insumos
- **market** — Ventas

Cada contexto sigue la estructura: `domain/` → `application/` → `infrastructure/`.

## Requisitos

- Python >= 3.12
- PostgreSQL 16
- Redis 7
- uv (package manager)

## Setup local

```bash
# Instalar dependencias
uv sync

# Copiar y configurar variables de entorno
cp .env.example .env

# Ejecutar migraciones
uv run alembic upgrade head

# Iniciar servidor de desarrollo
uv run uvicorn src.main:app --reload
```

## Testing

```bash
# Todos los tests
uv run pytest

# Con coverage
uv run pytest --cov=src

# Solo unitarios
uv run pytest tests/unit

# Solo integración
uv run pytest tests/integration
```

## Calidad

```bash
# Linter
uv run ruff check src/

# Type checker
uv run pyright

# Formatter
uv run ruff format src/
```
