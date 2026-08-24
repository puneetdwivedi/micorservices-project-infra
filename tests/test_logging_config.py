import logging

from utils.logging_config import ColoredFormatter, SUCCESS_LEVEL, configure_logging


def test_configure_logging_defaults_invalid_level_to_info():
    assert configure_logging("invalid") == logging.INFO


def test_colored_formatter_adds_level_prefix_and_color():
    formatter = ColoredFormatter(True)

    success = formatter.format(
        logging.LogRecord("test", SUCCESS_LEVEL, "", 0, "done", (), None)
    )
    error = formatter.format(
        logging.LogRecord("test", logging.ERROR, "", 0, "failed", (), None)
    )

    assert success.startswith("\033[32m\u2705 ")
    assert error.startswith("\033[31m\u274c ")
    assert success.endswith("\033[0m")
    assert error.endswith("\033[0m")
