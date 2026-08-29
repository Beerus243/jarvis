from __future__ import annotations
from dataclasses import dataclass
from .inspector import inspect_environment
from .requirement_resolver import resolve_requirements
from .action_planner import plan_actions
from .gap_analysis import analyze_gaps
from .installers import DEFAULT_INSTALLERS

@dataclass
class EnvironmentPreparationPlan:
    profile: str|None; requirements: object; gaps: object; execution_plan: object; current_state: dict; installation_plan: object|None=None
    def to_dict(self):
        installation = None
        if self.installation_plan is not None:
            installation = {'requirement': self.installation_plan.requirement, 'blocked': self.installation_plan.blocked,
                            'reason': self.installation_plan.reason,
                            'steps': [step.__dict__ for step in self.installation_plan.steps]}
        return {'profile':self.profile,'requirements':self.requirements.to_dict(),'gaps':self.gaps.to_dict(),'execution_plan':self.execution_plan.to_dict(),'current_state':self.current_state,'installation_plan':installation}

class EnvironmentPreparationEngine:
    def prepare(self, request, environment=None):
        current=environment if environment is not None else inspect_environment()
        requirements=resolve_requirements(request,current)
        execution=plan_actions(requirements)
        installer=DEFAULT_INSTALLERS.get({'flutter_development':'flutter','node':'node','java':'java'}.get(requirements.profile,''))
        installation=installer.plan() if installer and any(item['status'] != 'READY' and item['required'] for item in analyze_gaps(requirements).items) else None
        return EnvironmentPreparationPlan(requirements.profile,requirements,analyze_gaps(requirements),execution,current,installation)
