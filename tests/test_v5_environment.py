from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock
import hashlib
import zipfile

import pytest

from core.environment.conversation_plan import build_plan, validate_plan_artifact
from core.environment.intent import detect_environment_intent
from core.environment.installation_engine import InstallationEngine
from core.environment.installers.artifacts import InstallationArtifact
from core.environment.installers.contracts import TrustedSource
from core.environment.installers.android_installer import AndroidInstaller


def test_flutter_plan_uses_official_release_path_and_checksum(monkeypatch):
    monkeypatch.setattr('platform.machine', lambda: 'x86_64')
    metadata = {'current_release': {'stable': 'a'}, 'releases': [
        {'hash': 'a', 'version': '1.2.3', 'archive': 'stable/linux/flutter_linux_1.2.3-stable.tar.xz', 'sha256': 'a'*64}]}
    _, artifact = build_plan(detect_environment_intent('installe flutter'), fetcher=lambda _: metadata)
    assert artifact.source.url == 'https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_1.2.3-stable.tar.xz'
    assert validate_plan_artifact(artifact)
    assert not validate_plan_artifact(replace(artifact, checksum='wrong'))


def test_unsupported_profile_never_installs_flutter():
    fetch = Mock()
    with pytest.raises(ValueError, match='uniquement'):
        build_plan(detect_environment_intent('nodejs'), fetcher=fetch)
    fetch.assert_not_called()


def android_archive(tmp_path):
    archive = tmp_path/'tools.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        entry = zipfile.ZipInfo('cmdline-tools/bin/sdkmanager')
        entry.external_attr = 0o100755 << 16
        output.writestr(entry, '#!/bin/sh\nexit 0\n')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    source = TrustedSource('local', '1', archive.name, None, checksum, 'x86_64', str(archive))
    return InstallationArtifact(archive.name, '1', 'linux', 'x86_64', source, 'zip', tmp_path/'sdk', checksum)


def test_android_local_archive_verified_and_executable(tmp_path):
    artifact = android_archive(tmp_path)
    result = InstallationEngine(allowed_root=tmp_path).execute(AndroidInstaller().plan_component(),
        artifact=artifact, dry_run=False, confirmation_handler=lambda _: True)
    assert result.to_dict()['success']
    sdkmanager = artifact.destination/'cmdline-tools/latest/bin/sdkmanager'
    assert sdkmanager.is_file() and sdkmanager.stat().st_mode & 0o111


def test_changed_archive_stops_before_extraction(tmp_path):
    artifact = android_archive(tmp_path)
    Path(artifact.source.local_path).write_bytes(b'changed after confirmation')
    extractor = Mock()
    result = InstallationEngine(extractor=extractor, allowed_root=tmp_path).execute(AndroidInstaller().plan_component(),
        artifact=artifact, dry_run=False, confirmation_handler=lambda _: True)
    assert not result.to_dict()['success']
    assert 'empreinte' in result.results[-1].error
    extractor.extract.assert_not_called()


def test_environment_confirmation_consumed_once(monkeypatch, tmp_path):
    from core.environment.pending_plan import set_pending, get_pending
    from core.environment.command_handler import handle_environment_intent
    from contextlib import nullcontext
    intent = detect_environment_intent('installe flutter')
    artifact = replace(android_archive(tmp_path), destination=Path.home()/'.local/share/jarvis/environments/test')
    # Le faux moteur isole les effets ; le plan conserve les métadonnées approuvées.
    monkeypatch.setattr('core.environment.conversation_plan.validate_plan_artifact', lambda _: True)
    engine = Mock()
    engine.execute.return_value.to_dict.return_value = {'success': True}
    monkeypatch.setattr('core.environment.command_handler.InstallationEngine', lambda: engine)
    monkeypatch.setattr('core.environment.command_handler.InstallationLock', nullcontext)
    set_pending(intent, plan=AndroidInstaller().plan_component(), artifact=artifact)
    assert 'installé' in handle_environment_intent(detect_environment_intent('confirme'))
    assert get_pending() is None
    assert 'Aucun plan' in handle_environment_intent(detect_environment_intent('confirme'))
    engine.execute.assert_called_once()


def test_environment_not_ready_without_flutter_or_android():
    from core.environment.capabilities import EnvironmentCapabilities
    from core.environment.decision import decide
    result = decide(EnvironmentCapabilities(javac=True, java_home=True, sdkmanager=True))
    assert result.status == 'PARTIAL'
    assert 'Flutter' in result.missing and 'Android SDK' in result.missing


def test_explicit_product_is_not_replaced_by_another_missing_component(monkeypatch):
    from core.environment.command_handler import handle_environment_intent
    planner = Mock(side_effect=ValueError('offline'))
    monkeypatch.setattr('core.environment.conversation_plan.build_plan', planner)
    handle_environment_intent(detect_environment_intent('installe flutter'))
    assert planner.call_args.args[0].environment == 'Flutter'
    assert detect_environment_intent('prépare mon environnement Node.js').profile == 'node'
