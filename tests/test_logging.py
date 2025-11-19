import logging
from pathlib import Path
from app.utils.logging import setup_logging, get_logger


def test_setup_logging():
    setup_logging("INFO")
    logger = get_logger(__name__)
    assert logger is not None
    assert logger.level == logging.INFO or logger.level == 0


def test_get_logger():
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"


def test_log_messages():
    setup_logging("DEBUG")
    logger = get_logger("test")

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")


def test_log_file_created():
    setup_logging("INFO")
    logger = get_logger("test")
    logger.info("Test log message")

    log_dir = Path("logs")
    assert log_dir.exists()

    log_files = list(log_dir.glob("*.log"))
    assert len(log_files) > 0
