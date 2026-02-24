from app.services.dedup import content_hash, is_near_duplicate


def test_content_hash_is_deterministic() -> None:
    assert content_hash("abc") == content_hash("abc")


def test_near_duplicate_detection() -> None:
    a = "Threat report indicates ransomware increase in finance sector"
    b = "Finance sector sees ransomware increase according to threat report"
    assert is_near_duplicate(a, b, threshold=0.5)
