import hashlib, io, tarfile
from pathlib import Path
from core.environment.downloader import ArtifactDownloader
from core.environment.extractor import SecureArchiveExtractor
from core.environment.installers.artifacts import InstallationArtifact
from core.environment.installers.contracts import TrustedSource
from core.environment.installers.flutter_installer import FlutterInstaller
from core.environment.path_config import ConfigureUserPath
from core.environment.verifier import verify

def artifact(url='https://nodejs.org/dist/a.tar.xz', checksum=None):
    return InstallationArtifact('a.tar.xz','1','linux','x86_64',TrustedSource('Node.js','1','archive',url,checksum,'x86_64'),'tar',Path.home()/'x')
class Response:
    status_code=200; headers={}
    def __init__(self,data): self.data=data
    def iter_content(self,n): yield self.data
class Session:
    def __init__(self,data): self.data=data
    def get(self,*args,**kwargs): return Response(self.data)
def test_download_stream_and_checksum(tmp_path):
    data=b'abc'; result=ArtifactDownloader(tmp_path,session=Session(data)).download(artifact(checksum=hashlib.sha256(data).hexdigest()))
    assert result.success and result.path.read_bytes()==data
def test_download_rejects_bad_checksum(tmp_path):
    assert not ArtifactDownloader(tmp_path,session=Session(b'abc')).download(artifact(checksum='0'*64)).success
def test_download_rejects_untrusted_url(tmp_path):
    assert not ArtifactDownloader(tmp_path,session=Session(b'x')).download(artifact('https://evil.test/a')).success
def test_download_rejects_oversize(tmp_path):
    assert not ArtifactDownloader(tmp_path,max_size=2,session=Session(b'abc')).download(artifact()).success
def test_extractor_allows_normal_tar(tmp_path):
    archive=tmp_path/'a.tar'
    with tarfile.open(archive,'w') as tar:
        info=tarfile.TarInfo('flutter/bin/flutter'); info.size=3; tar.addfile(info,io.BytesIO(b'ok!'))
    out=tmp_path/'out'; assert SecureArchiveExtractor().extract(archive,out); assert (out/'flutter/bin/flutter').read_bytes()==b'ok!'
def test_extractor_rejects_traversal(tmp_path):
    archive=tmp_path/'a.tar'
    with tarfile.open(archive,'w') as tar:
        info=tarfile.TarInfo('../escape'); info.size=1; tar.addfile(info,io.BytesIO(b'x'))
    assert not SecureArchiveExtractor().extract(archive,tmp_path/'out')
def test_extractor_rejects_symlink_escape(tmp_path):
    archive=tmp_path/'a.tar'
    with tarfile.open(archive,'w') as tar:
        info=tarfile.TarInfo('link'); info.type=tarfile.SYMTYPE; info.linkname='/etc'; tar.addfile(info)
    assert not SecureArchiveExtractor().extract(archive,tmp_path/'out')

def test_flutter_plan_contains_typed_steps():
    assert [step.action_type for step in FlutterInstaller().plan().steps] == ['DOWNLOAD','VERIFY','EXTRACT','INSTALL','CONFIGURE_PATH','VERIFY_FLUTTER','VERIFY_DART']
def test_flutter_artifact_requires_valid_research():
    assert FlutterInstaller().artifact_from_research(None) is None
def test_path_configuration_is_idempotent(tmp_path):
    path=tmp_path/'.profile'; c=ConfigureUserPath(path, allowed_root=tmp_path); bin_path=tmp_path/'bin'; assert c.apply(bin_path); assert c.apply(bin_path); assert path.read_text().count(str(bin_path))==1
def test_path_configuration_rejects_system_path(tmp_path):
    assert not ConfigureUserPath(tmp_path/'.profile').apply('/usr/bin')
def test_verifier_allowlist_blocks_unknown():
    assert verify('rm').status.value=='BLOCKED'
