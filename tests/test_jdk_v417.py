from pathlib import Path
from core.environment.local_jdks import LocalJDKDiscovery
from core.environment.installers.jdk_installer import JdkInstaller
def make(root,javac=True):
    (root/'bin').mkdir(parents=True); (root/'bin/java').write_text('x')
    if javac: (root/'bin/javac').write_text('x')
def test_jdk_ready_and_partial(tmp_path):
    root=tmp_path/'jdk-21'; make(root); assert LocalJDKDiscovery([root]).discover()[0].state=='READY'
    partial=tmp_path/'jdk-22'; make(partial,False); assert LocalJDKDiscovery([partial]).discover()[0].state=='PARTIAL'
def test_jdk_plan_is_typed():
    assert [s.action_type for s in JdkInstaller().plan_installation().steps]==['DOWNLOAD','VERIFY','EXTRACT','INSTALL','CONFIGURE_JAVA_HOME','CONFIGURE_PATH','VERIFY_JAVA','VERIFY_JAVAC']
