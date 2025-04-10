import asyncio
import json
from typing import Awaitable, Callable, List, Tuple, TypeVar

import pytest
from result import Result
from tinydb import where
from tinydb.table import Table

from tinybridge import AIOBridge

T = TypeVar("T")


async def run_concurrently(
    op: Callable[..., Awaitable[Result[T, Exception]]], *args, **kwargs
) -> List[Result[T, Exception]]:
    """
    Helper function to run operations concurrently.
    """

    repeat = kwargs.pop("repeat", 10)
    tasks = [op(*args) for _ in range(repeat)]
    return await asyncio.gather(*tasks)


def verify_db_file(db_name: str) -> Tuple[bool, str]:
    """
    Verify if the database file exists.
    """

    with open(db_name, "r") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            return False, f"Failed to decode JSON from {db_name}"
        return (
            (True, "Ok")
            if "_default" in data
            else (False, f"Key '_default' not found in {db_name}")
        )


@pytest.mark.asyncio
async def test_table(db_name):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.table, "_default"):
            assert result.is_ok()
            assert isinstance(result.ok(), Table)


@pytest.mark.asyncio
async def test_tables(db_name, multitable_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.tables):
            assert result.is_ok()
            tables = result.ok()
            assert isinstance(tables, set)
            assert {"_default", "_users"}.issubset(tables)


@pytest.mark.asyncio
async def test_drop_tables(db_name, multitable_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.drop_tables):
            assert result.is_ok()
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
        for result in await run_concurrently(bridge.drop_table, table_name):
            assert result.is_ok()
        with open(db_name, "r") as file:
            data = json.load(file)
            assert table_name not in data


@pytest.mark.asyncio
async def test_close(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.close):
            assert result.is_ok()
            insert = await bridge.insert({"name": "Jane"})
            assert isinstance(insert.err(), ValueError)


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
        for result in await run_concurrently(bridge.insert, data):
            assert result.is_ok()
            assert isinstance(result.ok(), int)
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.insert_multiple, data):
            assert result.is_ok()
            ids = result.ok()
            assert isinstance(ids, list)
            assert len(ids) == len(data)
            assert all(isinstance(i, int) for i in ids)
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_all(db_name, default_db, defaults):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.all):
            assert result.is_ok()
            assert result.ok() == defaults
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        (
            where("name") == "Alice",
            [{"name": "Alice", "age": 28, "city": "Wonderland", "active": True}],
        ),
        (where("name") == "Bob", []),
    ],
)
async def test_search(db_name, default_db, query, expected):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.search, query):
            assert result.is_ok()
            assert result.ok() == expected
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.get, query):
            assert result.is_ok()
            assert result.ok() == expected
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.contains, query):
            assert result.is_ok()
            assert result.ok() == expected
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.update, update_data, query):
            assert result.is_ok()
            assert result.ok() == expected
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.update_multiple, query):
            assert result.is_ok()
            assert result.ok() == expected
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.upsert, data, query):
            assert result.is_ok()
            assert result.ok() == expected
        status, message = verify_db_file(db_name)
        assert status, message


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
        for i, result in enumerate(await run_concurrently(bridge.remove, query)):
            assert result.is_ok()
            if i == 0:
                assert result.ok() == expected
            else:
                assert result.ok() == []
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_truncate(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.truncate):
            assert result.is_ok()
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_count(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.count, where("active") == True):
            assert result.is_ok()
            assert result.ok() == 2
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_clear_cache(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.clear_cache):
            assert result.is_ok()
