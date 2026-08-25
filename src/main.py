import logging

from scripts import Build, Deploy
from utils.logging_config import SUCCESS_LEVEL, configure_logging

logger = logging.getLogger(__name__)
configure_logging()


def build():
	logger.info("Starting infrastructure build")
	try:
		synced_keys = Build().build()
	except Exception:
		logger.exception("Infrastructure build failed")
		raise
	logger.log(SUCCESS_LEVEL, "Infrastructure build completed: %d artifacts", len(synced_keys))


def deploy():
	logger.info("Starting infrastructure deployment")
	try:
		Deploy().deploy()
	except Exception:
		logger.exception("Infrastructure deployment failed")
		raise
	logger.log(SUCCESS_LEVEL, "Infrastructure deployment completed")


def main():
	build()
	deploy()


if __name__ == "__main__":
	main()
