import os
import unittest
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"

from sqlmodel import SQLModel, Session, create_engine, select
from app.services import TitleParser, parse_url_and_save, validate_public_url
from app.models import ParsedPage


class FakeResponse:
    is_redirect = False
    status_code = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        yield b"<html><head><title>Finance &amp; News</title></head><body><svg><title>Lock</title></svg></body></html>"


class ParserTests(unittest.TestCase):
    def test_only_document_title_is_saved(self):
        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)
        try:
            with Session(engine) as session, patch("app.services.validate_public_url"), patch("app.services.requests.get", return_value=FakeResponse()):
                page = parse_url_and_save("https://www.worldbank.org/", session)
                self.assertEqual(page.title, "Finance & News")
                self.assertEqual(session.exec(select(ParsedPage)).one().status_code, 200)
        finally:
            engine.dispose()

    def test_internal_addresses_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_url("http://127.0.0.1/")
        with self.assertRaises(ValueError):
            validate_public_url("file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
