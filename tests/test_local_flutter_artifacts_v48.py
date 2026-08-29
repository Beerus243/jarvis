import io, tarfile
from pathlib import Path
from core.environment.local_artifacts import LocalArtifactDiscovery
from core.environment.preparation_service import EnvironmentPreparationService
from core.environment.installers.flutter_installer import FlutterInstaller
from core.environment.installation_engine import InstallationEngine
from core.environment.execution import ExecutionResult, ExecutionStatus

def make_archive(path, entries=('flutter/bin/flutter','flutter/bin/dart')):
    with tarfile.open(path,'w') as tar:
        for name in entries:
            info=tarfile.TarInfo(name); info.size=1; tar.addfile(info,io.BytesIO(b'x'))
def test_valid_flutter_archive_is_discovered(tmp_path):
    p=tmp_path/'flutter_linux_3.24.0.tar.xz'; make_archive(p)
    c=LocalArtifactDiscovery([tmp_path]).discover(architecture='x86_64')[0]
    assert c.validation_status=='VALID' and c.version=='3.24.0'
def test_missing_flutter_entries_rejected(tmp_path):
    p=tmp_path/'flutter.zip'; make_archive(p,('other/file',)); assert not LocalArtifactDiscovery([tmp_path]).discover()
def test_traversal_rejected(tmp_path):
    p=tmp_path/'flutter.tar.xz'; make_archive(p,('../escape','flutter/bin/dart')); assert not LocalArtifactDiscovery([tmp_path]).discover()
def test_local_checksum_and_artifact(tmp_path):
    p=tmp_path/'flutter_linux_3.24.0.tar.xz'; make_archive(p); c=LocalArtifactDiscovery([tmp_path]).discover()[0]; a=LocalArtifactDiscovery([tmp_path]).to_installation_artifact(c,tmp_path/'install'); assert a and a.source.provider=='local' and a.checksum
def test_local_has_priority_over_web(tmp_path):
    p=tmp_path/'flutter_linux_3.24.0.tar.xz'; make_archive(p)
    class Web:
        def research(self,*a): raise AssertionError('web should not be called')
    report=EnvironmentPreparationService(Web(),local_discovery=LocalArtifactDiscovery([tmp_path])).prepare('Flutter'); assert report['source']=='LOCAL_ARTIFACT'
def test_unknown_extension_rejected(tmp_path):
    (tmp_path/'flutter.bin').write_bytes(b'x'); assert not LocalArtifactDiscovery([tmp_path]).discover()
def test_local_artifact_can_enter_runtime_without_downloader(tmp_path):
    p=tmp_path/'flutter_linux_3.24.0.tar.xz'; make_archive(p); d=LocalArtifactDiscovery([tmp_path]); c=d.discover()[0]; a=d.to_installation_artifact(c,tmp_path/'install')
    class Extract:
        def extract(self,archive,destination,kind): (Path(destination)/'bin').mkdir(parents=True); (Path(destination)/'bin/flutter').write_text('x'); (Path(destination)/'bin/dart').write_text('x'); return True
    class PathConfig:
        def apply(self,p): return True
    report=InstallationEngine(extractor=Extract(),path_config=PathConfig(),verifier=lambda n,executable=None: ExecutionResult(n,ExecutionStatus.SUCCESS),allowed_root=tmp_path).execute(FlutterInstaller().plan(),artifact=a,dry_run=False,confirmation_handler=lambda s: True)
    assert report.to_dict()['success']
