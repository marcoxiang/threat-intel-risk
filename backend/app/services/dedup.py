import hashlib
import re
from collections import Counter


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def semantic_similarity(text_a: str, text_b: str) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    counts_a = Counter(tokens_a)
    counts_b = Counter(tokens_b)
    shared = set(counts_a).intersection(counts_b)

    numerator = sum(min(counts_a[token], counts_b[token]) for token in shared)
    denominator = max(sum(counts_a.values()), sum(counts_b.values()))
    return numerator / denominator if denominator else 0.0


def is_near_duplicate(text_a: str, text_b: str, threshold: float = 0.9) -> bool:
    return semantic_similarity(text_a, text_b) >= threshold
