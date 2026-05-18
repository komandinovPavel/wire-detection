from app import AppController
from app.factory import build_controller


class MissingModelConfig:
    MODEL_PATH = "missing-model-for-factory-test.pt"


def test_build_controller_returns_app_controller():
    controller = build_controller(MissingModelConfig())

    assert isinstance(controller, AppController)
