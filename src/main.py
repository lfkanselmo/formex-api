from src.infrastructure.windows_event_loop import ensure_windows_selector_event_loop

ensure_windows_selector_event_loop()

import asyncio  # noqa: E402

import uvicorn  # noqa: E402

if __name__ == "__main__":
    # uvicorn.run()/Server.run() call config.setup_event_loop(), which forces
    # WindowsProactorEventLoopPolicy back on and undoes the line above — so the
    # server is driven directly instead, keeping our selector policy in effect.
    config = uvicorn.Config("src.infrastructure.api.main:app", host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
