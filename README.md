<img src="https://github.com/user-attachments/assets/48b13c90-92c8-4fd0-8f15-581ff5f4bd62" alt="Alt Text" max-height="450">

# tinybridge

TinyDB bridge implementation for `asyncio`-based applications.

**AIOBridge** is an async-safe adapter for [TinyDB](https://github.com/msiemens/tinydb), inspired by its design and intended for use within `asyncio`-based concurrent tasks. It enables safe and structured interaction with TinyDB from asynchronous Python code.

### Key capabilities

- Implements an async context manager for automatic resource handling
- Ensures concurrency safety via a shared `asyncio.Lock` per DB file path
- Executes all TinyDB operations using `asyncio.to_thread()` for non-blocking behavior
- Provides functional-style error handling via [`Result`](https://github.com/dbrgn/result) objects
- Supports configurable per-operation timeouts for robustness under load

## Installation

Install via pip:

```bash
pip install tinybridge
```

Or using [uv](https://github.com/astral-sh/uv):

```bash
uv add tinybridge
```

> `tinybridge` depends on `tinydb` and `result`, both installed automatically as dependencies.

## Configuration

`AIOBridge` accepts the following options during initialization:

| Parameter      | Type   | Default  | Description                                                   |
| -------------- | ------ | -------- | ------------------------------------------------------------- |
| `path`         | `str`  | —        | Path to the TinyDB JSON file                                  |
| `timeout`      | `int`  | `10`     | Timeout (in seconds) applied to each operation                |
| `tinydb_class` | `type` | `TinyDB` | Optional class to override the default TinyDB implementation  |
| `**kwargs`     | `dict` | —        | Additional keyword arguments passed to the TinyDB constructor |

### Customizing `tinydb_class`

You can override the default `TinyDB` class either by passing a custom class directly or by subclassing `AIOBridge`.

#### Via `tinydb_class` argument

```python
from tinybridge import AIOBridge
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

class InMemoryTinyDB(TinyDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, storage=MemoryStorage, **kwargs)

async with AIOBridge("db.json", tinydb_class=InMemoryTinyDB) as db:
    ...
```

#### By subclassing `AIOBridge`

```python
from tinybridge import AIOBridge
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

class CustomTinyDB(TinyDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, storage=CachingMiddleware(JSONStorage), **kwargs)

class CustomAIOBridge(AIOBridge):
    tinydb_class = CustomTinyDB
```

## Usage Example

Minimal example demonstrating asynchronous insert:

```python
import asyncio
from tinybridge import AIOBridge

async def main():
    async with AIOBridge("db.json") as db:
        result = await db.insert({"name": "Alice"})
        if result.is_ok():
            print("Inserted:", result.unwrap())
        else:
            print("Insert failed:", result.unwrap_err())

asyncio.run(main())
```

All standard TinyDB operations—such as `get`, `search`, `update`, and `remove`—are supported. Each method is wrapped for async compatibility and returns a `Result` object for safe error handling.

## Similar Projects

Alternative community-driven efforts to add async capabilities to TinyDB:

- [`aiotinydb/aiotinydb`](https://github.com/aiotinydb/aiotinydb)
- [`VermiIIi0n/async-tinydb`](https://github.com/VermiIIi0n/async-tinydb)
