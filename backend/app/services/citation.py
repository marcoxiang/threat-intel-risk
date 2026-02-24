import re
from collections import Counter
from dataclasses import dataclass


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass
class LinkResult:
    claim: str
    snippet_id: str
    score: float


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def _overlap_score(a: str, b: str) -> float:
    ta = Counter(_tokenize(a))
    tb = Counter(_tokenize(b))
    if not ta or not tb:
        return 0.0
    overlap = sum(min(ta[k], tb[k]) for k in ta.keys() & tb.keys())
    denom = max(sum(ta.values()), 1)
    return overlap / denom


def link_claims_to_snippets(
    claims: list[str], snippets: list[dict], min_score: float = 0.15
) -> list[LinkResult]:
    links: list[LinkResult] = []
    for claim in claims:
        best: tuple[str, float] | None = None
        for snippet in snippets:
            score = _overlap_score(claim, snippet["text"])
            if best is None or score > best[1]:
                best = (str(snippet["id"]), score)
        if best and best[1] >= min_score:
            links.append(LinkResult(claim=claim, snippet_id=best[0], score=round(best[1], 4)))
    return links
