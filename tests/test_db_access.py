import os

import pytest

from tinybridge import AIOBridge


@pytest.mark.asyncio
async def test_multiple_db_access_with_different_paths(tmp_path):
    bridge1 = AIOBridge(os.path.join(tmp_path, "test1.json"))
    bridge2 = AIOBridge(os.path.join(tmp_path, "test2.json"))

    async with bridge1, bridge2:
        assert bridge1.lock is not bridge2.lock


@pytest.mark.asyncio
async def test_multiple_db_access_with_same_path(tmp_path):
    bridge1 = AIOBridge(os.path.join(tmp_path, "test1.json"))
    bridge2 = AIOBridge(os.path.join(tmp_path, "test1.json"))

    async with bridge1, bridge2:
        assert bridge1.lock is bridge2.lock
