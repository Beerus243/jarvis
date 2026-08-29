from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from .contracts import TrustedSource
def validate_source(source:TrustedSource, allowed_hosts=('storage.googleapis.com','nodejs.org','download.oracle.com')):
    p=urlparse(source.url or '')
    return source.approved() and p.hostname in allowed_hosts
def verify_checksum(path, expected, algorithm='sha256'):
    if not expected: return False
    h=hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest().lower()==expected.lower()
def safe_extract_member(destination, member):
    dest=Path(destination).resolve(); target=(dest/member).resolve()
    if Path(member).is_absolute() or dest not in target.parents and target != dest: raise ValueError('Archive path traversal rejected')
    return target
