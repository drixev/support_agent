# Cambios: transiciones de estado + servidor MCP

Explicación de los cambios posteriores al commit inicial (`97530ec chore: init project + setup`).

## La idea general

Antes, el proyecto era una **API de tickets de soporte** (FastAPI) que solo permitía **leer** tickets: buscarlos y verlos.

Con estos cambios pasan dos cosas:

1. Ahora se puede **cambiar el estado** de un ticket (abrirlo, ponerlo en progreso, resolverlo, cerrarlo), con reglas que impiden saltos absurdos.
2. Se añade un **servidor MCP**, que es una "puerta" para que un agente de IA (por ejemplo, uno hecho con LangGraph) use los tickets como herramientas.

El proyecto sigue una **arquitectura hexagonal**, con capas. Los cambios van de dentro hacia fuera:

```
domain/          → las reglas del negocio (no sabe nada de bases de datos ni de HTTP)
application/     → los casos de uso ("cambiar el estado de un ticket")
infraestructure/ → cómo se guardan los datos (por ahora, en memoria)
mcp_server/      → NUEVO: cómo se expone todo eso a un LLM
```

---

## 1. `pyproject.toml`: arreglos y una dependencia nueva

- Había **dos errores de escritura** que hacían que se ignorara la configuración sin avisar:
  - `requries-python` → `requires-python`
  - `uvicorn[standar]` → `uvicorn[standard]` (con el nombre mal escrito no se instalaban los extras de uvicorn)
- Se añade `mcp` como dependencia normal, porque el servidor la necesita para funcionar.
- Se añade `mcp[cli]` solo en `dev`. Trae el comando `mcp dev` y el *Inspector*, una interfaz web para probar las herramientas a mano. En producción no hace falta.

## 2. Dominio: las reglas del negocio

**`domain/models.py`**: se añade `ALLOWED_TRANSITIONS`, un diccionario que dice **a qué estados se puede pasar desde cada estado**:

| Desde         | Puede pasar a                 |
|---------------|-------------------------------|
| `open`        | `in_progress`, `closed`       |
| `in_progress` | `resolved`, `open`            |
| `resolved`    | `closed`, `in_progress`       |
| `closed`      | nada (es el estado final)     |

Esto es una **máquina de estados**. Se usa `frozenset` para que nadie pueda modificar las reglas por accidente mientras el programa corre.

**`domain/errros.py`**: nuevo error `InvalidStatusTransitionError`. Si alguien intenta pasar de `open` a `resolved` sin pasar por `in_progress`, se lanza este error con un mensaje claro.

**`domain/ports.py`**: el "contrato" del repositorio (`TicketRepository`) gana el método `save()`. Un **puerto** es una interfaz: dice *qué* debe saber hacer un repositorio, no *cómo*. Como ahora hay que guardar cambios, el contrato necesita ese método.

## 3. Infraestructura: `in_memory.py`

Se implementa `save()` en el repositorio en memoria: guarda el ticket en un diccionario usando su `id` como clave. Cuando más adelante haya PostgreSQL, se creará otro repositorio con su propio `save()`, y el resto del código no tendrá que cambiar. Para eso sirve el puerto.

## 4. Aplicación: `ticket_service.py`

Nuevo caso de uso `update_status()`:

```python
ticket = await self.get_ticket(ticket_id)          # 1. lo busca (si no existe → TicketNotFoundError)
if new_status not in ALLOWED_TRANSITIONS[...]:     # 2. comprueba la regla
    raise InvalidStatusTransitionError(...)
updated = ticket.model_copy(update={...})          # 3. crea una COPIA con el nuevo estado
await self._repo.save(updated)                     # 4. la guarda
```

Fíjate en el paso 3: `Ticket` es **inmutable** (`frozen=True`), así que no se puede hacer `ticket.status = ...`. Se crea una copia nueva con el cambio. Así se evitan errores en los que alguien modifica un objeto que otra parte del código está usando.

## 5. Lo nuevo: `mcp_server/server.py`

**¿Qué es MCP?** Es un protocolo estándar para que un LLM descubra y use "herramientas" (*tools*). El servidor publica una lista del tipo "tengo estas funciones, con estos parámetros", y el agente decide cuándo llamarlas.

Las partes del archivo:

- **Logs a `stderr`**: el servidor se comunica por `stdio`, es decir, los mensajes JSON-RPC viajan por la salida estándar. Si escribieras un `print()` normal, mezclarías basura con esos mensajes y romperías la comunicación. Por eso los logs van a `stderr`.
- **`lifespan`**: código que se ejecuta una vez al arrancar el servidor. Crea el `TicketService` con datos de ejemplo (`seeded()`). Es el mismo concepto que el `lifespan` de FastAPI, y más adelante ahí se abrirá la conexión a Postgres.
- **`TicketView` / `SearchResult`**: son **DTOs**, objetos que definen qué datos salen hacia fuera. No se devuelve la entidad `Ticket` tal cual (por ejemplo, `created_at` no se expone). Así, si cambias el modelo interno, no rompes el contrato con el agente.
- **`TicketId`**: un tipo con validación (`TCK-0000`). Si el LLM se inventa un ID como `"abc"`, se rechaza antes de llegar a tu código.
- **Las 3 tools**:

| Tool                   | Qué hace                                                          | Anotación     |
|------------------------|-------------------------------------------------------------------|---------------|
| `search_tickets`       | Busca por palabras clave (2–200 caracteres, máximo 20 resultados) | solo lectura  |
| `get_ticket`           | Devuelve un ticket por su ID                                      | solo lectura  |
| `update_ticket_status` | Cambia el estado y pide un `reason` obligatorio                   | **escritura** |

- **`ToolAnnotations`**: son "pistas" para el cliente. `readOnlyHint=True` le dice al agente que la herramienta no cambia nada. Más adelante, en LangGraph, podrás usar esto para pedir **aprobación humana** antes de ejecutar las herramientas de escritura.
- **Docstrings**: aquí no son solo documentación. **El LLM las lee** para decidir qué herramienta usar. Por eso están en inglés y explican cuándo usar cada una.
- **`reason` + log `AUDIT`**: cada cambio de estado queda registrado con su motivo, como una auditoría básica.

## 6. Tests: `tests/test_mcp_server.py`

Son tests de **integración de verdad**: arrancan el servidor como un proceso aparte y le hablan por MCP, igual que lo haría un agente. Comprueban que:

1. Existen las 3 tools y sus anotaciones son correctas.
2. La búsqueda de `"SSO"` devuelve un resultado estructurado (`TCK-0001`).
3. Un ID inválido devuelve un **error de la tool**, no tumba el servidor. Esto es importante: el LLM ve el error y puede corregirse.
4. Saltar de `open` a `resolved` falla, y pasar de `open` a `in_progress` funciona.

---

## Pendientes detectados

1. En el docstring de `update_ticket_status` pone `close` y `resovled`; deberían ser `closed` y `resolved`. Como el LLM lee ese texto, una errata puede llevarlo a enviar un valor que no existe.
2. El docstring de `search_tickets` dice `get_tickets`, pero la tool se llama `get_ticket`.
3. El archivo `errros.py` tiene una errata en el nombre (`errors.py`). No es urgente, pero cuanto más tarde se renombre, más imports habrá que tocar.
4. A `mcp_server/` le falta un `__init__.py`, a diferencia del resto de paquetes. Funciona igual (Python lo trata como *namespace package*), pero es inconsistente.
