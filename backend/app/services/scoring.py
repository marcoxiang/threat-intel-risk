from app.models.enums import SeverityBand


def clamp_factor(value: int) -> int:
    return max(1, min(5, value))


def calculate_composite_score(
    tef: int,
    vulnerability: int,
    primary_loss: int,
    secondary_loss: int,
) -> float:
    tef = clamp_factor(tef)
    vulnerability = clamp_factor(vulnerability)
    primary_loss = clamp_factor(primary_loss)
    secondary_loss = clamp_factor(secondary_loss)

    score = 20 * (
        (0.30 * tef)
        + (0.25 * vulnerability)
        + (0.30 * primary_loss)
        + (0.15 * secondary_loss)
    )
    return round(score, 2)


def severity_band(score: float) -> SeverityBand:
    if score < 40:
        return SeverityBand.LOW
    if score < 60:
        return SeverityBand.MODERATE
    if score < 80:
        return SeverityBand.HIGH
    return SeverityBand.CRITICAL
