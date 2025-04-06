import asyncio
import json
from typing import Any, Callable, List, Tuple

import pytest
from result import Err, Ok, Result
from tinydb import where
from tinydb.table import Table

from tinybridge import AIOBridge


async def run_concurrently(
    op: Callable, *arguments, **kwargs
) -> List[Result[Any, Exception]]:
    """
    Helper function to run operations concurrently.
    """

    repeat = kwargs.pop("repeat", 10)
    tasks = [op(*arguments) for _ in range(repeat)]
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
            match result:
                case Ok(table):
                    assert table is not None
                    assert isinstance(table, Table)
                case Err(e):
                    assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_tables(db_name, multitable_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.tables):
            match result:
                case Ok(tables):
                    assert isinstance(tables, set)
                    assert {"_default", "_users"}.issubset(tables)
                case Err(e):
                    assert False, f"Unexpected error: {e}"


@pytest.mark.asyncio
async def test_drop_tables(db_name, multitable_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.drop_tables):
            match result:
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
        for result in await run_concurrently(bridge.drop_table, table_name):
            match result:
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

        for result in await run_concurrently(bridge.insert, {"name": "Jane"}):
            match result:
                case Ok(result):
                    assert False, "Expected an error when using a closed bridge"
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
        for result in await run_concurrently(bridge.insert, data):
            match result:
                case Ok(result):
                    assert isinstance(result, int)
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            match result:
                case Ok(result):
                    assert isinstance(result, list)
                    assert len(result) == len(data)
                case Err(e):
                    assert False, f"Unexpected error: {e}"
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_all(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.all):
            match result:
                case Ok(result):
                    assert isinstance(result, list)
                    assert len(result) == 3
                case Err(e):
                    assert False, f"Unexpected error: {e}"
        status, message = verify_db_file(db_name)
        assert status, message


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
        for result in await run_concurrently(bridge.search, query):
            match result:
                case Ok(result):
                    assert isinstance(result, list)
                    assert len(result) == expected
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            match result:
                case Ok(result):
                    assert result == expected
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            match result:
                case Ok(result):
                    assert isinstance(result, bool)
                    assert result == expected
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            match result:
                case Ok(result):
                    assert isinstance(result, list)
                    assert result == expected
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            match result:
                case Ok(result):
                    assert isinstance(result, list)
                    assert result == expected
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            match result:
                case Ok(result):
                    assert isinstance(result, list)
                    assert result == expected
                case Err(e):
                    assert False, f"Unexpected error: {e}"
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
            if i == 0:
                match result:
                    case Ok(result):
                        assert isinstance(result, list)
                        assert result == expected
                    case Err(e):
                        assert False, f"Unexpected error: {e}"
            else:
                match result:
                    case Ok(result):
                        assert isinstance(result, list)
                        assert result == []
                    case Err(e):
                        assert False, f"Unexpected error: {e}"

        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_truncate(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.truncate):
            match result:
                case Ok(result):
                    assert result is None
                case Err(e):
                    assert False, f"Unexpected error: {e}"
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_count(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.count, where("active") == True):
            match result:
                case Ok(result):
                    assert isinstance(result, int)
                    assert result == 2
                case Err(e):
                    assert False, f"Unexpected error: {e}"
        status, message = verify_db_file(db_name)
        assert status, message


@pytest.mark.asyncio
async def test_clear_cache(db_name, default_db):
    async with AIOBridge(db_name) as bridge:
        for result in await run_concurrently(bridge.clear_cache):
            match result:
                case Ok(result):
                    assert result is None
                case Err(e):
                    assert False, f"Unexpected error: {e}"
