"""Plans conversationnels bâtis depuis les métadonnées officielles, sans installation."""
from pathlib import Path
import platform
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from .adoptium_provider import AdoptiumProvider, JDKRequest
from .installers.jdk_installer import JdkInstaller
from .installers.android_installer import AndroidInstaller
from .installers.flutter_installer import FlutterInstaller
from .installers.artifacts import InstallationArtifact
from .installers.contracts import TrustedSource


def fetch_metadata(url):
    import requests
    if urlparse(url).hostname not in {'api.adoptium.net', 'dl.google.com', 'storage.googleapis.com'}:
        raise ValueError('Source de métadonnées non autorisée.')
    response = requests.get(url, timeout=10, allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect or len(response.content) > 16 * 1024 * 1024:
        raise ValueError('Métadonnées redirigées ou trop volumineuses.')
    return response.text if url.endswith('.xml') else response.json()


def build_plan(intent, fetcher=None):
    fetcher = fetcher or fetch_metadata
    if intent.profile not in {'java', 'flutter_development'}:
        raise ValueError('Installation conversationnelle disponible pour Java, Flutter et les outils Android uniquement.')
    if intent.requested_version:
        raise ValueError('La sélection d’une version précise nécessite un plan dédié ; aucune autre version ne sera substituée.')
    architecture = platform.machine().lower()
    if architecture not in {'x86_64', 'aarch64'}:
        raise ValueError('Architecture non prise en charge.')
    if intent.intent == 'JDK_INSTALL' or intent.profile == 'java':
        research = AdoptiumProvider(fetcher=fetcher).research(JDKRequest(feature_version=17,
            architecture='x64' if architecture == 'x86_64' else 'aarch64'))
        if research.status != 'READY' or not research.artifacts:
            raise ValueError('Métadonnées officielles JDK indisponibles : ' + ', '.join(research.warnings))
        item = research.artifacts[0]
        source = TrustedSource('Eclipse Adoptium', item.version, item.artifact, item.download_url, item.checksum, architecture)
        artifact = InstallationArtifact(Path(urlparse(item.download_url).path).name, item.version, 'linux', architecture,
            source, 'tar.gz', Path.home()/'.local/share/jarvis/environments/jdk'/item.version, item.checksum)
        return JdkInstaller().plan_installation(), artifact
    if intent.environment.lower() == 'android' or intent.intent == 'ANDROID_TOOLS_INSTALL':
        if architecture != 'x86_64':
            raise ValueError('Les outils Android Linux disponibles nécessitent x86_64.')
        xml = fetcher('https://dl.google.com/android/repository/repository2-3.xml')
        root = ET.fromstring(xml)
        for package in root.iter():
            if package.tag.split('}')[-1] != 'remotePackage' or package.get('path') != 'cmdline-tools;latest':
                continue
            # Certains dépôts utilisent un namespace uniquement sur la racine.
            for node in package.iter():
                node.tag = node.tag.split('}')[-1]
            for archive in package.findall('.//archive'):
                if archive.findtext('host-os') != 'linux':
                    continue
                complete = archive.find('complete')
                checksum = complete.find('checksum')
                filename = complete.findtext('url') or ''
                digest = (checksum.text or '').strip()
                algorithm = checksum.get('type', 'sha1').lower()
                if not re.fullmatch(r'commandlinetools-linux-[0-9]+_latest\.zip', filename):
                    continue
                version = package.findtext('revision/major') or filename.split('-')[2].split('_')[0]
                source = TrustedSource('Android', version, filename, 'https://dl.google.com/android/repository/'+filename, digest, architecture)
                artifact = InstallationArtifact(filename, version, 'linux', architecture, source, 'zip',
                    Path.home()/'.local/share/jarvis/environments/android'/version, digest, checksum_algorithm=algorithm)
                return AndroidInstaller().plan_component('cmdline-tools'), artifact
        raise ValueError('Aucun artefact officiel des outils Android pour Linux.')
    payload = fetcher('https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json')
    release = next((r for r in payload.get('releases', []) if r.get('hash') == payload.get('current_release', {}).get('stable')
                    and r.get('dart_sdk_arch', 'x64') == ('x64' if architecture == 'x86_64' else 'arm64')), None)
    if not release:
        raise ValueError('Version stable de Flutter introuvable pour cette architecture.')
    archive = release.get('archive', '')
    if not archive.startswith('stable/linux/') or '..' in archive:
        raise ValueError('Chemin d’artefact Flutter invalide.')
    source = TrustedSource('Flutter', release['version'], Path(archive).name,
        'https://storage.googleapis.com/flutter_infra_release/releases/'+archive, release.get('sha256'), architecture)
    artifact = InstallationArtifact(Path(archive).name, release['version'], 'linux', architecture, source, 'tar.xz',
        Path.home()/'.local/share/jarvis/environments/flutter'/release['version'], release.get('sha256'))
    return FlutterInstaller().plan(), artifact


def validate_plan_artifact(artifact):
    if not artifact.validate() or artifact.destination.expanduser().resolve() == Path.home().resolve():
        return False
    from .installers.security import validate_source
    digest = artifact.checksum or ''
    algorithm = artifact.checksum_algorithm
    size = {'sha1': 40, 'sha256': 64, 'sha512': 128}.get(algorithm)
    return bool(size and re.fullmatch(r'[a-fA-F0-9]{' + str(size) + '}', digest)
                and artifact.source.checksum == digest and validate_source(artifact.source))


def format_plan(pending):
    artifact = pending.artifact
    if not artifact or not pending.plan:
        return f'Plan {pending.plan_id} bloqué : aucun artefact officiel validé.'
    steps = ', '.join(step.action_type for step in pending.plan.steps)
    return (f'Plan {pending.plan_id} : {artifact.name}, version {artifact.version}.\n'
            f'Source : {artifact.source.url}\nDestination : {artifact.destination}\n'
            f'Empreinte {artifact.checksum_algorithm} : {artifact.checksum}\nÉtapes : {steps}.\n'
            'Aucune installation effectuée. Dites « confirme » ou « annule ».')
