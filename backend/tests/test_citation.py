from app.services.citation import link_claims_to_snippets


def test_claims_link_to_best_snippet() -> None:
    claims = ["Ransomware activity increased in healthcare providers"]
    snippets = [
        {"id": "1", "text": "Healthcare providers reported increased ransomware activity this month."},
        {"id": "2", "text": "Unrelated geopolitical commentary."},
    ]

    links = link_claims_to_snippets(claims, snippets)
    assert len(links) == 1
    assert links[0].snippet_id == "1"
