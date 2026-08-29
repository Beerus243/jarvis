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
from .installation_engine import InstallationState, InstallationReport, execute_installation_plan
from .repair_engine import RepairDecision, diagnose_failure, run_with_replan
from .intent import EnvironmentPreparationIntent, detect_environment_intent
from .workflow import EnvironmentWorkflow, EnvironmentWorkflowReport
from .preparation_service import EnvironmentPreparationService
from .web_research import WebSearchClient, WebSearchResult, WebLLMResearchProvider, GroqResearchInterpreter
from .downloader import ArtifactDownloader, DownloadResult
from .extractor import SecureArchiveExtractor
from .path_config import ConfigureUserPath
from .verifier import verify
from .research import (OfficialSource, OfficialSourceRegistry, DEFAULT_SOURCES, EnvironmentMetadata,
                       EnvironmentResearchRequest, EnvironmentResearchResult, EnvironmentResearcher,
                       MetadataCache, validate_metadata, ResearchCandidate, ResearchProvider)
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
__all__ += ["InstallationState", "InstallationReport", "execute_installation_plan"]
__all__ += ["RepairDecision", "diagnose_failure", "run_with_replan"]
__all__ += ["EnvironmentPreparationIntent", "detect_environment_intent"]
__all__ += ["EnvironmentWorkflow", "EnvironmentWorkflowReport"]
__all__ += ["EnvironmentPreparationService"]
__all__ += ["WebSearchClient", "WebSearchResult", "WebLLMResearchProvider", "GroqResearchInterpreter"]
__all__ += ["ArtifactDownloader", "DownloadResult", "SecureArchiveExtractor"]
__all__ += ["ConfigureUserPath", "verify"]
__all__ += ["OfficialSource", "OfficialSourceRegistry", "DEFAULT_SOURCES", "EnvironmentMetadata", "EnvironmentResearchRequest", "EnvironmentResearchResult", "EnvironmentResearcher", "MetadataCache", "validate_metadata", "ResearchCandidate", "ResearchProvider"]
