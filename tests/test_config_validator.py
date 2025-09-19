"""Unit tests for configuration validator."""

import pytest
import yaml
from pathlib import Path
from src.config_validator import (
    KubernetesValidator,
    DockerValidator,
    AnsibleValidator,
    ValidationError,
    extract_yaml_from_markdown,
    validate_file
)


class TestKubernetesValidator:
    """Test Kubernetes configuration validation."""

    def test_validate_yaml_syntax_valid(self):
        """Test valid YAML syntax validation."""
        valid_yaml = """
        apiVersion: batch/v1
        kind: CronJob
        metadata:
          name: test-cronjob
        spec:
          schedule: "*/5 * * * *"
        """
        result = KubernetesValidator.validate_yaml_syntax(valid_yaml)
        assert isinstance(result, dict)
        assert result['kind'] == 'CronJob'

    def test_validate_yaml_syntax_invalid(self):
        """Test invalid YAML syntax validation."""
        invalid_yaml = """
        apiVersion: batch/v1
        kind: CronJob
        metadata:
          name: test-cronjob
        spec:
          schedule: "*/5 * * * *"
        invalid_field: [unclosed bracket
        """
        with pytest.raises(ValidationError, match="Invalid YAML syntax"):
            KubernetesValidator.validate_yaml_syntax(invalid_yaml)

    def test_validate_kubernetes_resource_valid_cronjob(self):
        """Test valid CronJob resource validation."""
        config = {
            'apiVersion': 'batch/v1',
            'kind': 'CronJob',
            'metadata': {'name': 'test-cronjob'},
            'spec': {'schedule': '*/5 * * * *'}
        }
        assert KubernetesValidator.validate_kubernetes_resource(config) is True

    def test_validate_kubernetes_resource_missing_kind(self):
        """Test validation with missing kind field."""
        config = {
            'apiVersion': 'batch/v1',
            'metadata': {'name': 'test-cronjob'},
            'spec': {'schedule': '*/5 * * * *'}
        }
        with pytest.raises(ValidationError, match="Missing required field: kind"):
            KubernetesValidator.validate_kubernetes_resource(config)

    def test_validate_kubernetes_resource_unsupported_kind(self):
        """Test validation with unsupported resource kind."""
        config = {
            'apiVersion': 'v1',
            'kind': 'UnsupportedResource',
            'metadata': {'name': 'test'},
            'spec': {}
        }
        with pytest.raises(ValidationError, match="Unsupported resource kind"):
            KubernetesValidator.validate_kubernetes_resource(config)

    def test_validate_kubernetes_resource_invalid_api_version(self):
        """Test validation with invalid API version."""
        config = {
            'apiVersion': 'invalid/v1',
            'kind': 'CronJob',
            'metadata': {'name': 'test-cronjob'},
            'spec': {'schedule': '*/5 * * * *'}
        }
        with pytest.raises(ValidationError, match="Invalid apiVersion"):
            KubernetesValidator.validate_kubernetes_resource(config)

    def test_validate_kubernetes_resource_missing_metadata_name(self):
        """Test validation with missing metadata name."""
        config = {
            'apiVersion': 'batch/v1',
            'kind': 'CronJob',
            'metadata': {},
            'spec': {'schedule': '*/5 * * * *'}
        }
        with pytest.raises(ValidationError, match="Missing required field: metadata.name"):
            KubernetesValidator.validate_kubernetes_resource(config)

    @pytest.mark.parametrize("schedule,expected", [
        ("*/5 * * * *", True),
        ("0 2 * * *", True),
        ("*/12 * * * *", True),
        ("0 0 1 1 *", True),
        ("invalid", False),
        ("* * * *", False),
        ("60 * * * *", False),
    ])
    def test_validate_cron_schedule(self, schedule, expected):
        """Test cron schedule validation."""
        if expected:
            assert KubernetesValidator.validate_cron_schedule(schedule) is True
        else:
            with pytest.raises(ValidationError):
                KubernetesValidator.validate_cron_schedule(schedule)

    @pytest.mark.parametrize("image,expected", [
        ("nginx:latest", True),
        ("nginx:1.21", True),
        ("registry.com/nginx:latest", True),
        ("localhost:5000/nginx:v1.0", True),
        ("", False),
        ("invalid image name", False),
        ("NGINX:LATEST", True),  # Case insensitive
    ])
    def test_validate_image_tag(self, image, expected):
        """Test Docker image tag validation."""
        if expected:
            assert KubernetesValidator.validate_image_tag(image) is True
        else:
            with pytest.raises(ValidationError):
                KubernetesValidator.validate_image_tag(image)


class TestDockerValidator:
    """Test Docker configuration validation."""

    def test_validate_dockerfile_valid(self):
        """Test valid Dockerfile validation."""
        dockerfile_content = """
        FROM nginx:latest
        COPY . /app
        WORKDIR /app
        RUN npm install
        EXPOSE 80
        CMD ["nginx", "-g", "daemon off;"]
        """
        assert DockerValidator.validate_dockerfile(dockerfile_content) is True

    def test_validate_dockerfile_no_from(self):
        """Test Dockerfile without FROM instruction."""
        dockerfile_content = """
        COPY . /app
        WORKDIR /app
        """
        with pytest.raises(ValidationError, match="Dockerfile must start with FROM"):
            DockerValidator.validate_dockerfile(dockerfile_content)

    def test_validate_dockerfile_empty(self):
        """Test empty Dockerfile validation."""
        with pytest.raises(ValidationError, match="Dockerfile cannot be empty"):
            DockerValidator.validate_dockerfile("")


class TestAnsibleValidator:
    """Test Ansible configuration validation."""

    def test_validate_playbook_valid_list(self):
        """Test valid Ansible playbook as list."""
        playbook = [
            {
                'hosts': 'all',
                'tasks': [
                    {'name': 'Install nginx', 'package': {'name': 'nginx', 'state': 'present'}}
                ]
            }
        ]
        assert AnsibleValidator.validate_playbook(playbook) is True

    def test_validate_playbook_valid_dict(self):
        """Test valid Ansible playbook as dictionary."""
        playbook = {
            'hosts': 'all',
            'tasks': [
                {'name': 'Install nginx', 'package': {'name': 'nginx', 'state': 'present'}}
            ]
        }
        assert AnsibleValidator.validate_playbook(playbook) is True

    def test_validate_playbook_missing_hosts(self):
        """Test Ansible playbook missing hosts field."""
        playbook = [
            {
                'tasks': [
                    {'name': 'Install nginx', 'package': {'name': 'nginx', 'state': 'present'}}
                ]
            }
        ]
        with pytest.raises(ValidationError, match="Each play must have 'hosts' field"):
            AnsibleValidator.validate_playbook(playbook)

    def test_validate_playbook_invalid_format(self):
        """Test invalid Ansible playbook format."""
        with pytest.raises(ValidationError, match="Playbook must be a list or dictionary"):
            AnsibleValidator.validate_playbook("invalid")


class TestExtractYamlFromMarkdown:
    """Test YAML extraction from markdown."""

    def test_extract_single_yaml_block(self):
        """Test extracting single YAML block from markdown."""
        markdown_content = """
        # Test Document

        Here's a YAML configuration:

        ```yaml
        apiVersion: v1
        kind: Service
        metadata:
          name: test-service
        ```

        That's it!
        """
        yaml_blocks = extract_yaml_from_markdown(markdown_content)
        assert len(yaml_blocks) == 1
        assert 'apiVersion: v1' in yaml_blocks[0]
        assert 'kind: Service' in yaml_blocks[0]

    def test_extract_multiple_yaml_blocks(self):
        """Test extracting multiple YAML blocks from markdown."""
        markdown_content = """
        # Test Document

        First config:
        ```yaml
        apiVersion: v1
        kind: Service
        ```

        Second config:
        ```yaml
        apiVersion: batch/v1
        kind: CronJob
        ```
        """
        yaml_blocks = extract_yaml_from_markdown(markdown_content)
        assert len(yaml_blocks) == 2

    def test_extract_no_yaml_blocks(self):
        """Test extracting from markdown with no YAML blocks."""
        markdown_content = """
        # Test Document

        This is just regular text with no YAML.
        """
        yaml_blocks = extract_yaml_from_markdown(markdown_content)
        assert len(yaml_blocks) == 0

    def test_extract_empty_yaml_block(self):
        """Test extracting empty YAML block."""
        markdown_content = """
        # Test Document

        ```yaml
        ```
        """
        yaml_blocks = extract_yaml_from_markdown(markdown_content)
        # Empty blocks are filtered out by is_likely_yaml
        assert len(yaml_blocks) == 0


class TestValidateFile:
    """Test file validation functionality."""

    def test_validate_file_with_valid_kubernetes_yaml(self, tmp_path):
        """Test validating file with valid Kubernetes YAML."""
        # Create temporary markdown file with valid YAML
        markdown_content = """
        # CronJob Example

        ```yaml
        apiVersion: batch/v1
        kind: CronJob
        metadata:
          name: test-cronjob
        spec:
          schedule: "*/5 * * * *"
          jobTemplate:
            spec:
              template:
                spec:
                  containers:
                  - name: test-container
                    image: nginx:latest
                    args: ["echo", "Hello World"]
                  restartPolicy: OnFailure
        ```
        """

        test_file = tmp_path / "test.md"
        test_file.write_text(markdown_content)

        result = validate_file(test_file)
        assert result['valid'] is True
        assert result['yaml_blocks'] == 1
        assert len(result['errors']) == 0

    def test_validate_file_with_invalid_yaml(self, tmp_path):
        """Test validating file with invalid YAML."""
        markdown_content = """
        # Invalid YAML Example

        ```yaml
        apiVersion: batch/v1
        kind: CronJob
        metadata:
          name: test-cronjob
        spec:
          schedule: "invalid schedule"
        ```
        """

        test_file = tmp_path / "test.md"
        test_file.write_text(markdown_content)

        result = validate_file(test_file)
        assert result['valid'] is False
        assert result['yaml_blocks'] == 1
        assert len(result['errors']) > 0

    def test_validate_file_nonexistent(self):
        """Test validating nonexistent file."""
        result = validate_file(Path("nonexistent.md"))
        assert result['valid'] is False
        assert len(result['errors']) > 0


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_input_validation(self):
        """Test validation with None inputs."""
        with pytest.raises(ValidationError):
            KubernetesValidator.validate_kubernetes_resource(None)

    def test_empty_string_validation(self):
        """Test validation with empty strings."""
        with pytest.raises(ValidationError):
            KubernetesValidator.validate_yaml_syntax("")

    def test_very_large_yaml_validation(self):
        """Test validation with very large YAML content."""
        # Create a large but valid YAML
        large_config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': 'large-config'},
            'data': {f'key_{i}': f'value_{i}' for i in range(1000)}
        }

        # This should not raise an error
        assert KubernetesValidator.validate_kubernetes_resource(large_config) is True

    def test_unicode_content_validation(self):
        """Test validation with unicode content."""
        config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': 'unicode-config'},
            'data': {'message': 'Hello 世界 🌍'}
        }
        assert KubernetesValidator.validate_kubernetes_resource(config) is True

    def test_deeply_nested_yaml_validation(self):
        """Test validation with deeply nested YAML."""
        config = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {'name': 'nested-deployment'},
            'spec': {
                'replicas': 1,
                'selector': {'matchLabels': {'app': 'test'}},
                'template': {
                    'metadata': {'labels': {'app': 'test'}},
                    'spec': {
                        'containers': [{
                            'name': 'app',
                            'image': 'nginx:latest',
                            'env': [
                                {'name': 'VAR1', 'value': 'value1'},
                                {'name': 'VAR2', 'valueFrom': {'secretKeyRef': {'name': 'secret', 'key': 'key'}}}
                            ]
                        }]
                    }
                }
            }
        }
        assert KubernetesValidator.validate_kubernetes_resource(config) is True