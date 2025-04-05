# DBAdapter Simple Proxy implementation

import asyncio
import functools
import weakref
from typing import Any

from result import Err, Ok, Result
from tinydb import TinyDB


class AIOBridge:
    """
    Async-safe proxy adapter for TinyDB.

    This adapter wraps TinyDB in an asyncio-compatible context, allowing safe concurrent
    access and dynamic method proxying. Each method call is executed in a thread, wrapped
    with a timeout, and returns a `Result` (`Ok` or `Err`) to encourage safe functional error handling.
    """

    __locks = weakref.WeakValueDictionary()

    tinydb_class = TinyDB

    def __init__(self, path: str, *, timeout: int = 10, **kwargs):
        """
        Initialize the AIOBridge.

        Args:
            path (str): Path to the TinyDB JSON file.
            timeout (int, optional): Timeout in seconds for each DB operation. Defaults to 10.
            *args: Positional arguments forwarded to TinyDB.
            **kwargs: Keyword arguments forwarded to TinyDB.
        """
        self._path = path
        self._timeout = timeout
        self._db = None
        self._kwargs = kwargs
        self._tinydb_class = self._kwargs.pop("tinydb_class", self.tinydb_class)

        if path not in AIOBridge.__locks:
            self.lock = asyncio.Lock()
            AIOBridge.__locks[path] = self.lock
        else:
            self.lock = AIOBridge.__locks[path]

    async def __aenter__(self):
        self._db = self._tinydb_class(self._path, **self._kwargs)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._db is not None:
            self._db.close()

    def __getattr__(self, name: str):
        """
        Intercept TinyDB method calls and wrap them as async functions.

        The wrapped methods:
        - Run in a background thread using `asyncio.to_thread`
        - Are protected by an `asyncio.Lock` to prevent race conditions
        - Use a timeout (`self._timeout`)
        - Return a `Result` object (Ok or Err)

        Args:
            name (str): The attribute/method name to retrieve from TinyDB.

        Returns:
            Callable: An awaitable proxy method that returns a `Result`.
        """
        db_attr = getattr(self._db, name, None)
        if callable(db_attr):

            @functools.wraps(db_attr)
            async def wrapper(*args, **kwargs) -> Result[Any, Exception]:
                async with self.lock:
                    try:
                        result = await asyncio.wait_for(
                            asyncio.to_thread(
                                functools.partial(db_attr, *args, **kwargs)
                            ),
                            timeout=self._timeout,
                        )
                        return Ok(result)
                    except Exception as e:
                        return Err(e)

            return wrapper

        return db_attr
