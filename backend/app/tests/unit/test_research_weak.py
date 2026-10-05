"""Research flags searches whose best passage is below the chat threshold
(an off-topic search listed 10 weak passages with no warning; 2026-10-06)."""

import pytest

from app.core.security import create_access_token, hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.research import ResearchResult
from app.services import research_service


def _result(score):
    return ResearchResult(id="x", title="T", citation="", court=None, year=None, case_type="statute",
                          excerpt="e", text="t", relevance=score)


@pytest.mark.parametrize("scores, weak", [([0.52, 0.43], True), ([0.81, 0.60], False), ([], False)])
def test_weak_matches_flag(client, db_session, monkeypatch, scores, weak):
    u = User(email="r@gmail.com", password_hash=hash_password("x"), full_name="R", role=UserRole.STUDENT,
             is_active=True, is_verified=True)
    db_session.add(u)
    db_session.commit()
    monkeypatch.setattr(research_service.ResearchService, "search",
                        lambda self, *a, **k: [_result(s) for s in scores])
    tok = create_access_token(u.id, "student", u.token_version)
    r = client.post("/api/v1/research/search", json={"query": "biryani recipe"},
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["weak_matches"] is weak
    assert len(r.json()["results"]) == len(scores)  # nothing is hidden
