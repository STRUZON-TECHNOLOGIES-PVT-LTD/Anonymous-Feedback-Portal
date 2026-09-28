"""Admin endpoints: auth, submissions list/detail, stats and repeated-name/fingerprint
aggregation (all offline, SQLite-backed)."""

import uuid
from datetime import datetime, timedelta, timezone

from conftest import TEST_ADMIN, add_submission, login

PREVIEW_LEN = 160


def _long_confession() -> str:
    return "x" * 200


class TestLogin:
    def test_success_sets_http_only_cookie(self, client):
        r = client.post(
            "/api/admin/login",
            json={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]},
        )
        assert r.status_code == 200
        assert r.json() == {"username": "admin"}
        set_cookie = r.headers["set-cookie"]
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie
        assert set_cookie.startswith("admin_session=")

    def test_wrong_password_401(self, client):
        r = client.post(
            "/api/admin/login",
            json={"username": TEST_ADMIN["username"], "password": "wrong"},
        )
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid credentials"

    def test_unknown_user_same_error(self, client):
        r = client.post("/api/admin/login", json={"username": "ghost", "password": "anything"})
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid credentials"

    def test_last_login_recorded(self, client):
        client.post(
            "/api/admin/login",
            json={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]},
        )

        import asyncio
        import os

        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        async def fetch():
            engine = create_async_engine(os.environ["DATABASE_URL"])
            try:
                async with engine.connect() as conn:
                    return (
                        await conn.execute(text("SELECT last_login_at IS NOT NULL FROM admins"))
                    ).scalar_one()
            finally:
                await engine.dispose()

        assert asyncio.run(fetch())


class TestMeAndLogout:
    def test_me_authenticated(self, client):
        login(client)
        r = client.get("/api/admin/me")
        assert r.status_code == 200
        assert r.json() == {"username": "admin"}

    def test_me_without_cookie_401(self, client):
        assert client.get("/api/admin/me").status_code == 401

    def test_me_garbage_cookie_401(self, client):
        client.cookies.set("admin_session", "garbage.token.value")
        assert client.get("/api/admin/me").status_code == 401

    def test_logout_clears_session(self, client):
        login(client)
        r = client.post("/api/admin/logout")
        assert r.status_code == 204
        assert client.get("/api/admin/me").status_code == 401


class TestListSubmissions:
    def test_pagination_and_total(self, client):
        for i in range(3):
            add_submission(f"confession {i}", created_at=datetime.now(timezone.utc) - timedelta(minutes=i))
        login(client)

        page1 = client.get("/api/admin/submissions?page=1&page_size=2").json()
        assert page1["total"] == 3
        assert len(page1["items"]) == 2
        # newest first
        assert page1["items"][0]["confession_preview"] == "confession 0"

        page2 = client.get("/api/admin/submissions?page=2&page_size=2").json()
        assert len(page2["items"]) == 1
        assert page2["items"][0]["confession_preview"] == "confession 2"

    def test_preview_truncates_at_160(self, client):
        add_submission(_long_confession())
        login(client)
        item = client.get("/api/admin/submissions").json()["items"][0]
        assert item["confession_preview"] == "x" * PREVIEW_LEN + "..."
        assert len(item["confession_preview"]) == PREVIEW_LEN + 3

    def test_short_confession_not_truncated(self, client):
        add_submission("short")
        login(client)
        item = client.get("/api/admin/submissions").json()["items"][0]
        assert item["confession_preview"] == "short"

    def test_requires_auth(self, client):
        assert client.get("/api/admin/submissions").status_code == 401


class TestGetSubmission:
    def test_detail_with_answers_and_names(self, client):
        qid = 1  # seeded question order 1
        add_submission(
            "Maria handled the client well.",
            answer_specs=[(qid, "Good")],
            created_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        login(client)
        sub_id = client.get("/api/admin/submissions").json()["items"][0]["id"]
        detail = client.get(f"/api/admin/submissions/{sub_id}").json()
        assert detail["confession_text"] == "Maria handled the client well."
        assert detail["extracted_names"] == ["Maria"]
        assert detail["answers"][0]["question_text"] == "How would you rate your overall experience this month?"
        assert detail["answers"][0]["selected_option"] == "Good"
        assert detail["ip_address"] == "10.0.0.9"

    def test_unknown_uuid_404(self, client):
        login(client)
        r = client.get("/api/admin/submissions/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404

    def test_invalid_uuid_string_404_not_500(self, client):
        # Regression: a non-UUID path segment used to reach Postgres and blow
        # up with a DataError -> 500. It must be a clean 404.
        login(client)
        r = client.get("/api/admin/submissions/not-a-uuid")
        assert r.status_code == 404
        assert r.json()["detail"] == "Submission not found"


class TestStats:
    def test_zero_filled_30_day_series(self, client):
        now = datetime.now(timezone.utc)
        # Anchor at noon local to avoid a midnight boundary crossing the date.
        noon_today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        add_submission("today 1", created_at=noon_today)
        add_submission("today 2", created_at=noon_today + timedelta(minutes=1))
        add_submission("yesterday", created_at=noon_today - timedelta(days=1))
        login(client)

        stats = client.get("/api/admin/stats").json()
        series = stats["submissions_last_30_days"]
        assert len(series) == 30
        assert series[-1]["date"] == now.date().isoformat()
        assert series[-1]["count"] == 2  # today's two submissions
        assert series[-2]["date"] == (now.date() - timedelta(days=1)).isoformat()
        assert series[-2]["count"] == 1  # yesterday's single submission
        assert series[-3]["count"] == 0  # gap filled with zero, not skipped
        assert sum(day["count"] for day in series) == 3
        assert stats["total_submissions"] == 3

    def test_question_breakdown_counts_options(self, client):
        qid = 1
        add_submission("a", answer_specs=[(qid, "Good")])
        add_submission("b", answer_specs=[(qid, "Excellent")])
        add_submission("c", answer_specs=[(qid, "Good")])
        login(client)

        stats = client.get("/api/admin/stats").json()
        breakdown = {b["question_id"]: b for b in stats["question_breakdown"]}
        assert breakdown[qid]["option_counts"] == {"Good": 2, "Excellent": 1}

    def test_repeated_fingerprints_with_distinct_ips(self, client):
        add_submission("one", fingerprint="fp-A", ip="10.0.0.1")
        add_submission("two", fingerprint="fp-A", ip="10.0.0.2")
        add_submission("three", fingerprint="fp-B")
        login(client)

        stats = client.get("/api/admin/stats").json()
        repeated = stats["top_repeated_fingerprints"]
        assert any(
            fp["device_fingerprint"] == "fp-A"
            and fp["count"] == 2
            and sorted(fp["ip_addresses"]) == ["10.0.0.1", "10.0.0.2"]
            for fp in repeated
        )
        assert not any(fp["device_fingerprint"] == "fp-B" for fp in repeated)

    def test_repeated_names_endpoint_and_min_count(self, client):
        add_submission("Maria leads the team well.")
        add_submission("Maria deserves more recognition.")
        add_submission("Pedro is new.")
        login(client)

        names = client.get("/api/admin/repeated-names").json()
        maria = next(n for n in names if n["name"] == "Maria")
        assert maria["mention_count"] == 2
        assert len(maria["submission_ids"]) == 2
        assert all(uuid.UUID(sid) for sid in maria["submission_ids"])

        # min_count=3 filters Maria (2 mentions) and Pedro (1) out entirely.
        filtered = client.get("/api/admin/repeated-names?min_count=3").json()
        assert filtered == []

    def test_requires_auth(self, client):
        assert client.get("/api/admin/stats").status_code == 401