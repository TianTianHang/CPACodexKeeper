import http.client
import json
import pathlib
import sys
import threading
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.maintainer import CPACodexKeeper
from src.settings import Settings
from src.web import MonitorHandler, MonitorServer


class WebTests(unittest.TestCase):
    def setUp(self):
        self.keeper = CPACodexKeeper(Settings(cpa_endpoint="https://example.com", cpa_token="secret"), dry_run=True)
        self.server = MonitorServer(("127.0.0.1", 0), MonitorHandler, self.keeper, refresh_interval=3)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _request(self, path):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
            body = response.read()
            return response.status, dict(response.getheaders()), body
        finally:
            conn.close()

    def test_api_status_returns_monitor_snapshot(self):
        self.keeper.update_monitor_total(1)
        self.keeper.update_monitor_token("t1", {
            "disabled": False,
            "health": "alive",
            "action": "none",
            "quota_reached": False,
            "near_expiry": False,
            "expired_status": False,
        })

        status, headers, body = self._request("/api/status")

        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["tokens"][0]["name"], "t1")

    def test_healthz_returns_ok(self):
        status, _headers, body = self._request("/healthz")

        self.assertEqual(status, 200)
        self.assertEqual(body, b"ok\n")

    def test_index_returns_html(self):
        status, headers, body = self._request("/")

        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"CPACodexKeeper Monitor", body)
        self.assertIn(b"Live monitor", body)
        self.assertIn("账号状态卡片".encode("utf-8"), body)
        self.assertIn("本轮处理".encode("utf-8"), body)
        self.assertIn("5h".encode("utf-8"), body)
        self.assertIn(b"Week", body)
        self.assertIn(b"Team", body)
        self.assertIn("剩余额度不足".encode("utf-8"), body)


if __name__ == "__main__":
    unittest.main()
