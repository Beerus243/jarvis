from __future__ import annotations
from dataclasses import dataclass, field
from .execution import ExecutionResult, ExecutionStatus

@dataclass
class EnvironmentExecutionReport:
    results: list[ExecutionResult]=field(default_factory=list)
    def to_dict(self): return {'results':[r.to_dict() for r in self.results], 'success': all(r.status==ExecutionStatus.SUCCESS for r in self.results)}
    def format(self):
        lines=['ENVIRONNEMENT FLUTTER','=====================']
        for r in self.results: lines.append(f"{r.action_id}: {getattr(r.status,'value',r.status)}")
        lines.append('Résultat : ENVIRONNEMENT FLUTTER PRÊT' if self.results and all(r.status==ExecutionStatus.SUCCESS for r in self.results) else 'Résultat : environnement incomplet')
        return '\n'.join(lines)
