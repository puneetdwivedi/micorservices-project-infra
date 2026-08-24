import logging
import os
import sys
from typing import Optional


SUCCESS_LEVEL = 25
_LEVELS = {
	"DEBUG": logging.DEBUG,
	"INFO": logging.INFO,
	"WARNING": logging.WARNING,
	"ERROR": logging.ERROR,
	"SUCCESS": SUCCESS_LEVEL,
}
_COLORS = {
	logging.DEBUG: "\033[36m",
	logging.INFO: "\033[37m",
	logging.WARNING: "\033[33m",
	logging.ERROR: "\033[31m",
	SUCCESS_LEVEL: "\033[32m",
}
_PREFIXES = {
	logging.DEBUG: "\U0001f50d ",
	logging.INFO: "\u2139\ufe0f ",
	logging.WARNING: "\u26a0\ufe0f ",
	logging.ERROR: "\u274c ",
	SUCCESS_LEVEL: "\u2705 ",
}
_RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
	"""Format log records with colors for interactive terminal output."""

	def __init__(self, use_color: bool):
		super().__init__("%(asctime)s %(levelname)s %(name)s - %(message)s")
		self.use_color = use_color

	def format(self, record: logging.LogRecord) -> str:
		message = super().format(record)
		message = f"{_PREFIXES.get(record.levelno, '')}{message}"
		if not self.use_color:
			return message
		color = _COLORS.get(record.levelno, "")
		return f"{color}{message}{_RESET}" if color else message


logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def configure_logging(level: Optional[str] = None) -> int:
	"""Configure application logging from an explicit value or LOG_LEVEL."""
	configured_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
	log_level = _LEVELS.get(configured_level, logging.INFO)
	stream = logging.StreamHandler(sys.stderr)
	stream.setFormatter(ColoredFormatter(stream.stream.isatty()))
	logging.basicConfig(
		level=log_level,
		handlers=[stream],
		force=True,
	)
	return log_level