import pytest
from src.infrastructure.api.rate_limiting import limiter
from src.infrastructure.windows_event_loop import ensure_windows_selector_event_loop

ensure_windows_selector_event_loop()


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    # Integration tests register/log in far more often per run than a real
    # client would per hour; without this, later tests would trip limits
    # meant for actual abuse, not test volume.
    limiter.reset()
