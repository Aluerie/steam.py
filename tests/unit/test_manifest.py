from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from steam import manifest as manifest_module
from steam.manifest import ManifestPath
from steam.protobufs.content_manifest import PayloadFileMappingChunkData

CONTENT = bytes(range(256)) * 4  # 1024 bytes
CHUNK_SIZE = 100  # chunks: [0, 100), [100, 200), ..., [1000, 1024)


class FakeServer:
    def __init__(self, chunks: dict[str, bytes]) -> None:
        self.chunks = chunks
        self.requested: list[str] = []

    async def get(self, path: str) -> bytes:
        self.requested.append(path)
        return self.chunks[path.rsplit("/", 1)[-1]]


def fake_path(*, key: bytes | None = b"key", directory: bool = False) -> tuple[Any, FakeServer]:
    chunks: list[PayloadFileMappingChunkData] = []
    data: dict[str, bytes] = {}
    for start in range(0, len(CONTENT), CHUNK_SIZE):
        piece = CONTENT[start : start + CHUNK_SIZE]
        sha = start.to_bytes(20, "big")
        chunks.append(PayloadFileMappingChunkData(sha=sha, offset=start, cb_original=len(piece)))
        data[sha.hex()] = piece
    server = FakeServer(data)
    path = SimpleNamespace(
        _manifest=SimpleNamespace(_key=key, server=server, depot_id=373301),
        size=len(CONTENT),
        chunks=chunks,
        is_dir=lambda: directory,
    )
    return path, server


@pytest.fixture(autouse=True)
def no_encryption(monkeypatch: pytest.MonkeyPatch) -> None:
    # The fake chunks are stored as plain bytes;
    monkeypatch.setattr(manifest_module.utils, "symmetric_decrypt", lambda data, key: data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("offset", "size", "chunks_downloaded"),
    [
        (0, 10, 1),  # start of the first chunk
        (150, 20, 1),  # inside one chunk
        (190, 20, 2),  # across a chunk border
        (100, 100, 1),  # exactly one chunk
        (50, 500, 6),  # many chunks
        (1000, 100, 1),  # past the end: only what's there
        (0, 1024, 11),  # the whole file
    ],
)
async def test_read_range(offset: int, size: int, chunks_downloaded: int) -> None:
    path, server = fake_path()
    assert await ManifestPath.read_range(path, offset, size) == CONTENT[offset : offset + size]
    assert len(server.requested) == chunks_downloaded
    assert all(request.startswith("depot/373301/chunk/") for request in server.requested)


@pytest.mark.asyncio
@pytest.mark.parametrize(("offset", "size"), [(2000, 10), (10, 0)])
async def test_read_range_empty(offset: int, size: int) -> None:
    path, server = fake_path()
    assert await ManifestPath.read_range(path, offset, size) == b""
    assert server.requested == []


@pytest.mark.asyncio
async def test_read_range_errors() -> None:
    with pytest.raises(ValueError, match="negative"):
        await ManifestPath.read_range(fake_path()[0], -1, 10)
    with pytest.raises(RuntimeError, match="no key"):
        await ManifestPath.read_range(fake_path(key=None)[0], 0, 10)
    with pytest.raises(IsADirectoryError):
        await ManifestPath.read_range(fake_path(directory=True)[0], 0, 10)
