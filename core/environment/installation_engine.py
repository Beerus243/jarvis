from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from .execution import ExecutionResult, ExecutionStatus
from pathlib import Path
from .downloader import ArtifactDownloader
from .extractor import SecureArchiveExtractor
from .path_config import ConfigureUserPath
from .verifier import verify
import os
from contextlib import contextmanager

class InstallationEngine:
    """Dispatcher for typed installation steps; never accepts shell commands."""
    def __init__(self, downloader=None, extractor=None, path_config=None, verifier=verify, allowed_root=None):
        self.downloader=downloader or ArtifactDownloader(); self.extractor=extractor or SecureArchiveExtractor(); self.path_config=path_config or ConfigureUserPath(); self.verifier=verifier; self.allowed_root=Path(allowed_root or Path.home()).resolve()
    def execute(self, plan, *, artifact=None, dry_run=True, confirmation_handler=None):
        if not dry_run and artifact is not None:
            destination=Path(artifact.destination).expanduser().resolve()
            if not destination.is_relative_to(self.allowed_root):
                return InstallationReport([ExecutionResult('preflight',ExecutionStatus.FAILED,error='Destination hors HOME.')])
        done=set(); results=[]; state={}
        for step in plan.steps:
            if any(dep not in done for dep in step.dependencies):
                results.append(ExecutionResult(step.id,ExecutionStatus.SKIPPED,error='Dépendance non satisfaite.')); break
            if dry_run:
                results.append(ExecutionResult(step.id,ExecutionStatus.SKIPPED,metadata={'dry_run':True})); done.add(step.id); continue
            if step.requires_confirmation and not (confirmation_handler and confirmation_handler(step)):
                results.append(ExecutionResult(step.id,ExecutionStatus.CANCELLED,error='Confirmation refusée ou absente.')); break
            try:
                if artifact is None and step.action_type in {'DOWNLOAD','VERIFY','EXTRACT','INSTALL','CONFIGURE_PATH'}: raise ValueError('InstallationArtifact requis.')
                if step.action_type == 'DOWNLOAD':
                    value=None
                    for _ in range(2):
                        value=self.downloader.download(artifact)
                        if value.success: break
                    state['download']=value
                    if not value.success: raise RuntimeError(value.error or 'Téléchargement échoué.')
                elif step.action_type == 'VERIFY':
                    if not state.get('download') or not state['download'].success: raise RuntimeError('Téléchargement absent.')
                elif step.action_type == 'EXTRACT':
                    value=self.extractor.extract(state['download'].path, artifact.destination, artifact.archive_type)
                    if not value: raise RuntimeError('Extraction échouée.')
                    state['root']=self._flutter_root(artifact.destination)
                elif step.action_type == 'INSTALL':
                    if not state.get('root'): raise RuntimeError('Racine Flutter introuvable.')
                elif step.action_type == 'CONFIGURE_PATH':
                    if not self.path_config.apply(Path(state['root'])/'bin'): raise RuntimeError('Configuration PATH refusée.')
                elif step.action_type == 'VERIFY_FLUTTER':
                    result=self.verifier('verify_flutter', executable=str(Path(state['root'])/'bin/flutter'))
                    if result.status != ExecutionStatus.SUCCESS: raise RuntimeError(result.error or result.stderr or 'Flutter invalide.')
                elif step.action_type == 'VERIFY_DART':
                    result=self.verifier('verify_dart', executable=str(Path(state['root'])/'bin/dart'))
                    if result.status != ExecutionStatus.SUCCESS: raise RuntimeError(result.error or result.stderr or 'Dart invalide.')
                else: raise ValueError(f'Opération inconnue: {step.action_type}')
                results.append(ExecutionResult(step.id,ExecutionStatus.SUCCESS,metadata={'operation':step.action_type})); done.add(step.id)
            except Exception as exc:
                results.append(ExecutionResult(step.id,ExecutionStatus.FAILED,error=str(exc))); break
        return InstallationReport(results)
    @staticmethod
    def _flutter_root(destination):
        destination=Path(destination).resolve()
        direct=destination/'bin/flutter'
        nested=destination/'flutter/bin/flutter'
        if direct.exists(): return destination
        if nested.exists(): return destination/'flutter'
        candidates=[p for p in destination.iterdir()] if destination.exists() else []
        for candidate in candidates:
            if (candidate/'bin/flutter').exists(): return candidate
        raise FileNotFoundError('Répertoire Flutter extrait introuvable.')

class InstallationState(str, Enum):
    NOT_STARTED='NOT_STARTED'; PLANNED='PLANNED'; WAITING_CONFIRMATION='WAITING_CONFIRMATION'; RUNNING='RUNNING'; VERIFYING='VERIFYING'; SUCCEEDED='SUCCEEDED'; FAILED='FAILED'; BLOCKED='BLOCKED'; SKIPPED='SKIPPED'; CANCELLED='CANCELLED'

@dataclass
class InstallationReport:
    results:list[ExecutionResult]=field(default_factory=list)
    product:str|None=None; version:str|None=None; destination:str|None=None
    def to_dict(self): return {'product':self.product,'version':self.version,'destination':self.destination,'results':[r.to_dict() for r in self.results], 'success':bool(self.results) and all(r.status==ExecutionStatus.SUCCESS for r in self.results)}

def execute_installation_plan(plan, *, confirmation_handler=None, dry_run=True, operations=None):
    """Execute only typed installation steps. Real side effects require injected operations."""
    operations=operations or {}
    results=[]; done=set()
    for step in plan.steps:
        if any(dep not in done for dep in step.dependencies):
            results.append(ExecutionResult(step.id,ExecutionStatus.SKIPPED,error='Dépendance non satisfaite.')); break
        if dry_run:
            results.append(ExecutionResult(step.id,ExecutionStatus.SKIPPED,metadata={'dry_run':True})); done.add(step.id); continue
        if step.requires_confirmation and not (confirmation_handler and confirmation_handler(step)):
            results.append(ExecutionResult(step.id,ExecutionStatus.CANCELLED,error='Confirmation refusée ou absente.')); break
        operation=operations.get(step.action_type)
        if operation is None:
            results.append(ExecutionResult(step.id,ExecutionStatus.BLOCKED,error=f'Opération {step.action_type} non configurée.')); break
        started=monotonic()
        try: value=operation(step)
        except Exception as exc: results.append(ExecutionResult(step.id,ExecutionStatus.FAILED,duration=monotonic()-started,error=str(exc))); break
        result=value if isinstance(value,ExecutionResult) else ExecutionResult(step.id,ExecutionStatus.SUCCESS,duration=monotonic()-started)
        results.append(result)
        if result.status != ExecutionStatus.SUCCESS: break
        done.add(step.id)
    return InstallationReport(results)
