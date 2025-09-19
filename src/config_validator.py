"""Configuration validation utilities for DevOps tasks."""

import yaml
import re
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class ValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class KubernetesValidator:
    """Validates Kubernetes YAML configurations."""

    REQUIRED_FIELDS = {
        'CronJob': ['apiVersion', 'kind', 'metadata', 'spec'],
        'Deployment': ['apiVersion', 'kind', 'metadata', 'spec'],
        'Service': ['apiVersion', 'kind', 'metadata', 'spec'],
        'ConfigMap': ['apiVersion', 'kind', 'metadata', 'data'],
        'Secret': ['apiVersion', 'kind', 'metadata', 'data'],
        'PersistentVolume': ['apiVersion', 'kind', 'metadata', 'spec'],
        'PersistentVolumeClaim': ['apiVersion', 'kind', 'metadata', 'spec'],
    }

    API_VERSIONS = {
        'CronJob': ['batch/v1', 'batch/v1beta1'],
        'Deployment': ['apps/v1'],
        'Service': ['v1'],
        'ConfigMap': ['v1'],
        'Secret': ['v1'],
        'PersistentVolume': ['v1'],
        'PersistentVolumeClaim': ['v1'],
    }

    @staticmethod
    def validate_yaml_syntax(content: str) -> Dict[str, Any]:
        """Validate YAML syntax and return parsed content."""
        if not content or not content.strip():
            raise ValidationError("YAML content cannot be empty")

        try:
            # Handle multi-document YAML by loading all documents and returning the first valid one
            documents = list(yaml.safe_load_all(content))
            if not documents:
                raise ValidationError("No valid YAML documents found")

            # Return the first non-None document
            for doc in documents:
                if doc is not None:
                    return doc

            raise ValidationError("No valid YAML content found")
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML syntax: {e}")

    @classmethod
    def validate_kubernetes_resource(cls, config: Dict[str, Any]) -> bool:
        """Validate Kubernetes resource structure."""
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")

        kind = config.get('kind')
        if not kind:
            raise ValidationError("Missing required field: kind")

        if kind not in cls.REQUIRED_FIELDS:
            raise ValidationError(f"Unsupported resource kind: {kind}")

        # Check required fields
        required = cls.REQUIRED_FIELDS[kind]
        for field in required:
            if field not in config:
                raise ValidationError(f"Missing required field for {kind}: {field}")

        # Validate API version
        api_version = config.get('apiVersion')
        valid_versions = cls.API_VERSIONS.get(kind, [])
        if api_version not in valid_versions:
            raise ValidationError(
                f"Invalid apiVersion for {kind}: {api_version}. "
                f"Expected one of: {valid_versions}"
            )

        # Validate metadata
        metadata = config.get('metadata', {})
        if not metadata.get('name'):
            raise ValidationError("Missing required field: metadata.name")

        return True

    @staticmethod
    def validate_cron_schedule(schedule: str) -> bool:
        """Validate cron schedule format."""
        if not schedule or not schedule.strip():
            raise ValidationError("Cron schedule cannot be empty")

        schedule = schedule.strip()
        parts = schedule.split()

        if len(parts) != 5:
            raise ValidationError(f"Invalid cron schedule format: {schedule}. Expected 5 fields, got {len(parts)}")

        # Validate each field
        minute, hour, day, month, dow = parts

        # Minute validation (0-59)
        if not KubernetesValidator._validate_cron_field(minute, 0, 59):
            raise ValidationError(f"Invalid minute field: {minute}")

        # Hour validation (0-23)
        if not KubernetesValidator._validate_cron_field(hour, 0, 23):
            raise ValidationError(f"Invalid hour field: {hour}")

        # Day validation (1-31)
        if not KubernetesValidator._validate_cron_field(day, 1, 31):
            raise ValidationError(f"Invalid day field: {day}")

        # Month validation (1-12)
        if not KubernetesValidator._validate_cron_field(month, 1, 12):
            raise ValidationError(f"Invalid month field: {month}")

        # Day of week validation (0-7, 7 = Sunday)
        if not KubernetesValidator._validate_cron_field(dow, 0, 7):
            raise ValidationError(f"Invalid day of week field: {dow}")

        return True

    @staticmethod
    def _validate_cron_field(field: str, min_val: int, max_val: int) -> bool:
        """Validate individual cron field."""
        if field == '*':
            return True

        # Handle step values (*/n)
        if field.startswith('*/'):
            try:
                step = int(field[2:])
                return step > 0
            except ValueError:
                return False

        # Handle ranges (n-m)
        if '-' in field:
            try:
                start, end = field.split('-', 1)
                start_val = int(start)
                end_val = int(end)
                return min_val <= start_val <= end_val <= max_val
            except ValueError:
                return False

        # Handle lists (n,m,o)
        if ',' in field:
            try:
                values = [int(v.strip()) for v in field.split(',')]
                return all(min_val <= v <= max_val for v in values)
            except ValueError:
                return False

        # Handle single values
        try:
            value = int(field)
            return min_val <= value <= max_val
        except ValueError:
            return False

    @staticmethod
    def validate_image_tag(image: str) -> bool:
        """Validate Docker image tag format."""
        if not image:
            raise ValidationError("Image cannot be empty")

        # More flexible image validation that handles registries and ports
        # Registry can be hostname:port, image name can have multiple segments separated by /
        image_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*(?::[0-9]+)?/)?[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9._-]+)?$'
        if not re.match(image_pattern, image, re.IGNORECASE):
            raise ValidationError(f"Invalid image format: {image}")

        return True


class DockerValidator:
    """Validates Docker configurations."""

    @staticmethod
    def validate_dockerfile(content: str) -> bool:
        """Validate Dockerfile syntax and best practices."""
        if not content or not content.strip():
            raise ValidationError("Dockerfile cannot be empty")

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        if not lines:
            raise ValidationError("Dockerfile cannot be empty")

        first_line = lines[0].strip()
        if not first_line.upper().startswith('FROM'):
            raise ValidationError("Dockerfile must start with FROM instruction")

        return True


class AnsibleValidator:
    """Validates Ansible playbook configurations."""

    @staticmethod
    def validate_playbook(config: Dict[str, Any]) -> bool:
        """Validate Ansible playbook structure."""
        if not isinstance(config, (list, dict)):
            raise ValidationError("Playbook must be a list or dictionary")

        if isinstance(config, list):
            for play in config:
                if not isinstance(play, dict):
                    raise ValidationError("Each play must be a dictionary")
                if 'hosts' not in play:
                    raise ValidationError("Each play must have 'hosts' field")

        return True


def extract_yaml_from_markdown(content: str) -> List[str]:
    """Extract YAML code blocks from markdown content."""
    yaml_blocks = []
    lines = content.split('\n')
    in_yaml_block = False
    current_block = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line == '```yaml' or (stripped_line == '```' and not in_yaml_block):
            # Start of code block (either explicit yaml or generic)
            in_yaml_block = True
            current_block = []
        elif stripped_line == '```' and in_yaml_block:
            # End of code block - check if it contains YAML
            block_content = '\n'.join(current_block)
            if is_likely_yaml(block_content):
                yaml_blocks.append(block_content)
            current_block = []
            in_yaml_block = False
        elif in_yaml_block:
            current_block.append(line)

    return yaml_blocks


def is_likely_yaml(content: str) -> bool:
    """Check if content is likely to be YAML based on common patterns."""
    if not content.strip():
        return False

    # Common YAML patterns for Kubernetes
    yaml_indicators = [
        'apiVersion:', 'kind:', 'metadata:', 'spec:',
        'name:', 'namespace:', 'labels:', 'annotations:',
        'containers:', 'image:', 'ports:', 'env:'
    ]

    content_lower = content.lower()
    for indicator in yaml_indicators:
        if indicator.lower() in content_lower:
            return True

    # Check for basic YAML structure (key: value pairs)
    lines = content.strip().split('\n')
    yaml_like_lines = 0
    for line in lines:
        stripped = line.strip()
        if ':' in stripped and not stripped.startswith('#'):
            yaml_like_lines += 1

    # If more than 30% of non-empty lines look like YAML, consider it YAML
    non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    if non_empty_lines and yaml_like_lines / len(non_empty_lines) > 0.3:
        return True

    return False


def validate_file(file_path: Path) -> Dict[str, Any]:
    """Validate a configuration file and return results."""
    results = {
        'file': str(file_path),
        'valid': False,
        'errors': [],
        'warnings': [],
        'yaml_blocks': 0
    }

    try:
        content = file_path.read_text(encoding='utf-8')

        if file_path.suffix == '.md':
            # Extract YAML from markdown
            yaml_blocks = extract_yaml_from_markdown(content)
            results['yaml_blocks'] = len(yaml_blocks)

            for i, yaml_content in enumerate(yaml_blocks):
                try:
                    # Handle multi-document YAML blocks
                    documents = list(yaml.safe_load_all(yaml_content))
                    for doc_idx, config in enumerate(documents):
                        if config and isinstance(config, dict):
                            KubernetesValidator.validate_kubernetes_resource(config)

                            # Additional validations based on resource type
                            if config.get('kind') == 'CronJob':
                                schedule = config.get('spec', {}).get('schedule', '')
                                if schedule:
                                    KubernetesValidator.validate_cron_schedule(schedule)

                            # Validate container images
                            spec = config.get('spec', {})
                            if 'jobTemplate' in spec:
                                containers = spec.get('jobTemplate', {}).get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                            elif 'template' in spec:
                                containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                            else:
                                containers = spec.get('containers', [])

                            for container in containers:
                                image = container.get('image', '')
                                if image:
                                    KubernetesValidator.validate_image_tag(image)

                except ValidationError as e:
                    results['errors'].append(f"YAML block {i+1}: {e}")
                except Exception as e:
                    results['errors'].append(f"YAML block {i+1}: Unexpected error: {e}")

        elif file_path.suffix in ['.yaml', '.yml']:
            # Direct YAML file
            config = KubernetesValidator.validate_yaml_syntax(content)
            if config:
                KubernetesValidator.validate_kubernetes_resource(config)
                results['yaml_blocks'] = 1

        results['valid'] = len(results['errors']) == 0

    except Exception as e:
        results['errors'].append(f"File processing error: {e}")

    return results