import logging

from utils.logging_config import configure_logging


logger = logging.getLogger(__name__)


def main():
	configure_logging()
	logger.warning("Deployment workflow is not implemented yet")
