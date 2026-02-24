from app.models.enums import SeverityBand
from app.services.scoring import calculate_composite_score, severity_band


def test_calculate_composite_score() -> None:
    score = calculate_composite_score(5, 5, 5, 5)
    assert score == 100.0


def test_severity_band_thresholds() -> None:
    assert severity_band(39) == SeverityBand.LOW
    assert severity_band(40) == SeverityBand.MODERATE
    assert severity_band(60) == SeverityBand.HIGH
    assert severity_band(80) == SeverityBand.CRITICAL
