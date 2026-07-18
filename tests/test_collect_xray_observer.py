import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class CollectXrayObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.scripts_dir = str(self.repo_root / "scripts")
        if self.scripts_dir not in sys.path:
            sys.path.insert(0, self.scripts_dir)

        spec = importlib.util.spec_from_file_location(
            "collect_xray_observer",
            self.repo_root / "scripts" / "collect_xray_observer.py",
        )
        self.collector = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        sys.modules[spec.name] = self.collector
        spec.loader.exec_module(self.collector)

    def test_parse_xray_access_log_line_extracts_identity_and_source_ip(self) -> None:
        row = self.collector.parse_xray_access_log_line(
            "2023/11/22 17:01:32 192.168.1.33:11421 accepted tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice",
            source_timezone="+03:00",
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["occurred_at"], "2023-11-22T14:01:32Z")
        self.assertEqual(row["source_ip"], "192.168.1.33")
        self.assertEqual(row["client_email"], "panel-alice")
        self.assertEqual(row["inbound_tag"], "VLESS_INBOUND")

    def test_collect_observations_uses_cursor_and_aggregates_by_minute_identity_and_ip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            log_path = tmp_path / "access.log"
            cursor_path = tmp_path / "observer-cursor.json"
            log_path.write_text(
                "\n".join(
                    [
                        "2023/11/22 17:01:32 192.168.1.33:11421 accepted tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice",
                        "2023/11/22 17:01:36 192.168.1.33:11424 accepted tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice",
                        "2023/11/22 17:02:01 192.168.1.44:12000 accepted tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-bob",
                        "this is not an xray access log line",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            first = self.collector.collect_observations(
                log_path=log_path,
                cursor_path=cursor_path,
                source_timezone="+03:00",
            )
            self.assertEqual(len(first["observations"]), 2)
            self.assertEqual(first["parse_error_count"], 1)
            self.assertEqual(first["observations"][0]["client_email"], "panel-alice")
            self.assertEqual(first["observations"][0]["source_ip"], "192.168.1.33")
            self.assertEqual(first["observations"][0]["occurred_at"], "2023-11-22T14:01:00Z")
            self.assertEqual(first["observations"][1]["client_email"], "panel-bob")
            self.assertTrue(cursor_path.exists())

            second = self.collector.collect_observations(
                log_path=log_path,
                cursor_path=cursor_path,
                source_timezone="+03:00",
            )
            self.assertEqual(second["observations"], [])
            self.assertEqual(second["parse_error_count"], 0)

            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    "2023/11/22 17:03:10 203.0.113.9:13000 accepted tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice\n"
                )

            third = self.collector.collect_observations(
                log_path=log_path,
                cursor_path=cursor_path,
                source_timezone="+03:00",
            )
            self.assertEqual(len(third["observations"]), 1)
            self.assertEqual(third["parse_error_count"], 0)
            self.assertEqual(third["observations"][0]["occurred_at"], "2023-11-22T14:03:00Z")
            cursor_payload = json.loads(cursor_path.read_text(encoding="utf-8"))
            self.assertGreater(int(cursor_payload["offset"]), 0)

    def test_run_pushes_heartbeat_even_without_valid_observations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            log_path = tmp_path / "access.log"
            cursor_path = tmp_path / "observer-cursor.json"
            log_path.write_text("broken xray line\n", encoding="utf-8")

            with mock.patch.object(self.collector, "push_observer_batch", return_value={"accepted_count": 0}) as mocked_push:
                result = self.collector.run(
                    log_path=log_path,
                    cursor_path=cursor_path,
                    api_url="https://api.pokrov.test/api/internal/observer/batches",
                    node_code="pl",
                    secret="pl-secret",
                    source_timezone="UTC",
                )

        self.assertTrue(result["sent"])
        payload = result["payload"]
        self.assertEqual(payload["observations"], [])
        self.assertEqual(payload["parse_error_count"], 1)
        mocked_push.assert_called_once()

    def test_offset_aware_timestamps_are_canonical_utc_z(self) -> None:
        cases = (
            ("2023-11-22T14:01:32Z", "2023-11-22T14:01:32Z"),
            ("2023-11-22T17:01:32+03:00", "2023-11-22T14:01:32Z"),
            ("2023-11-22T09:01:32-05:00", "2023-11-22T14:01:32Z"),
        )
        for timestamp, expected in cases:
            with self.subTest(timestamp=timestamp):
                row = self.collector.parse_xray_access_log_line(
                    f"{timestamp} 192.168.1.33:11421 accepted tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice"
                )
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["occurred_at"], expected)

    def test_naive_timestamp_uses_explicit_fixed_offset_timezone(self) -> None:
        cases = (
            ("2023/11/22 17:01:32", "+03:00"),
            ("2023/11/22 10:01:32", "-04:00"),
        )
        for timestamp, source_timezone in cases:
            with self.subTest(source_timezone=source_timezone):
                row = self.collector.parse_xray_access_log_line(
                    f"{timestamp} 192.168.1.33:11421 accepted "
                    "tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice",
                    source_timezone=source_timezone,
                )
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["occurred_at"], "2023-11-22T14:01:32Z")

    def test_naive_timestamp_accepts_only_utc_name_aliases(self) -> None:
        line = (
            "2023/11/22 14:01:32 192.168.1.33:11421 accepted "
            "tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice"
        )
        for source_timezone in ("UTC", "Z"):
            with self.subTest(source_timezone=source_timezone):
                row = self.collector.parse_xray_access_log_line(
                    line,
                    source_timezone=source_timezone,
                )
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["occurred_at"], "2023-11-22T14:01:32Z")

    def test_naive_timestamp_without_source_timezone_is_counted_as_parse_error(self) -> None:
        self._assert_naive_timezone_failure_is_counted(source_timezone="")

    def test_naive_timestamp_with_invalid_or_iana_timezone_is_counted_as_parse_error(self) -> None:
        for source_timezone in ("Mars/Olympus_Mons", "Europe/Moscow", "+24:00", "-12:60"):
            with self.subTest(source_timezone=source_timezone):
                self._assert_naive_timezone_failure_is_counted(source_timezone=source_timezone)

    def _assert_naive_timezone_failure_is_counted(self, *, source_timezone: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            log_path = tmp_path / "access.log"
            cursor_path = tmp_path / "observer-cursor.json"
            log_path.write_text(
                "2023/11/22 17:01:32 192.168.1.33:11421 accepted "
                "tcp192.168.1.36:443 [VLESS_INBOUND -> proxy] email: panel-alice\n",
                encoding="utf-8",
            )

            collected = self.collector.collect_observations(
                log_path=log_path,
                cursor_path=cursor_path,
                source_timezone=source_timezone,
            )

        self.assertEqual(collected["observations"], [])
        self.assertEqual(collected["parse_error_count"], 1)


if __name__ == "__main__":
    unittest.main()
