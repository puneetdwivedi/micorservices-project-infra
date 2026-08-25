import json
import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from utils import constants
from utils.constants import (
	AWS_ACCESS_KEY,
	AWS_DEFAULT_REGION,
	AWS_SECRET_KEY,
	PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
	PROJECT_NAME_PREFIX,
)
from utils.logging_config import SUCCESS_LEVEL
from utils.services import S3Manager

logger = logging.getLogger(__name__)


class Build:
	"""Build and publish CloudFormation and Lambda artifacts to S3."""

	def __init__(
		self,
		project_root: Path | None = None,
		bucket_name: str = PDW_S3_BUCKET_SANDBOX_PROJECT_PARTIALS,
		project_name_prefix: str = PROJECT_NAME_PREFIX,
		s3_manager: S3Manager | None = None,
	):
		self.project_root = project_root or Path(__file__).resolve().parents[1]
		self.infra_root = self.project_root / "infra"
		self.bucket_name = bucket_name
		self.project_name_prefix = project_name_prefix.strip("/")
		self.s3_manager = s3_manager or S3Manager(
			AWS_ACCESS_KEY,
			AWS_SECRET_KEY,
			AWS_DEFAULT_REGION,
		)

	def build(self) -> list[str]:
		"""Create the artifact bucket and sync all available infra artifacts."""
		logger.info("Starting infrastructure artifact sync")
		self.ensure_bucket()
		self.build_configuration()

		synced_keys = []
		synced_keys.extend(self.sync_directory("stacks"))
		synced_keys.extend(self.sync_directory("templates"))
		synced_keys.extend(self.package_and_sync_lambdas())
		logger.log(SUCCESS_LEVEL, "Synchronized %d infrastructure artifacts", len(synced_keys))
		return synced_keys

	def build_configuration(self) -> Path:
		"""Render stack configuration placeholders using values from constants.py."""
		source_path = self.infra_root / "stacks" / "configuration" / "configuration.json"
		parsed_path = source_path.parent / "parsed" / source_path.name
		if not source_path.exists():
			return parsed_path

		with source_path.open(encoding="utf-8") as source_file:
			configuration = json.load(source_file)
		parsed_configuration = self._render_configuration(configuration)
		parsed_path.parent.mkdir(parents=True, exist_ok=True)
		with parsed_path.open("w", encoding="utf-8") as parsed_file:
			json.dump(parsed_configuration, parsed_file, indent=2)
			parsed_file.write("\n")
		return parsed_path

	def _render_configuration(self, value):
		if isinstance(value, dict):
			return {key: self._render_configuration(item) for key, item in value.items()}
		if isinstance(value, list):
			return [self._render_configuration(item) for item in value]
		if isinstance(value, str):
			return re.sub(r"\{\{([A-Z][A-Z0-9_]*)\}\}", self._constant_value, value)
		return value

	@staticmethod
	def _constant_value(match):
		constant_name = match.group(1)
		if not hasattr(constants, constant_name):
			raise ValueError(f"Unknown configuration constant: {constant_name}")
		return str(getattr(constants, constant_name))

	def ensure_bucket(self) -> None:
		"""Create the configured bucket, leaving an existing owned bucket intact."""
		if not self.s3_manager.create_bucket(self.bucket_name):
			buckets = self.s3_manager.get_buckets()
			if self.bucket_name not in buckets:
				raise RuntimeError(f"Unable to create S3 bucket: {self.bucket_name}")
		if not self.s3_manager.add_cloudformation_read_policy(
			self.bucket_name, self.project_name_prefix
		):
			raise RuntimeError(f"Unable to configure CloudFormation access: {self.bucket_name}")

	def sync_directory(self, directory_name: str) -> list[str]:
		"""Sync an infra directory while preserving its S3 prefix."""
		directory = self.infra_root / directory_name
		if not directory.exists():
			self.remove_stale_objects(directory_name, [])
			return []

		synced_keys = []
		for file_path in sorted(path for path in directory.rglob("*") if path.is_file()):
			object_key = self._project_key(file_path.relative_to(self.infra_root))
			if not self.s3_manager.sync_file(str(file_path), self.bucket_name, object_key):
				raise RuntimeError(f"Unable to sync {file_path}")
			synced_keys.append(object_key)
		self.remove_stale_objects(directory_name, synced_keys)
		return synced_keys

	def remove_stale_objects(self, directory_name, synced_keys):
		"""Delete objects under a managed infra prefix that are absent locally."""
		prefix = self._project_key(Path(directory_name)) + "/"
		current_keys = set(synced_keys)
		stale_keys = [
			key
			for key in self.s3_manager.list_object_keys(self.bucket_name, prefix)
			if key not in current_keys
		]
		for object_key in stale_keys:
			if not self.s3_manager.delete_object(self.bucket_name, object_key):
				raise RuntimeError(f"Unable to delete stale Lambda archive: {object_key}")

	def package_and_sync_lambdas(self) -> list[str]:
		"""Zip each Lambda directory and sync it as ``lambdas/<name>.zip``."""
		lambdas_directory = self.infra_root / "lambdas"
		if not lambdas_directory.exists():
			self.remove_stale_objects("lambdas", [])
			return []

		synced_keys = []
		lambda_directories = sorted(path for path in lambdas_directory.iterdir() if path.is_dir())
		with TemporaryDirectory() as temporary_directory:
			for lambda_directory in lambda_directories:
				source_files = [
					path
					for path in lambda_directory.rglob("*")
					if path.is_file() and path.suffix not in {".pyc", ".pyo"}
				]
				if not source_files:
					continue

				archive_path = Path(temporary_directory) / f"{lambda_directory.name}.zip"
				with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
					for source_file in sorted(source_files):
						archive.write(
							source_file,
							source_file.relative_to(lambda_directory),
						)

				object_key = self._project_key(Path("lambdas") / archive_path.name)
				if not self.s3_manager.sync_file(str(archive_path), self.bucket_name, object_key):
					raise RuntimeError(f"Unable to sync {archive_path}")
				synced_keys.append(object_key)
		self.remove_stale_objects("lambdas", synced_keys)
		return synced_keys

	def _project_key(self, path: Path) -> str:
		"""Build an S3 key rooted at the configured project prefix."""
		return "/".join((self.project_name_prefix, *path.parts))
