import json
from pathlib import Path

from scripts import Deploy


def test_get_stacks_loads_configuration_and_preserves_filename_order(tmp_path: Path):
	stacks_directory = tmp_path / "infra" / "stacks"
	configuration_directory = stacks_directory / "configuration"
	parsed_configuration_directory = configuration_directory / "parsed"
	parsed_configuration_directory.mkdir(parents=True)
	(stacks_directory / "infra.yml").write_text("infra")
	(stacks_directory / "network.yml").write_text("network")
	(parsed_configuration_directory / "configuration.json").write_text(
		json.dumps(
			{
				"pdw-stack-infra": {
					"ProjectPartialsS3BucketName": "test-bucket",
				},
				"pdw-stack-network": {"VpcCidr": "10.0.0.0/16"},
			}
		)
	)

	stacks = Deploy(
		project_root=tmp_path,
		bucket_name="test-bucket",
		cloudformation_client=object(),
	)._Deploy__get_stacks()

	assert [stack.stack_name for stack in stacks] == [
		"pdw-stack-infra",
		"pdw-stack-network",
	]
	assert stacks[0].parameters == [
		{
			"ParameterKey": "ProjectPartialsS3BucketName",
			"ParameterValue": "test-bucket",
		}
	]
	assert stacks[1].parameters == [
		{"ParameterKey": "VpcCidr", "ParameterValue": "10.0.0.0/16"},
	]
