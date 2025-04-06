# AIOBridge implementation

import asyncio
import functools
import weakref
from typing import Any, Callable, Iterable, List, Mapping, Optional, Set, Tuple, Union

from result import Err, Ok, Result
from tinydb import TinyDB
from tinydb.queries import QueryLike
from tinydb.table import Document, Table


class AIOBridge:
    """
    Async-safe proxy adapter for TinyDB.

    This adapter wraps TinyDB in an asyncio-compatible context, allowing safe concurrent
    access and dynamic method proxying. Each method call is executed in a thread, wrapped
    with a timeout, and returns a `Result` (`Ok` or `Err`) to encourage safe functional error handling.
    """

    __locks = weakref.WeakValueDictionary()

    tinydb_class = TinyDB

    def __init__(self, path: Union[str, None], *, timeout: int = 10, **kwargs):
        """Initialize AIOBridge.

        Args:
            path (Union[str, None]): Path to the TinyDB file or None.
            timeout (int): Operation timeout in seconds.
            **kwargs: Passed to TinyDB constructor.
        """

        # AIOBridge is a proxy over TinyDB, and cannot enforce the exact
        # constructor signature of a custom TinyDB subclass.
        #
        # Some implementations may require a 'path', while others (like in-memory
        # storage) may not accept it at all.
        #
        # To support both cases, 'path' is required but allowed to be None.
        # If not None, it's passed explicitly to the TinyDB constructor.

        self._timeout = timeout

        if path is not None:
            kwargs["path"] = path
        tinydb_class = kwargs.pop("tinydb_class", self.tinydb_class)
        self._db = tinydb_class(**kwargs)

        path = path or "default"
        if path not in AIOBridge.__locks:
            self.lock = asyncio.Lock()
            AIOBridge.__locks[path] = self.lock
        else:
            self.lock = AIOBridge.__locks[path]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._db is not None:
            self._db.close()

    async def __execute(self, op, *args, **kwargs) -> Result[Any, Exception]:
        """Run a TinyDB operation in a thread-safe, async-safe context."""

        # This pattern is chosen over fully dynamic proxying (e.g., __getattr__)
        # with static type extraction because such approaches introduce
        # excessive complexity, especially for maintaining proper type hints.
        #
        # Instead, explicit method wrapping—combined with this core execution
        # logic—gives us the best trade-off: clean runtime behavior with full
        # static typing support and LSP compatibility.

        async with self.lock:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(functools.partial(op, *args, **kwargs)),
                    timeout=self._timeout,
                )
                return Ok(result)
            except Exception as e:
                return Err(e)

    @property
    def db(self) -> TinyDB:
        """Return the underlying TinyDB instance."""
        return self._db

    # DB level methods
    async def table(self, name: str, **kwargs) -> Result[Table, Exception]:
        """Access or create a table by name."""
        return await self.__execute(self.db.table, name, **kwargs)

    async def tables(self) -> Result[Set[str], Exception]:
        """Return the set of table names."""
        return await self.__execute(self.db.tables)

    async def drop_tables(self) -> Result[None, Exception]:
        """Remove all tables."""
        return await self.__execute(self.db.drop_tables)

    async def drop_table(self, name: str) -> Result[None, Exception]:
        """Remove a specific table by name."""
        return await self.__execute(self.db.drop_table, name)

    async def close(self) -> Result[None, Exception]:
        """Close the database (if not already closed)."""
        return await self.__execute(self.db.close)

    # Table level methods
    async def insert(self, document: Mapping) -> Result[int, Exception]:
        """Insert a single document."""
        return await self.__execute(self.db.insert, document)

    async def insert_multiple(
        self, documents: Iterable[Mapping]
    ) -> Result[List[int], Exception]:
        """Insert multiple documents."""
        return await self.__execute(self.db.insert_multiple, documents)

    async def all(self) -> Result[List[Document], Exception]:
        """Return all documents in the table."""
        return await self.__execute(self.db.all)

    async def search(self, cond: QueryLike) -> Result[List[Document], Exception]:
        """Return documents matching the given query."""
        return await self.__execute(self.db.search, cond)

    async def get(
        self,
        cond: Optional[QueryLike] = None,
        doc_id: Optional[int] = None,
        doc_ids: Optional[List[int]] = None,
    ) -> Result[Optional[Union[Document, List[Document]]], Exception]:
        """Get a document by query, doc_id, or list of IDs."""
        return await self.__execute(self.db.get, cond, doc_id, doc_ids)

    async def contains(
        self, cond: Optional[QueryLike] = None, doc_id: Optional[int] = None
    ) -> Result[bool, Exception]:
        """Check if a document exists by query or doc_id."""
        return await self.__execute(self.db.contains, cond, doc_id)

    async def update(
        self,
        fields: Union[Mapping, Callable[[Mapping], None]],
        cond: Optional[QueryLike] = None,
        doc_ids: Optional[Iterable[int]] = None,
    ) -> Result[List[int], Exception]:
        """Update documents by query or doc_ids."""
        return await self.__execute(self.db.update, fields, cond, doc_ids)

    async def update_multiple(
        self,
        updates: Iterable[Tuple[Union[Mapping, Callable[[Mapping], None]], QueryLike]],
    ) -> Result[List[int], Exception]:
        """Update multiple document-query pairs."""
        return await self.__execute(self.db.update_multiple, updates)

    async def upsert(
        self, document: Mapping, cond: Optional[QueryLike] = None
    ) -> Result[List[int], Exception]:
        """Update if match found, insert otherwise."""
        return await self.__execute(self.db.upsert, document, cond)

    async def remove(
        self,
        cond: Optional[QueryLike] = None,
        doc_ids: Optional[Iterable[int]] = None,
    ) -> Result[List[int], Exception]:
        """Remove documents by query or doc_ids."""
        return await self.__execute(self.db.remove, cond, doc_ids)

    async def truncate(self) -> Result[None, Exception]:
        """Remove all documents from the table."""
        return await self.__execute(self.db.truncate)

    async def count(self, cond: QueryLike) -> Result[int, Exception]:
        """Return the number of documents matching the query."""
        return await self.__execute(self.db.count, cond)

    async def clear_cache(self) -> Result[None, Exception]:
        """Clear the query cache."""
        return await self.__execute(self.db.clear_cache)
