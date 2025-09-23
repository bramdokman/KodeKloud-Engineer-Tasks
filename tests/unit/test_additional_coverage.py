"""Additional unit tests to improve code coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import yaml
import json

from src.kodekloud_tasks.task_parser import TaskParser
from src.kodekloud_tasks.utils import (
    load_markdown_file,
    extract_code_blocks,
    validate_yaml_syntax,
    validate_json_syntax,
    find_all_files,
    extract_task_metadata,
    validate_kubernetes_resource,
    normalize_whitespace,
    calculate_similarity,
)


class TestUtilsCoverage:
    """Additional tests for utils module to improve coverage."""

    @pytest.mark.unit
    def test_load_markdown_file_io_error(self, tmp_path):
        """Test IOError handling in load_markdown_file."""
        filepath = tmp_path / "test.md"
        filepath.write_text("content")
        filepath.chmod(0o000)  # Remove read permissions

        # Some systems might still allow reading, so we mock the open
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(IOError) as exc:
                load_markdown_file(filepath)
            assert "Error reading markdown file" in str(exc.value)

    @pytest.mark.unit
    def test_extract_task_metadata_git_category(self):
        """Test Git category detection in metadata extraction."""
        content = """
        # Git Workflow Task

        Configure Git hooks for the repository.
        """
        metadata = extract_task_metadata(content)
        assert metadata["category"] == "Git"

    @pytest.mark.unit
    def test_extract_task_metadata_no_category(self):
        """Test metadata extraction with no category match."""
        content = """
        # Generic Task

        This is a general task without specific technology.
        """
        metadata = extract_task_metadata(content)
        assert metadata["category"] is None

    @pytest.mark.unit
    def test_validate_kubernetes_resource_invalid_metadata(self):
        """Test K8s validation with non-dict metadata."""
        yaml_content = """
apiVersion: v1
kind: ConfigMap
metadata: "invalid_metadata_string"
"""
        valid, error = validate_kubernetes_resource(yaml_content)
        assert not valid
        assert "Invalid metadata format" in error

    @pytest.mark.unit
    def test_validate_kubernetes_resource_exception(self):
        """Test K8s validation with malformed YAML."""
        yaml_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test
  invalid: [unclosed bracket
"""
        valid, error = validate_kubernetes_resource(yaml_content)
        assert not valid
        assert error is not None

    @pytest.mark.unit
    def test_normalize_whitespace_multiple_spaces(self):
        """Test normalization of multiple spaces and tabs."""
        text = "  This   has\t\tmultiple    spaces\n\nand newlines  "
        result = normalize_whitespace(text)
        assert result == "This has multiple spaces and newlines"

    @pytest.mark.unit
    def test_calculate_similarity_whitespace_only(self):
        """Test similarity calculation with whitespace-only strings."""
        assert calculate_similarity("   ", "  \t\n") == 1.0
        assert calculate_similarity("   ", "word") == 0.0


class TestTaskParserCoverage:
    """Additional tests for TaskParser to improve coverage."""

    @pytest.fixture
    def parser(self):
        """Create a TaskParser instance."""
        return TaskParser()

    @pytest.mark.unit
    def test_extract_configurations_docker_in_yaml(self, parser):
        """Test Docker configuration detection in YAML."""
        content = """
        ```yaml
        version: '3'
        services:
          docker-app:
            image: nginx
        ```
        """
        configs = parser._extract_configurations(content)
        assert len(configs["docker"]) == 1
        assert "docker-app" in configs["docker"][0]

    @pytest.mark.unit
    def test_extract_configurations_puppet_class(self, parser):
        """Test Puppet configuration detection."""
        content = """
        ```yaml
        class { 'apache':
          ensure => installed
        }
        ```
        """
        configs = parser._extract_configurations(content)
        assert len(configs["puppet"]) == 1

    @pytest.mark.unit
    def test_extract_requirements_mixed_format(self, parser):
        """Test requirements extraction with mixed formats."""
        content = """
        ## Requirements
        - First requirement with bullet
        * Second requirement with asterisk
        • Third requirement with bullet point

        1. Numbered requirement one
        2. Numbered requirement two

        Additional text that should not be included.
        """
        requirements = parser._extract_requirements(content)
        assert len(requirements) == 5
        assert "First requirement with bullet" in requirements
        assert "Second requirement with asterisk" in requirements
        assert "Numbered requirement one" in requirements

    @pytest.mark.unit
    def test_estimate_difficulty_with_keywords(self, parser):
        """Test difficulty estimation with complex keywords."""
        content = """
        # Task

        Configure multi-node cluster with RBAC and high availability.
        Performance optimization and security hardening required.
        Troubleshoot complex networking issues.
        """
        difficulty = parser._estimate_difficulty(content)
        # Should detect multiple complex keywords
        assert difficulty in ["intermediate", "advanced"]

    @pytest.mark.unit
    def test_estimate_difficulty_edge_cases(self, parser):
        """Test difficulty estimation edge cases."""
        # Very short content
        content1 = "# Short"
        assert parser._estimate_difficulty(content1) == "beginner"

        # Medium length but simple
        content2 = "# Task\n" + ("Simple text. " * 100)
        assert parser._estimate_difficulty(content2) == "beginner"

        # Long content with many code blocks
        content3 = "# Task\n" + ("x" * 6000)
        for i in range(7):
            content3 += f"\n```yaml\nconfig{i}\n```"
        assert parser._estimate_difficulty(content3) == "advanced"

    @pytest.mark.unit
    def test_get_statistics_division_by_zero(self, parser):
        """Test statistics calculation with edge cases."""
        parser.parsed_tasks = []
        stats = parser.get_statistics()
        assert stats == {}

        # Add task without commands
        parser.parsed_tasks = [{
            "metadata": {"category": "Test"},
            "difficulty": "unknown",  # Unknown difficulty
            "technologies": [],
            "content": {"commands": []},
            "solution": None
        }]
        stats = parser.get_statistics()
        assert stats["avg_commands_per_task"] == 0
        assert stats["tasks_with_solutions"] == 0

    @pytest.mark.unit
    def test_parse_directory_with_find_all_files_import(self, parser, tmp_path):
        """Test parse_directory with actual file finding."""
        # Create test structure
        k8s_dir = tmp_path / "kubernetes"
        k8s_dir.mkdir()
        docker_dir = tmp_path / "docker"
        docker_dir.mkdir()

        (k8s_dir / "task1.md").write_text("# K8s Task")
        (docker_dir / "task2.md").write_text("# Docker Task")
        (tmp_path / "root_task.md").write_text("# Root Task")

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file') as mock_load:
            mock_load.side_effect = ["# K8s Task", "# Docker Task", "# Root Task"]
            tasks = parser.parse_directory(tmp_path)

        assert len(tasks) == 3


class TestEdgeCaseCoverage:
    """Additional edge case tests for comprehensive coverage."""

    @pytest.mark.unit
    def test_validate_yaml_syntax_complex_error(self):
        """Test YAML validation with complex error."""
        yaml_content = """
        key1: value1
        key2:
          - item1
          - item2: {nested: [unclosed}
        """
        valid, error = validate_yaml_syntax(yaml_content)
        assert not valid
        assert error is not None

    @pytest.mark.unit
    def test_validate_json_syntax_nested_error(self):
        """Test JSON validation with nested structure error."""
        json_content = '{"key": {"nested": [1, 2, "unclosed string}'
        valid, error = validate_json_syntax(json_content)
        assert not valid
        assert error is not None

    @pytest.mark.unit
    def test_find_all_files_recursive(self, tmp_path):
        """Test recursive file finding in nested directories."""
        # Create nested structure
        sub1 = tmp_path / "sub1"
        sub2 = tmp_path / "sub1" / "sub2"
        sub3 = tmp_path / "sub1" / "sub2" / "sub3"

        sub1.mkdir()
        sub2.mkdir()
        sub3.mkdir()

        (tmp_path / "root.md").write_text("root")
        (sub1 / "level1.md").write_text("level1")
        (sub2 / "level2.md").write_text("level2")
        (sub3 / "level3.md").write_text("level3")
        (sub1 / "not_md.txt").write_text("ignored")

        files = find_all_files(tmp_path, "*.md")
        assert len(files) == 4

        # Check all levels are found
        file_names = [f.name for f in files]
        assert "root.md" in file_names
        assert "level1.md" in file_names
        assert "level2.md" in file_names
        assert "level3.md" in file_names

    @pytest.mark.unit
    def test_extract_code_blocks_no_language(self):
        """Test extraction of code blocks without language specification."""
        content = """
        ```
        code without language
        ```

        ```python
        python code
        ```
        """
        # Get all blocks
        all_blocks = extract_code_blocks(content)
        assert len(all_blocks) == 2
        assert "code without language" in all_blocks[0]
        assert "python code" in all_blocks[1]

        # Filter by language
        python_blocks = extract_code_blocks(content, "python")
        assert len(python_blocks) == 1
        assert "python code" in python_blocks[0]


class TestIntegrationCoverage:
    """Integration tests for better coverage."""

    @pytest.mark.unit
    def test_task_parser_full_workflow(self, tmp_path):
        """Test complete TaskParser workflow."""
        parser = TaskParser()

        # Create a comprehensive task file
        content = """# Comprehensive Kubernetes Task

## Prerequisites
- Kubernetes cluster
- kubectl configured

## Requirements
- Deploy nginx deployment
- Configure service
- Set up ingress

## Solution
First, create the namespace:

```bash
kubectl create namespace production
kubectl label namespace production env=prod
```

Then deploy the application:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
```

Configure ansible for automation:

```yml
- name: Deploy to Kubernetes
  hosts: localhost
  tasks:
    - name: Apply deployment
      k8s:
        src: deployment.yaml
```

## Verification
```bash
kubectl get pods -n production
kubectl get svc -n production
```

This is an advanced task with multi-node cluster configuration and high availability setup required.
"""
        task_file = tmp_path / "comprehensive.md"
        task_file.write_text(content)

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file', return_value=content):
            result = parser.parse_task(task_file)

        # Verify comprehensive parsing
        assert result["metadata"]["title"] == "Comprehensive Kubernetes Task"
        assert result["metadata"]["has_solution"] is True
        assert result["metadata"]["has_commands"] is True
        assert result["metadata"]["has_yaml"] is True
        assert result["metadata"]["category"] == "Kubernetes"

        assert len(result["requirements"]) == 3
        assert result["solution"] is not None
        assert "First, create the namespace" in result["solution"]

        assert len(result["content"]["commands"]) > 0
        assert any("kubectl" in cmd for cmd in result["content"]["commands"])

        assert "yaml" in result["content"]["code_blocks"]
        assert "bash" in result["content"]["code_blocks"]
        assert "yml" in result["content"]["code_blocks"]

        assert len(result["content"]["configurations"]["kubernetes"]) > 0
        assert len(result["content"]["configurations"]["ansible"]) > 0

        assert result["difficulty"] in ["intermediate", "advanced"]
        assert "Kubernetes" in result["technologies"]
        assert "Ansible" in result["technologies"]

        # Test statistics
        stats = parser.get_statistics()
        assert stats["total_tasks"] == 1
        assert stats["tasks_with_solutions"] == 1