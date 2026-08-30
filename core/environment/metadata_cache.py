"""Validation policy for cached official metadata."""
from __future__ import annotations
from enum import Enum
from urllib.parse import urlparse
import time

class CachePolicy(str, Enum):
    FRESH_CACHE='FRESH_CACHE'; STALE_CACHE='STALE_CACHE'; CORRUPTED_CACHE='CORRUPTED_CACHE'; NO_CACHE='NO_CACHE'

def inspect_cached_metadata(payload, *, provider: str, allowed_hosts: set[str], architecture: str = 'x86_64', ttl: int = 3600, now=None):
    if not isinstance(payload, dict): return CachePolicy.CORRUPTED_CACHE, None
    try:
        metadata=payload['metadata']; source=payload['source']; timestamp=float(payload['timestamp'])
        if payload.get('state') != 'CACHED_OFFICIAL_METADATA' or not metadata or not isinstance(source, str):
            return CachePolicy.CORRUPTED_CACHE, None
        if metadata.get('architecture') not in {architecture, None}: return CachePolicy.CORRUPTED_CACHE, None
        url=urlparse(metadata.get('download_url',''))
        if url.scheme != 'https' or url.hostname not in allowed_hosts: return CachePolicy.CORRUPTED_CACHE, None
        if provider.lower() in {'eclipse adoptium','adoptium'} and not metadata.get('checksum'): return CachePolicy.CORRUPTED_CACHE, None
        age=(now if now is not None else time.time())-timestamp
        return (CachePolicy.FRESH_CACHE if age <= ttl else CachePolicy.STALE_CACHE), metadata
    except (KeyError, TypeError, ValueError):
        return CachePolicy.CORRUPTED_CACHE, None
