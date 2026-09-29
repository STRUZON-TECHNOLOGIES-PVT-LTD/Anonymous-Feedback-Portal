"""Public endpoints: questions list + feedback submission (incl. bot checks,
answer validation, fingerprint re-hash, rate limiting)."""

import asyncio
import hashlib
import uuid

from conftest import count_rows, question_id_by_index
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

VALID_PAYLOAD = {
    "confession_text": "John never listens during standup",
    "answers": [],
    "device": {},
}


def _submit(client, **overrides):
    payload = {**VALID_PAYLOAD, **overrides}
    return client.post("/api/feedback", json=payload)


def _set_question_active(qid: int, active: bool) -> None:
    import os

    engine_url = os.environ["DATABASE_URL"]

    async def update():
        engine = create_async_engine(engine_url)
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text("UPDATE questions SET active = :a WHERE id = :qid"),
                    {"a": active, "qid": qid},
                )
        finally:
            await engine.dispose()

    asyncio.run(update())


class TestListQuestions:
    def test_returns_seeded_questions_in_order(self, client):
        r = client.get("/api/questions")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 10
        assert [q["order"] for q in data] == list(range(1, 11))
        assert data[0]["text"] == "How would you rate your overall experience this month?"

    def test_hides_inactive_questions(self, client):
        _set_question_active(question_id_by_index(1), False)
        data = client.get("/api/questions").json()
        assert len(data) == 9


class TestSubmitFeedback:
    def test_happy_path(self, client):
        qid = question_id_by_index(1)
        r = _submit(
            client,
            answers=[{"question_id": qid, "selected_option": "Good"}],
            device={"user_agent": "pytest", "screen_resolution": "1920x1080"},
            form_seconds=12.0,
        )
        assert r.status_code == 201
        body = r.json()
        uuid.UUID(body["id"])  # must parse
        assert body["submitted_at"]
        assert count_rows("submissions") == 1

    def test_names_persisted_normalized(self, client):
        r = _submit(client, confession_text="John's team did great. John is reliable.", form_seconds=10.0)
        assert r.status_code == 201
        from conftest import login

        login(client)
        detail = client.get(f"/api/admin/submissions/{r.json()['id']}").json()
        assert detail["extracted_names"] == ["John's"]

    def test_fingerprint_rehashed_server_side(self, client):
        r = _submit(client, device={"fingerprint_hash": "client-supplied-fp"}, form_seconds=10.0)
        assert r.status_code == 201
        from conftest import login

        login(client)
        detail = client.get(f"/api/admin/submissions/{r.json()['id']}").json()
        assert detail["device_fingerprint"] == hashlib.sha256(b"client-supplied-fp").hexdigest()

    def test_ip_recorded(self, client):
        r = _submit(client, form_seconds=10.0)
        assert r.status_code == 201
        from conftest import login

        login(client)
        detail = client.get(f"/api/admin/submissions/{r.json()['id']}").json()
        assert detail["ip_address"]  # TestClient reports an address

    def test_invalid_question_id_rejected(self, client):
        r = _submit(client, answers=[{"question_id": 999999, "selected_option": "x"}], form_seconds=10.0)
        assert r.status_code == 400
        assert r.json()["detail"] == "Invalid question_id in answers"
        assert count_rows("submissions") == 0

    def test_duplicate_question_id_rejected(self, client):
        qid = question_id_by_index(1)
        r = _submit(
            client,
            answers=[
                {"question_id": qid, "selected_option": "Good"},
                {"question_id": qid, "selected_option": "Excellent"},
            ],
            form_seconds=10.0,
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Duplicate question_id in answers"
        assert count_rows("submissions") == 0

    def test_inactive_question_rejected(self, client):
        qid = question_id_by_index(1)
        _set_question_active(qid, False)
        r = _submit(client, answers=[{"question_id": qid, "selected_option": "Good"}], form_seconds=10.0)
        assert r.status_code == 400
        assert r.json()["detail"] == "Invalid question_id in answers"
        assert count_rows("submissions") == 0

    def test_honeypot_fakes_success_without_persisting(self, client):
        r = _submit(client, website="http://spam.example", form_seconds=10.0)
        assert r.status_code == 201
        assert count_rows("submissions") == 0

    def test_too_fast_fakes_success_without_persisting(self, client):
        r = _submit(client, form_seconds=0.5)
        assert r.status_code == 201
        assert count_rows("submissions") == 0


class TestSubmitRateLimit:
    def test_fourth_submission_within_minute_is_429(self, client):
        qid = question_id_by_index(1)
        payload = {
            **VALID_PAYLOAD,
            "answers": [{"question_id": qid, "selected_option": "Good"}],
            "form_seconds": 10.0,
        }
        app_state = client.app.state
        # SUBMIT_RATE_LIMIT is "3/minute" (set in conftest); TestClient shares
        # one remote address, so three fill the bucket and the fourth trips it.
        app_state.limiter.enabled = True
        try:
            for _ in range(3):
                assert client.post("/api/feedback", json=payload).status_code == 201
            assert client.post("/api/feedback", json=payload).status_code == 429
        finally:
            app_state.limiter.enabled = False

        assert count_rows("submissions") == 3