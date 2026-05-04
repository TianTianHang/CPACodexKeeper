import threading

from .maintainer import CPACodexKeeper
from .settings import SettingsError, load_settings
from .web import run_web_server


def build_arg_parser():
    import argparse

    parser = argparse.ArgumentParser(description="CPACodexKeeper")
    parser.add_argument("--dry-run", action="store_true", help="演练模式，不实际修改 / Dry run")
    parser.add_argument("--daemon", action="store_true", default=True, help="守护模式，默认开启 / Run forever")
    parser.add_argument("--once", dest="daemon", action="store_false", help="仅执行一轮后退出 / Run once")
    parser.add_argument("--web", action="store_true", help="启动只读 Web 面板并并行运行自动维护 / Run read-only web monitor")
    parser.add_argument("--web-host", help="Web 面板监听地址 / Web bind host")
    parser.add_argument("--web-port", type=int, help="Web 面板监听端口 / Web bind port")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    try:
        settings = load_settings()
    except SettingsError as exc:
        parser.exit(status=2, message=f"Configuration error: {exc}\n")

    maintainer = CPACodexKeeper(settings=settings, dry_run=args.dry_run)
    if args.web:
        maintenance_thread = threading.Thread(
            target=maintainer.run_forever if args.daemon else maintainer.run,
            kwargs={"interval_seconds": settings.interval_seconds} if args.daemon else {},
            daemon=True,
        )
        maintenance_thread.start()
        run_web_server(
            maintainer,
            args.web_host or settings.web_host,
            args.web_port or settings.web_port,
            refresh_interval=settings.web_refresh_interval,
        )
        return 0
    if args.daemon:
        maintainer.run_forever(interval_seconds=settings.interval_seconds)
        return 0
    maintainer.run()
    return 0
