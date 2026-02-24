from app.services.emerging import EmergingInputs, evaluate_emerging


def test_emerging_triggers_when_all_conditions_pass() -> None:
    result = evaluate_emerging(
        EmergingInputs(
            recent_mentions=20,
            baseline_mentions=16,
            recent_sectors=["Finance", "Energy", "Retail"],
            baseline_sectors=["Finance", "Finance", "Finance"],
            recent_actor_techniques=["APT1:Ransomware", "APT2:Ransomware"],
            baseline_actor_techniques=["APT1:Phishing"],
            source_diversity=4,
            confidence=0.9,
        )
    )
    assert result.triggered is True


def test_emerging_not_triggered_for_low_confidence() -> None:
    result = evaluate_emerging(
        EmergingInputs(
            recent_mentions=20,
            baseline_mentions=16,
            recent_sectors=["Finance", "Energy", "Retail"],
            baseline_sectors=["Finance", "Finance", "Finance"],
            recent_actor_techniques=["APT1:Ransomware", "APT2:Ransomware"],
            baseline_actor_techniques=["APT1:Phishing"],
            source_diversity=4,
            confidence=0.5,
        )
    )
    assert result.triggered is False
