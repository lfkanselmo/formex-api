import asyncio
import sys


def ensure_windows_selector_event_loop() -> None:
    # psycopg's async mode refuses to run on Windows' default ProactorEventLoop
    # (raises InterfaceError). Irrelevant in Docker/Linux, where this is a no-op.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
