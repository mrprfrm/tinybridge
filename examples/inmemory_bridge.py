import asyncio
from typing import Any, List

from result import Ok, Result
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from tinydb.table import Document

from tinybridge import AIOBridge


class InMemoryTinyDB(TinyDB):
    """
    Custom TinyDB class for testing purposes.
    """

    default_storage_class = MemoryStorage


class InMemoryAIOBridge(AIOBridge):
    """
    Custom bridge class to test attribute access.
    """

    tinydb_class = InMemoryTinyDB

    def __init__(self, *, timeout: int = 10, **kwargs):
        super().__init__(None, timeout=timeout, **kwargs)

    async def getmany(self, doc_ids: List[Any]) -> Result[List[Document], Exception]:
        """
        Custom search method to test attribute access.
        """
        result = []
        table = self.db._read_table()
        for doc_id in doc_ids:
            if doc_id in table:
                result.append(table[doc_id])

        return Ok(result)


async def main():
    async with InMemoryAIOBridge() as bridge:
        result = await bridge.insert({"name": "John", "age": 30})
        print(f"Inserted document ID: {result}")

        doc_ids = ["1", "2", "3"]
        result = await bridge.getmany(doc_ids)
        print(f"Retrieved documents: {result}")


if __name__ == "__main__":
    asyncio.run(main())
