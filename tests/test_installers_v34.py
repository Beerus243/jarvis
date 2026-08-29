from pathlib import Path
import hashlib, tempfile, pytest
from core.environment.installers import *
def test_artifact_validation_and_sources():
    src=TrustedSource('node','1','tar','https://nodejs.org/a.tar')
    assert validate_source(src)
    assert InstallationArtifact('x','1','linux','x86_64',src,'tar',Path.home()/'x').validate()
def test_checksum_and_traversal(tmp_path):
    p=tmp_path/'a'; p.write_bytes(b'x'); assert verify_checksum(p,hashlib.sha256(b'x').hexdigest())
    with pytest.raises(ValueError): safe_extract_member(tmp_path,'../../etc/passwd')
def test_node_and_java_plans():
    assert len(NodeInstaller().plan().steps)==2 and len(JdkInstaller().plan().steps)==2
