from collections import Counter
from dataclasses import dataclass


@dataclass
class EmergingInputs:
    recent_mentions: int
    baseline_mentions: int
    recent_sectors: list[str]
    baseline_sectors: list[str]
    recent_actor_techniques: list[str]
    baseline_actor_techniques: list[str]
    source_diversity: int
    confidence: float


@dataclass
class EmergingResult:
    trend_ratio: float
    novelty_score: float
    source_diversity: int
    triggered: bool
    trigger_reason: str


def compute_trend_ratio(recent_mentions: int, baseline_mentions: int) -> float:
    baseline_quarter = baseline_mentions / 4
    denominator = max(baseline_quarter, 1)
    return round(recent_mentions / denominator, 4)


def _distribution_shift(recent: list[str], baseline: list[str]) -> float:
    if not recent:
        return 0.0
    if not baseline:
        return 1.0

    recent_count = Counter(recent)
    baseline_count = Counter(baseline)

    recent_set = set(recent_count)
    baseline_set = set(baseline_count)

    new_ratio = len(recent_set - baseline_set) / max(len(recent_set), 1)

    overlap = recent_set & baseline_set
    if not overlap:
        overlap_shift = 1.0
    else:
        total_recent = sum(recent_count.values())
        total_base = sum(baseline_count.values())
        overlap_shift = sum(
            abs((recent_count[k] / total_recent) - (baseline_count[k] / total_base))
            for k in overlap
        ) / max(len(overlap), 1)
    return min(1.0, round((0.6 * new_ratio) + (0.4 * overlap_shift), 4))


def compute_novelty_score(
    recent_sectors: list[str],
    baseline_sectors: list[str],
    recent_actor_techniques: list[str],
    baseline_actor_techniques: list[str],
) -> float:
    sector_shift = _distribution_shift(recent_sectors, baseline_sectors)
    actor_shift = _distribution_shift(recent_actor_techniques, baseline_actor_techniques)
    return round((0.5 * sector_shift) + (0.5 * actor_shift), 4)


def evaluate_emerging(inputs: EmergingInputs) -> EmergingResult:
    trend_ratio = compute_trend_ratio(inputs.recent_mentions, inputs.baseline_mentions)
    novelty_score = compute_novelty_score(
        inputs.recent_sectors,
        inputs.baseline_sectors,
        inputs.recent_actor_techniques,
        inputs.baseline_actor_techniques,
    )

    checks = {
        "trend_ratio>=1.8": trend_ratio >= 1.8,
        "novelty_score>=0.35": novelty_score >= 0.35,
        "source_diversity>=3": inputs.source_diversity >= 3,
        "confidence>=0.70": inputs.confidence >= 0.70,
    }
    triggered = all(checks.values())
    failed = [k for k, passed in checks.items() if not passed]
    reason = "auto-triggered by trend+novelty" if triggered else f"not-triggered: {', '.join(failed)}"

    return EmergingResult(
        trend_ratio=trend_ratio,
        novelty_score=novelty_score,
        source_diversity=inputs.source_diversity,
        triggered=triggered,
        trigger_reason=reason,
    )
