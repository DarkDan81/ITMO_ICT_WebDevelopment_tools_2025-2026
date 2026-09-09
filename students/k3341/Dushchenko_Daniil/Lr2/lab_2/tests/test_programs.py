import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]


class PageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500 if self.path == "/error" else 200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        content = "<html>no title</html>" if self.path == "/empty" else "<title>Финансы &amp; бюджет</title>"
        self.wfile.write(content.encode())

    def log_message(self, *args):
        pass


class ProgramsTests(unittest.TestCase):
    def test_sum_modes(self):
        for mode, limit in [("formula", 10**13), ("loop", 100003)]:
            for method in ["threading", "multiprocessing", "async"]:
                with self.subTest(mode=mode, method=method):
                    env = dict(os.environ, LAB2_SUM_MODE=mode, LAB2_SUM_LIMIT=str(limit), LAB2_WORKERS="4")
                    result = subprocess.run([sys.executable, f"task1_{method}.py"], cwd=ROOT, env=env,
                                            capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(str(limit * (limit + 1) // 2), result.stdout)

    def test_parsers_continue_after_failed_page(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), PageHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                for method in ["threading", "multiprocessing", "async"]:
                    with self.subTest(method=method):
                        db = Path(temporary) / f"{method}.db"
                        urls = [f"http://127.0.0.1:{server.server_port}/{name}" for name in ["one", "error", "two", "empty"]]
                        env = dict(os.environ, LAB2_URLS=json.dumps(urls), LAB2_WORKERS="2",
                                   DATABASE_URL="sqlite:///" + db.as_posix(), PYTHONIOENCODING="utf-8")
                        result = subprocess.run([sys.executable, f"task2_{method}.py"], cwd=ROOT, env=env,
                                                capture_output=True, text=True, encoding="utf-8", timeout=20)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn("Successful: 2; Failed: 2; Total: 4", result.stdout)
                        conn = sqlite3.connect(db)
                        try:
                            rows = conn.execute("SELECT title, status_code FROM parsedpage").fetchall()
                            self.assertEqual(rows, [("Финансы & бюджет", 200)] * 2)
                        finally:
                            conn.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
