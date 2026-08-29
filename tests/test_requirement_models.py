from core.environment.requirements import Requirement, RequirementPlan, RequirementSet, RequirementStatus


def test_requirement_models_are_serializable():
    req = Requirement("git", "Git", RequirementStatus.SATISFIED)
    assert req.to_dict()["status"] == "SATISFIED"
    assert RequirementSet("demo", [req]).to_dict()["requirements"][0]["name"] == "git"
    assert RequirementPlan("x", "demo", [req]).to_dict()["profile"] == "demo"


def test_optional_requirement_is_marked():
    assert Requirement("studio", required=False).to_dict()["optional"] is True
