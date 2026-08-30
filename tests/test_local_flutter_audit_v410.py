import io, tarfile, hashlib
from core.environment.local_artifacts import LocalArtifactDiscovery

def make(path, names):
    with tarfile.open(path,'w') as t:
        for name in names:
            i=tarfile.TarInfo(name); i.size=1; t.addfile(i,io.BytesIO(b'x'))
def test_nested_flutter_root_is_valid(tmp_path):
    p=tmp_path/'flutter_linux_x64_3.30.0.tar.xz'; make(p,('flutter_linux_x64_3.30.0/flutter/bin/flutter','flutter_linux_x64_3.30.0/flutter/bin/dart')); assert LocalArtifactDiscovery([tmp_path]).discover()
def test_invalid_candidates_are_visible_to_audit(tmp_path):
    p=tmp_path/'flutter.tar.xz'; make(p,('other',)); c=LocalArtifactDiscovery([tmp_path]).discover(include_invalid=True); assert c and c[0].validation_status=='INVALID'
def test_sha256_is_local_measurement(tmp_path):
    p=tmp_path/'flutter.tar.xz'; make(p,('flutter/bin/flutter','flutter/bin/dart')); d=LocalArtifactDiscovery([tmp_path]); assert d.checksum(p)==hashlib.sha256(p.read_bytes()).hexdigest()
def test_missing_dart_is_rejected(tmp_path):
    p=tmp_path/'flutter.tar.xz'; make(p,('flutter/bin/flutter',)); assert not LocalArtifactDiscovery([tmp_path]).discover()
def test_no_archive_returns_empty(tmp_path):
    assert LocalArtifactDiscovery([tmp_path]).discover()==[]
