"""Read-only local environment inspection and requirement analysis."""

from .inspector import format_environment_report, inspect_environment
from .action_planner import format_execution_plan, plan_actions, plan_environment_setup
from .actions import ActionType, ExecutionPlan, PlannedAction, RiskLevel
from .execution import ExecutionResult, ExecutionStatus
from .action_executor import execute_action, execute_plan
from .action_executor import execute_plan_with_replan
from .resolvers import JavaEnvironmentResolver, AndroidEnvironmentResolver, FlutterEnvironmentResolver
from .execution_report import EnvironmentExecutionReport
from .repair_executor import execute_repair
from .profiles import EnvironmentProfile, EnvironmentProfileRegistry, DEFAULT_PROFILES
from .gap_analysis import GapAnalysis, analyze_gaps
from .preparation import EnvironmentPreparationEngine, EnvironmentPreparationPlan
from .requirement_resolver import format_requirement_plan, resolve_requirements
from .requirements import Requirement, RequirementPlan, RequirementSet, RequirementStatus

__all__ = ["inspect_environment", "format_environment_report", "resolve_requirements",
           "format_requirement_plan", "Requirement", "RequirementPlan", "RequirementSet",
           "RequirementStatus", "ActionType", "RiskLevel", "PlannedAction", "ExecutionPlan",
           "plan_actions", "plan_environment_setup", "format_execution_plan"]
__all__ += ["ExecutionResult", "ExecutionStatus", "execute_action", "execute_plan"]
__all__ += ["execute_plan_with_replan", "JavaEnvironmentResolver", "AndroidEnvironmentResolver", "FlutterEnvironmentResolver", "EnvironmentExecutionReport"]
__all__ += ["execute_repair"]
__all__ += ["EnvironmentProfile", "EnvironmentProfileRegistry", "DEFAULT_PROFILES", "GapAnalysis", "analyze_gaps", "EnvironmentPreparationEngine", "EnvironmentPreparationPlan"]
