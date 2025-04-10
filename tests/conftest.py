import json
import os
from typing import List, Mapping

import pytest


@pytest.fixture
def db_name(tmp_path: str) -> str:
    """
    Fixture to provide a temporary database name.
    """
    return os.path.join(tmp_path, "test.json")


@pytest.fixture
def defaults() -> List[Mapping]:
    return [
        {"name": "John", "age": 30, "city": "New York", "active": True},
        {"name": "Jane", "age": 25, "city": "Los Angeles", "active": False},
        {"name": "Alice", "age": 28, "city": "Wonderland", "active": True},
    ]


@pytest.fixture
def users() -> List[Mapping]:
    return [
        {"name": "Bob", "age": 35, "city": "Chicago", "active": True},
        {"name": "Charlie", "age": 40, "city": "Houston", "active": False},
    ]


@pytest.fixture
def default_db(db_name, defaults):
    """
    Fixture to create a default table for testing.
    """
    db = {"_default": dict(enumerate(defaults, start=1))}
    # db = {
    #     "_default": {
    #         1: {"name": "John", "age": 30, "city": "New York", "active": True},
    #         2: {"name": "Jane", "age": 25, "city": "Los Angeles", "active": False},
    #         3: {"name": "Alice", "age": 28, "city": "Wonderland", "active": True},
    #     }
    # }
    with open(db_name, "w") as file:
        json.dump(db, file)


@pytest.fixture
def multitable_db(db_name, defaults, users):
    """
    Fixture to create a multitable database for testing.
    """
    db = {
        "_default": dict(enumerate(defaults, start=1)),
        "_users": dict(enumerate(users, start=1)),
    }
    # db = {
    #     "_default": {
    #         1: {"name": "John", "age": 30, "city": "New York", "active": True},
    #         2: {"name": "Jane", "age": 25, "city": "Los Angeles", "active": False},
    #         3: {"name": "Alice", "age": 28, "city": "Wonderland", "active": True},
    #     },
    #     "_users": {
    #         1: {"name": "Bob", "age": 35, "city": "Chicago", "active": True},
    #         2: {"name": "Charlie", "age": 40, "city": "Houston", "active": False},
    #     },
    # }
    with open(db_name, "w") as file:
        json.dump(db, file)
