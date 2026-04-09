import pytest

from app.core.metrics import metrics_store
from app.main import app


@pytest.fixture(autouse=True)
def reset_app_state():
    metrics_store.reset()
    app.dependency_overrides.clear()
    yield
    metrics_store.reset()
    app.dependency_overrides.clear()
