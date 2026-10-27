"""Helpers for reading sharded conda-pypi repodata."""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path

import msgpack

try:
    from compression import zstd  # Python 3.14+ stdlib (PEP 784)
except ImportError:
    from backports import zstd

USER_AGENT = "conda-pypi-repodata-patches"
DEFAULT_CHANNEL = "https://conda.anaconda.org/conda-pypi"
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "cache"))


def fetch(url: str, cache_path: Path, use_cache: bool) -> bytes:
    if use_cache and cache_path.exists():
        return cache_path.read_bytes()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request) as response:
        data = response.read()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return data


def unpack_zst_msgpack(data: bytes):
    return msgpack.unpackb(zstd.decompress(data), raw=False)


def normalize(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {key: normalize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def channel_base(channel: str, subdir: str) -> str:
    return f"{channel.rstrip('/')}/{subdir}"


def load_shard_index(
    channel: str = DEFAULT_CHANNEL,
    subdir: str = "noarch",
    use_cache: bool = False,
) -> dict:
    base = channel_base(channel, subdir)
    return unpack_zst_msgpack(
        fetch(
            f"{base}/repodata_shards.msgpack.zst",
            CACHE_DIR / subdir / "repodata_shards.msgpack.zst",
            use_cache,
        )
    )


def shard_hash(index: dict, name: str) -> str | None:
    value = index.get("shards", {}).get(name)
    if value is None:
        return None
    return value.hex() if isinstance(value, bytes) else str(value)


def load_shard(
    hex_hash: str,
    channel: str = DEFAULT_CHANNEL,
    subdir: str = "noarch",
    use_cache: bool = False,
) -> dict:
    base = channel_base(channel, subdir)
    return unpack_zst_msgpack(
        fetch(
            f"{base}/shards/{hex_hash}.msgpack.zst",
            CACHE_DIR / subdir / "shards" / f"{hex_hash}.msgpack.zst",
            use_cache,
        )
    )
