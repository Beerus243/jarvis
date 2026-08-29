from __future__ import annotations
from dataclasses import dataclass
from .requirements import RequirementStatus

@dataclass
class GapAnalysis:
    profile: str|None
    items: list[dict]
    readiness: str
    def to_dict(self): return {'profile':self.profile,'items':self.items,'readiness':self.readiness}

def analyze_gaps(requirement_plan):
    items=[]
    for req in requirement_plan.requirements:
        status=getattr(req.status,'value',req.status)
        category={'SATISFIED':'READY','MISSING':'MISSING','MISCONFIGURED':'MISCONFIGURED','PARTIAL':'PARTIAL','UNKNOWN':'UNKNOWN'}.get(status,'UNSUPPORTED')
        items.append({'requirement':req.name,'status':category,'required':req.required})
    required=[x for x in items if x['required']]
    readiness='READY' if required and all(x['status']=='READY' for x in required) else 'NOT_READY' if any(x['status']=='MISSING' for x in required) else 'PARTIALLY_READY'
    return GapAnalysis(requirement_plan.profile,items,readiness)
