import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.cli import build_arg_parser, main
from src.settings import Settings


class CLITests(unittest.TestCase):
    def test_defaults_to_daemon_mode(self):
        parser = build_arg_parser()
        args = parser.parse_args([])

        self.assertTrue(args.daemon)

    def test_once_disables_daemon_mode(self):
        parser = build_arg_parser()
        args = parser.parse_args(["--once"])

        self.assertFalse(args.daemon)

    def test_web_arguments_parse(self):
        parser = build_arg_parser()
        args = parser.parse_args(["--web", "--web-host", "127.0.0.1", "--web-port", "9090"])

        self.assertTrue(args.web)
        self.assertEqual(args.web_host, "127.0.0.1")
        self.assertEqual(args.web_port, 9090)

    @patch("src.cli.load_settings")
    @patch("src.cli.CPACodexKeeper")
    @patch("sys.argv", ["prog", "--once"])
    def test_main_runs_once(self, keeper_cls, load_settings_mock):
        load_settings_mock.return_value = Settings(
            cpa_endpoint="https://example.com",
            cpa_token="secret",
        )
        keeper = keeper_cls.return_value

        exit_code = main()

        self.assertEqual(exit_code, 0)
        keeper.run.assert_called_once()
        keeper.run_forever.assert_not_called()

    @patch("src.cli.run_web_server")
    @patch("src.cli.threading.Thread")
    @patch("src.cli.load_settings")
    @patch("src.cli.CPACodexKeeper")
    @patch("sys.argv", ["prog", "--web", "--web-host", "127.0.0.1", "--web-port", "9090"])
    def test_main_starts_web_and_maintenance_thread(self, keeper_cls, load_settings_mock, thread_cls, run_web_server_mock):
        settings = Settings(
            cpa_endpoint="https://example.com",
            cpa_token="secret",
            web_refresh_interval=7,
        )
        load_settings_mock.return_value = settings
        keeper = keeper_cls.return_value
        thread = thread_cls.return_value

        exit_code = main()

        self.assertEqual(exit_code, 0)
        thread_cls.assert_called_once()
        self.assertIs(thread_cls.call_args.kwargs["target"], keeper.run_forever)
        self.assertEqual(thread_cls.call_args.kwargs["kwargs"], {"interval_seconds": settings.interval_seconds})
        self.assertTrue(thread_cls.call_args.kwargs["daemon"])
        thread.start.assert_called_once()
        run_web_server_mock.assert_called_once_with(keeper, "127.0.0.1", 9090, refresh_interval=7)
