import io, tarfile
from pathlib import Path
from core.environment.installation_engine import InstallationEngine
from core.environment.installers.flutter_installer import FlutterInstaller
from core.environment.execution import ExecutionStatus, ExecutionResult
from core.environment.path_config import ConfigureUserPath

class FakeDownload:
    def __init__(self,path): self.path=path; self.calls=0
    def download(self,artifact): self.calls+=1; return type('R',(),{'success':True,'path':self.path})()
class FakeExtract:
    def __init__(self): self.calls=0
    def extract(self,archive,destination,kind):
        self.calls+=1; root=Path(destination)/'flutter'; (root/'bin').mkdir(parents=True,exist_ok=True)
        (root/'bin/flutter').write_text('x'); (root/'bin/dart').write_text('x'); return True
class FakePath:
    def __init__(self): self.calls=0
    def apply(self,path): self.calls+=1; return True
def artifact(tmp):
    from core.environment.installers.artifacts import InstallationArtifact
    from core.environment.installers.contracts import TrustedSource
    return InstallationArtifact('flutter.tar.xz','1','linux','x86_64',TrustedSource('Flutter','1','archive','https://storage.googleapis.com/a'),'tar',tmp/'install')
def test_flutter_runtime_end_to_end(tmp_path):
    plan=FlutterInstaller().plan(); dl=FakeDownload(tmp_path/'a'); ex=FakeExtract(); pc=FakePath()
    def verifier(name, executable=None): return ExecutionResult(name,ExecutionStatus.SUCCESS)
    report=InstallationEngine(dl,ex,pc,verifier).execute(plan,artifact=artifact(tmp_path),dry_run=False,confirmation_handler=lambda step: True)
    assert report.to_dict()['success'] and dl.calls==1 and ex.calls==1 and pc.calls==1
def test_runtime_stops_after_download_failure(tmp_path):
    class Bad:
        def download(self,a): return type('R',(),{'success':False,'error':'network','path':None})()
    ex=FakeExtract(); report=InstallationEngine(Bad(),ex,FakePath()).execute(FlutterInstaller().plan(),artifact=artifact(tmp_path),dry_run=False,confirmation_handler=lambda s: True)
    assert report.results[-1].status==ExecutionStatus.FAILED and ex.calls==0
def test_runtime_dry_run_has_no_side_effects(tmp_path):
    dl=FakeDownload(tmp_path/'a'); ex=FakeExtract(); pc=FakePath(); report=InstallationEngine(dl,ex,pc).execute(FlutterInstaller().plan(),artifact=artifact(tmp_path),dry_run=True)
    assert all(item.status==ExecutionStatus.SKIPPED for item in report.results) and dl.calls==0 and ex.calls==0 and pc.calls==0
