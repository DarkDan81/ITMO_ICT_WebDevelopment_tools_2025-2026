"""Проверки сценариев API. Используется отдельная БД в памяти."""
import os
import unittest

os.environ["JWT_SECRET"] = "test-secret-" * 8
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.db import get_session
from app.main import app
from app.models import User


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(self.engine)

        def session_override():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = session_override
        self.client = TestClient(app, raise_server_exceptions=False)
        self.headers = self.register("student@example.com")
        response = self.client.post("/categories", headers=self.headers, json={"name": "Еда", "monthly_limit": 100})
        self.assertEqual(response.status_code, 201, response.text)
        self.category = response.json()["id"]
        response = self.client.post("/tags", headers=self.headers, json={"name": "учёба"})
        self.tag = response.json()["id"]

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def register(self, email):
        response = self.client.post("/auth/register", json={"email": email, "full_name": "Студент", "password": "password123"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("hashed_password", response.json())
        response = self.client.post("/auth/token", data={"username": email, "password": "password123"})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def operation(self, **changes):
        return {"title": "Обед", "amount": 120, "operation_type": "expense",
                "operation_date": "2026-09-09T12:00:00", "category_id": self.category,
                "tags": [{"tag_id": self.tag, "priority": 2}], **changes}

    def test_crud_and_report(self):
        created = self.client.post("/operations", headers=self.headers, json=self.operation())
        self.assertEqual(created.status_code, 201, created.text)
        item = created.json()
        self.assertEqual(item["category"]["name"], "Еда")
        self.assertEqual(item["tags"][0]["priority"], 2)
        self.client.post("/operations", headers=self.headers, json=self.operation(amount=500, operation_type="income"))
        self.client.post("/operations", headers=self.headers, json=self.operation(amount=999, operation_date="2026-10-01T00:00:00"))
        report = self.client.get("/reports/monthly?year=2026&month=9", headers=self.headers)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual((report.json()["income"], report.json()["expense"], report.json()["balance"]), (500, 120, 380))
        self.assertEqual(report.json()["categories"][0]["remaining"], -20)
        self.assertTrue(report.json()["categories"][0]["exceeded"])
        response = self.client.patch(f'/operations/{item["id"]}', headers=self.headers, json={"amount": 50, "tags": []})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["tags"], [])
        response = self.client.delete(f'/operations/{item["id"]}', headers=self.headers)
        self.assertEqual(response.status_code, 204, response.text)

    def test_bad_requests_do_not_save_partial_operation(self):
        bad = self.client.post("/operations", headers=self.headers, json=self.operation(tags=[{"tag_id": 999}]))
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.client.get("/operations", headers=self.headers).json(), [])
        bad = self.client.post("/operations", headers=self.headers,
                               json=self.operation(tags=[{"tag_id": self.tag}, {"tag_id": self.tag}]))
        self.assertEqual(bad.status_code, 422)
        item = self.client.post("/operations", headers=self.headers, json=self.operation()).json()
        bad = self.client.patch(f'/operations/{item["id"]}', headers=self.headers,
                                json={"amount": 999, "tags": [{"tag_id": 999}]})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.client.get(f'/operations/{item["id"]}', headers=self.headers).json()["amount"], 120)
        for payload in [{"title": None}, {"category_id": None}, {"amount": -1}, {"title": ""}]:
            response = self.client.patch(f'/operations/{item["id"]}', headers=self.headers, json=payload)
            self.assertEqual(response.status_code, 422, response.text)

    def test_auth_and_ownership(self):
        self.assertEqual(self.client.get("/operations").status_code, 401)
        self.assertEqual(self.client.get("/operations", headers={"Authorization": "Bearer broken"}).status_code, 401)
        other = self.register("other@example.com")
        item = self.client.post("/operations", headers=self.headers, json=self.operation()).json()
        self.assertEqual(self.client.get("/operations", headers=other).json(), [])
        self.assertEqual(self.client.get(f'/operations/{item["id"]}', headers=other).status_code, 404)
        self.assertEqual(self.client.post("/operations", headers=other, json=self.operation()).status_code, 404)
        self.assertEqual(self.client.get("/reports/monthly?year=2026&month=9", headers=other).json()["expense"], 0)
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.email == "student@example.com")).one()
            self.assertNotEqual(user.hashed_password, "password123")
        changed = self.client.post("/users/me/password", headers=self.headers,
                                   json={"old_password": "password123", "new_password": "new-password123"})
        self.assertEqual(changed.status_code, 204)
        self.assertEqual(self.client.get("/users/me", headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post("/auth/token", data={"username": "student@example.com", "password": "password123"}).status_code, 401)
        self.assertEqual(self.client.post("/auth/token", data={"username": "student@example.com", "password": "new-password123"}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
