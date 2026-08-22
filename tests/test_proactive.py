from datetime import datetime, timedelta, timezone

from memory.proactive import clear_proposals, detect_proposals


def test_work_pause_proposal_and_cooldown():
    clear_proposals()
    started = datetime(2026, 8, 22, 8, tzinfo=timezone.utc)
    context = {"activity": "working", "started_at": started.isoformat()}
    now = started + timedelta(hours=2)
    first = detect_proposals(context, now=now)
    second = detect_proposals(context, now=now + timedelta(minutes=5))
    assert first[0]["type"] == "working_reminder"
    assert second == []


def test_no_proposal_before_threshold():
    clear_proposals()
    started = datetime(2026, 8, 22, 8, tzinfo=timezone.utc)
    assert detect_proposals({"activity": "studying", "started_at": started.isoformat()}, now=started + timedelta(minutes=30)) == []


def test_proposal_has_no_external_dependency():
    clear_proposals()
    started = datetime(2026, 8, 22, 8, tzinfo=timezone.utc)
    result = detect_proposals({"activity": "sleeping", "started_at": started.isoformat()}, now=started + timedelta(hours=8))
    assert result and result[0]["priority"] == "normal"
