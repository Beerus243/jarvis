from core.environment.android_sdk import AndroidSDKDiscovery
from pathlib import Path
def test_android_sdk_components_are_discovered(tmp_path,monkeypatch):
    root=tmp_path/'sdk'; (root/'platform-tools').mkdir(parents=True); adb=root/'platform-tools/adb'; adb.write_text('x'); adb.chmod(0o755); (root/'build-tools/34').mkdir(parents=True); (root/'platforms/android-34').mkdir(parents=True); (root/'cmdline-tools/latest').mkdir(parents=True)
    item=AndroidSDKDiscovery([root]).discover(); assert item.sdk=='PRESENT' and item.build_tools=='PRESENT' and item.platforms=='PRESENT' and item.cmdline_tools=='PRESENT'
def test_android_sdk_missing(tmp_path):
    assert AndroidSDKDiscovery([tmp_path/'none']).discover().sdk=='SDK_MISSING'
def test_android_sdk_does_not_modify_files(tmp_path):
    root=tmp_path/'sdk'; root.mkdir(); before=list(root.iterdir()); AndroidSDKDiscovery([root]).discover(); assert list(root.iterdir())==before
