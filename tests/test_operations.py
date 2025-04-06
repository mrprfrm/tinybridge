import json

import pytest
from result import Err, Ok
from tinydb import where
from tinydb.table import Table

from tinybridge import AIOBridge


@pytest.mark.asyncio
async def test_table(db_name):
    async with AIOBridge(db_name) as bridge:
        match await bridge.table("_default"):
            case Ok(table):
                assert table is not None
                assert isinstance(table, Table)
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_tables(db_name, multitable_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.tables():
            case Ok(tables):
                assert isinstance(tables, set)
                assert {"_default", "_users"}.issubset(tables)
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_drop_tables(db_name, multitable_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.drop_tables():
            case Ok(result):
                assert result is None
            case Err(e):
                assert False, f"Unexpected error: {e}"
        with open(db_name, "r") as file:
            data = json.load(file)
            assert "_default" not in data
            assert "_users" not in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "table_name",
    [
        "_default",
        "_users",
    ],
)
async def test_drop_table(db_name, multitable_db, table_name):
    async with AIOBridge(db_name) as bridge:
        match await bridge.drop_table(table_name):
            case Ok(result):
                assert result is None
            case Err(e):
                assert False, f"Unexpected error: {e}"
        with open(db_name, "r") as file:
            data = json.load(file)
            assert table_name not in data


@pytest.mark.asyncio
async def test_close(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.close():
            case Ok(result):
                assert result is None
            case Err(e):
                assert False, f"Unexpected error: {e}"
        match await bridge.insert({"name": "Jane"}):
            case Ok(result):
                assert True, "Expected an error when using a closed bridge"
            case Err(e):
                assert isinstance(e, ValueError)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        {"name": "Jane"},
        {"name": "John", "age": 30},
        {"name": "Alice", "age": 25, "city": "Wonderland", "active": True},
    ],
)
async def test_insert(db_name, data):
    async with AIOBridge(db_name) as bridge:
        match await bridge.insert(data):
            case Ok(result):
                assert isinstance(result, int)
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"name": "Jane"}],
        [{"name": "Alice", "age": 25}, {"name": "John", "age": 30}],
    ],
)
async def test_insert_multiple(db_name, data):
    async with AIOBridge(db_name) as bridge:
        match await bridge.insert_multiple(data):
            case Ok(result):
                assert isinstance(result, list)
                assert len(result) == len(data)
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_all(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.all():
            case Ok(result):
                assert isinstance(result, list)
                assert len(result) == 3
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        (where("name") == "Alice", 1),
        (where("name") == "Bob", 0),
    ],
)
async def test_search(db_name, default_db, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.search(query):
            case Ok(result):
                assert isinstance(result, list)
                assert len(result) == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        (
            where("name") == "Alice",
            {"name": "Alice", "age": 28, "city": "Wonderland", "active": True},
        ),
        (where("name") == "Bob", None),
    ],
)
async def test_get(db_name, default_db, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.get(query):
            case Ok(result):
                assert result == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        (where("name") == "Alice", True),
        (where("name") == "Bob", False),
    ],
)
async def test_contains(db_name, default_db, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.contains(query):
            case Ok(result):
                assert isinstance(result, bool)
                assert result == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "update_data,query,expected",
    [
        ({"status": "updated"}, where("name") == "Alice", [3]),
        ({"status": "none"}, where("name") == "Bob", []),
    ],
)
async def test_update(db_name, default_db, update_data, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.update(update_data, query):
            case Ok(result):
                assert isinstance(result, list)
                assert result == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        (
            [
                ({"status": "updated"}, where("name") == "Alice"),
                ({"age": 28}, where("name") == "John"),
            ],
            [1, 3],
        ),
        (
            [
                ({"status": "none"}, where("name") == "Bob"),
            ],
            [],
        ),
    ],
)
async def test_update_multiple(db_name, default_db, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.update_multiple(query):
            case Ok(result):
                assert isinstance(result, list)
                assert result == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,query,expected",
    [
        ({"status": "updated"}, where("name") == "Alice", [3]),
        ({"name": "Bob", "status": "new"}, where("name") == "Bob", [4]),
    ],
)
async def test_upsert(db_name, default_db, data, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.upsert(data, query):
            case Ok(result):
                assert isinstance(result, list)
                assert result == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        (where("name") == "Alice", [3]),
        (where("name") == "Bob", []),
    ],
)
async def test_remove(db_name, default_db, query, expected):
    async with AIOBridge(db_name) as bridge:
        match await bridge.remove(query):
            case Ok(result):
                assert isinstance(result, list)
                assert result == expected
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_truncate(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.truncate():
            case Ok(result):
                assert result is None
            case Err(e):
                assert False, f"Unexpected error: {e}"
        with open(db_name, "r") as file:
            data = json.load(file)
            assert "_default" in data
            assert len(data["_default"]) == 0


@pytest.mark.asyncio
async def test_count(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.count(where("active") == True):
            case Ok(result):
                assert isinstance(result, int)
                assert result == 2
            case Err(e):
                assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_clear_cache(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        match await bridge.clear_cache():
            case Ok(result):
                assert result is None
            case Err(e):
                assert False, f"Unexpected error: {e}"
