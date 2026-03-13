import os
from unittest.mock import MagicMock
from app.ui.import_worker import ImportWorker
from app.core.modes import Mode
from app.plotting.config import load_config


def test_import_worker_sets_correct_env_variable(mocker):
    """
    Checks if the ImportWorker correctly sets the OS environment
    variable based on the Mode passed to it.
    """
    # 1. Mock the dependencies to prevent the worker from actually
    # trying to run the whole pipeline or write to disk.
    mocker.patch("app.ui.import_worker.run_plotting_pipeline")
    mock_converter_cls = MagicMock()

    # 2. Test DEVICE Mode
    worker_device = ImportWorker(
        path="dummy_path", mode=Mode.DEVICE, converter_class=mock_converter_cls
    )
    worker_device.run()
    assert os.environ["MEMRISTOR_MODE"] == Mode.DEVICE.value

    # 3. Test STACK Mode
    worker_stack = ImportWorker(
        path="dummy_path", mode=Mode.STACK, converter_class=mock_converter_cls
    )
    worker_stack.run()
    assert os.environ["MEMRISTOR_MODE"] == Mode.STACK.value


def test_load_config_reads_env_variable(monkeypatch):
    """
    Checks if load_config properly picks up the variable from
    the environment and changes the output directory.
    """
    # Simulate the environment being set to 'Stack Level'
    monkeypatch.setenv("MEMRISTOR_MODE", Mode.STACK.value)

    cfg = load_config()

    # Check that the config mode matches
    assert cfg.mode == Mode.STACK
    # Check that the output path ends with the correct mode name
    assert str(cfg.output_dir).endswith(Mode.STACK.value)

    # Simulate the environment being set to 'Device Level'
    monkeypatch.setenv("MEMRISTOR_MODE", Mode.DEVICE.value)

    cfg_dev = load_config()
    assert cfg_dev.mode == Mode.DEVICE
    assert str(cfg_dev.output_dir).endswith(Mode.DEVICE.value)
