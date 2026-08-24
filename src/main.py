import logging

from scripts import Build
from utils.logging_config import SUCCESS_LEVEL, configure_logging

logger = logging.getLogger(__name__)


def build():
	logger.info("Starting infrastructure build")
	try:
		synced_keys = Build().build()
	except Exception:
		logger.exception("Infrastructure build failed")
		raise
	logger.log(SUCCESS_LEVEL, "Infrastructure build completed: %d artifacts", len(synced_keys))


def main():
	configure_logging()
	build()


if __name__ == "__main__":
	main()
