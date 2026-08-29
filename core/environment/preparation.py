from __future__ import annotations
from dataclasses import dataclass
from .inspector import inspect_environment
from .requirement_resolver import resolve_requirements
from .action_planner import plan_actions
from .gap_analysis import analyze_gaps

@dataclass
class EnvironmentPreparationPlan:
    profile: str|None; requirements: object; gaps: object; execution_plan: object; current_state: dict
    def to_dict(self): return {'profile':self.profile,'requirements':self.requirements.to_dict(),'gaps':self.gaps.to_dict(),'execution_plan':self.execution_plan.to_dict(),'current_state':self.current_state}

class EnvironmentPreparationEngine:
    def prepare(self, request, environment=None):
        current=environment if environment is not None else inspect_environment()
        requirements=resolve_requirements(request,current)
        return EnvironmentPreparationPlan(requirements.profile,requirements,analyze_gaps(requirements),plan_actions(requirements),current)
