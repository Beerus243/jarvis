from __future__ import annotations
from dataclasses import dataclass, field
from .inspector import inspect_environment
from .preparation import EnvironmentPreparationEngine
from .installation_engine import execute_installation_plan
from .execution import ExecutionResult, ExecutionStatus

@dataclass
class EnvironmentWorkflowReport:
    profile: str|None
    initial_state: dict
    preparation: object
    results: list[ExecutionResult]=field(default_factory=list)
    final_state: dict|None=None
    status: str='PLANNED'
    def to_dict(self): return {'profile':self.profile,'initial_state':self.initial_state,'preparation':self.preparation.to_dict(),'results':[r.to_dict() for r in self.results],'final_state':self.final_state,'status':self.status}

class EnvironmentWorkflow:
    def __init__(self, inspector=inspect_environment, preparation_engine=None):
        self.inspector=inspector; self.preparation_engine=preparation_engine or EnvironmentPreparationEngine()
    def prepare(self, request, *, dry_run=True, confirmation_handler=None, operations=None):
        initial=self.inspector(); preparation=self.preparation_engine.prepare(request, initial)
        if dry_run: return EnvironmentWorkflowReport(preparation.profile,initial,preparation, status='PLANNED')
        results=execute_installation_plan(getattr(preparation, 'installation_plan', None) or _empty_installation_plan(preparation), confirmation_handler=confirmation_handler, dry_run=False, operations=operations)
        final=self.inspector(); status='READY' if results.to_dict()['success'] else 'PARTIAL'
        return EnvironmentWorkflowReport(preparation.profile,initial,preparation,results.results,final,status)

class _empty_installation_plan:
    steps=[]
