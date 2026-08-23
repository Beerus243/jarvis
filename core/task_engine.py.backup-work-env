"""Tâches bornées et annulables de JARVIS."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

from core.action_planner import plan_actions
from core.action_executor import execute_plan

PLANNED, RUNNING, WAITING_CONFIRMATION, COMPLETED, FAILED, CANCELLED = (
    "PLANNED", "RUNNING", "WAITING_CONFIRMATION", "COMPLETED", "FAILED", "CANCELLED"
)


@dataclass
class Task:
    goal: str
    steps: list = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = PLANNED
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())
    current_step: int = 0


_active_task = None


def create_task(goal):
    global _active_task
    steps = plan_actions(goal)
    if not steps and "environnement de travail" in str(goal).casefold():
        from core.action_planner import PlannedAction
        steps = [PlannedAction("OPEN_BROWSER", "navigateur"), PlannedAction("OPEN_VSCODE", "éditeur")]
    task = Task(goal, steps)
    _active_task = task
    return task


def get_active_task():
    return _active_task


def cancel_task():
    global _active_task
    if _active_task is None:
        return False
    _active_task.status = CANCELLED
    _active_task = None
    return True


def execute_task(task=None, confirmation=False, dispatcher=None):
    global _active_task
    task = task or _active_task
    if task is None:
        return task
    task.status = RUNNING
    results = execute_plan(task.steps, confirmation=confirmation, dispatcher=dispatcher)
    task.current_step = len(results)
    task.status = COMPLETED if results and all(item.success for item in results) else FAILED
    _active_task = task if task.status == FAILED else None
    return task, results


def task_dict(task):
    return asdict(task) if task else None
