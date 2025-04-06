import json
import os

import pytest


@pytest.fixture
def db_name(tmp_path):
    """
    Fixture to provide a temporary database name.
    """
    return os.path.join(tmp_path, "test.json")


@pytest.fixture
def default_db(db_name):
    """
    Fixture to create a default table for testing.
    """
    db = {
        "_default": {
            1: {"name": "John", "age": 30, "city": "New York", "active": True},
            2: {"name": "Jane", "age": 25, "city": "Los Angeles", "active": False},
            3: {"name": "Alice", "age": 28, "city": "Wonderland", "active": True},
        }
    }
    with open(db_name, "w") as file:
        json.dump(db, file)


@pytest.fixture
def multitable_db(db_name):
    """
    Fixture to create a multitable database for testing.
    """
    db = {
        "_default": {
            1: {"name": "John", "age": 30, "city": "New York", "active": True},
            2: {"name": "Jane", "age": 25, "city": "Los Angeles", "active": False},
            3: {"name": "Alice", "age": 28, "city": "Wonderland", "active": True},
        },
        "_users": {
            1: {"name": "Bob", "age": 35, "city": "Chicago", "active": True},
            2: {"name": "Charlie", "age": 40, "city": "Houston", "active": False},
        },
    }
    with open(db_name, "w") as file:
        json.dump(db, file)
