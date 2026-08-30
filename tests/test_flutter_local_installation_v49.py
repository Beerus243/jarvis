import io, tarfile
from pathlib import Path
from core.environment.local_artifacts import LocalArtifactDiscovery
from core.environment.installers.flutter_installer import FlutterInstaller
from core.environment.installation_engine import InstallationEngine
from core.environment.execution import ExecutionResult, ExecutionStatus

def archive(path, entries=('flutter/bin/flutter','flutter/bin/dart')):
    with tarfile.open(path,'w') as t:
        for name in entries:
            i=tarfile.TarInfo(name); i.size=1; t.addfile(i,io.BytesIO(b'x'))
def test_local_archive_to_plan_and_engine(tmp_path):
    p=tmp_path/'flutter_linux_3.25.0.tar.xz'; archive(p); d=LocalArtifactDiscovery([tmp_path]); c=d.discover()[0]; a=d.to_installation_artifact(c,tmp_path/'install')
    class E:
        def extract(self,src,dst,kind): (Path(dst)/'bin').mkdir(parents=True); (Path(dst)/'bin/flutter').write_text('x'); (Path(dst)/'bin/dart').write_text('x'); return True
    class P:
        def apply(self,path): return True
    report=InstallationEngine(extractor=E(),path_config=P(),verifier=lambda n,executable=None: ExecutionResult(n,ExecutionStatus.SUCCESS),allowed_root=tmp_path).execute(FlutterInstaller().plan(),artifact=a,dry_run=False,confirmation_handler=lambda s:True)
    assert report.to_dict()['success']
def test_local_discovery_does_not_call_web_or_downloader(tmp_path):
    p=tmp_path/'flutter_linux_3.25.0.tar.xz'; archive(p); d=LocalArtifactDiscovery([tmp_path]); assert d.discover()
def test_ready_and_partial_states(tmp_path):
    i=FlutterInstaller(tmp_path/'flutter'); assert i.installation_status('1.0')=='ABSENT'; (tmp_path/'flutter'/'1.0').mkdir(parents=True); assert i.installation_status('1.0')=='PARTIAL'
def test_invalid_archive_never_becomes_artifact(tmp_path):
    p=tmp_path/'flutter.tar.xz'; archive(p,('other',)); assert not LocalArtifactDiscovery([tmp_path]).discover()
