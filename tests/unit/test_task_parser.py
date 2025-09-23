"""Unit tests for TaskParser module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.kodekloud_tasks.task_parser import TaskParser


class TestTaskParser:
    """Test TaskParser class."""

    @pytest.fixture
    def parser(self):
        """Create a TaskParser instance."""
        return TaskParser()

    @pytest.fixture
    def sample_markdown_content(self):
        """Sample markdown content for testing."""
        return """# Deploy Kubernetes Application

## Requirements
- Deploy a multi-tier application
- Configure persistent storage
- Set up service discovery

## Solution
Deploy the following resources in order:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app-namespace
```

```bash
kubectl apply -f deployment.yaml
kubectl get pods -n app-namespace
```

```json
{
  "config": {
    "replicas": 3
  }
}
```

## Verification
Check the deployment status.
"""

    @pytest.fixture
    def complex_markdown_content(self):
        """Complex markdown content for advanced testing."""
        return """# Advanced Kubernetes Cluster Setup

## Prerequisites
- Multi-node cluster
- High availability configuration
- RBAC enabled
- Security policies

## Implementation

Deploy complex application with multiple components:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: complex-app
spec:
  replicas: 5
```

```bash
# Complex commands
kubectl create ns production
kubectl apply -f app.yaml
git clone https://github.com/example/repo.git
ansible-playbook -i inventory deploy.yml
puppet apply manifest.pp
docker build -t app:latest .
```

```yml
- name: Ansible playbook
  hosts: all
  tasks:
    - name: Deploy app
      docker_container:
        name: app
```

```puppet
class { 'nginx':
  ensure => present,
}
```

Performance optimization and troubleshooting required.
"""

    @pytest.mark.unit
    def test_parser_initialization(self, parser):
        """Test TaskParser initialization."""
        assert parser.parsed_tasks == []
        assert isinstance(parser.parsed_tasks, list)

    @pytest.mark.unit
    def test_parse_task_basic(self, parser, tmp_path, sample_markdown_content):
        """Test basic task parsing."""
        task_file = tmp_path / "task.md"
        task_file.write_text(sample_markdown_content)

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file') as mock_load:
            mock_load.return_value = sample_markdown_content
            result = parser.parse_task(task_file)

        assert result["filepath"] == str(task_file)
        assert result["metadata"]["title"] == "Deploy Kubernetes Application"
        assert result["metadata"]["has_solution"] is True
        assert result["metadata"]["has_commands"] is True
        assert result["metadata"]["has_yaml"] is True
        assert result["difficulty"] == "beginner"
        assert "Kubernetes" in result["technologies"]
        assert len(parser.parsed_tasks) == 1

    @pytest.mark.unit
    def test_parse_task_complex(self, parser, tmp_path, complex_markdown_content):
        """Test complex task parsing."""
        task_file = tmp_path / "complex_task.md"
        task_file.write_text(complex_markdown_content)

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file') as mock_load:
            mock_load.return_value = complex_markdown_content
            result = parser.parse_task(task_file)

        assert result["difficulty"] == "advanced"
        assert len(result["technologies"]) > 3
        assert "Kubernetes" in result["technologies"]
        assert "Docker" in result["technologies"]
        assert "Ansible" in result["technologies"]
        assert "Puppet" in result["technologies"]
        assert "Git" in result["technologies"]

    @pytest.mark.unit
    def test_extract_sections(self, parser, sample_markdown_content):
        """Test section extraction."""
        sections = parser._extract_sections(sample_markdown_content)

        assert "title" in sections
        assert sections["title"] == "Deploy Kubernetes Application"
        assert "requirements" in sections
        assert "solution" in sections
        assert "verification" in sections
        assert "Configure persistent storage" in sections["requirements"]

    @pytest.mark.unit
    def test_extract_all_code_blocks(self, parser, sample_markdown_content):
        """Test code block extraction."""
        code_blocks = parser._extract_all_code_blocks(sample_markdown_content)

        assert "yaml" in code_blocks
        assert "bash" in code_blocks
        assert "json" in code_blocks
        assert len(code_blocks["yaml"]) == 1
        assert len(code_blocks["bash"]) == 1
        assert len(code_blocks["json"]) == 1
        assert "Namespace" in code_blocks["yaml"][0]
        assert "kubectl" in code_blocks["bash"][0]

    @pytest.mark.unit
    def test_extract_commands(self, parser, complex_markdown_content):
        """Test command extraction."""
        commands = parser._extract_commands(complex_markdown_content)

        assert len(commands) > 0
        assert any("kubectl" in cmd for cmd in commands)
        assert any("git" in cmd for cmd in commands)
        assert any("ansible" in cmd for cmd in commands)
        assert any("puppet" in cmd for cmd in commands)
        assert any("docker" in cmd for cmd in commands)
        # Comments should be excluded
        assert not any(cmd.startswith("#") for cmd in commands)

    @pytest.mark.unit
    def test_extract_commands_with_inline_code(self, parser):
        """Test extraction of inline commands."""
        content = """
        Run `kubectl get pods` to check status.
        Execute `docker ps` to list containers.
        Use `git status` to check repository.
        The variable `result` should be checked.
        """
        commands = parser._extract_commands(content)

        assert "kubectl get pods" in commands
        assert "docker ps" in commands
        assert "git status" in commands
        # Non-command inline code should not be included
        assert "result" not in commands

    @pytest.mark.unit
    def test_extract_configurations(self, parser, complex_markdown_content):
        """Test configuration extraction."""
        configs = parser._extract_configurations(complex_markdown_content)

        assert len(configs["kubernetes"]) > 0
        assert len(configs["ansible"]) > 0
        assert len(configs["puppet"]) > 0
        assert any("Deployment" in cfg for cfg in configs["kubernetes"])
        assert any("docker_container" in cfg for cfg in configs["ansible"])
        assert any("nginx" in cfg for cfg in configs["puppet"])

    @pytest.mark.unit
    def test_extract_requirements(self, parser, sample_markdown_content):
        """Test requirements extraction."""
        requirements = parser._extract_requirements(sample_markdown_content)

        assert len(requirements) == 3
        assert "Deploy a multi-tier application" in requirements
        assert "Configure persistent storage" in requirements
        assert "Set up service discovery" in requirements

    @pytest.mark.unit
    def test_extract_requirements_numbered(self, parser):
        """Test extraction of numbered requirements."""
        content = """
        ## Requirements
        1. Install Docker
        2. Configure Kubernetes
        3. Deploy application
        """
        requirements = parser._extract_requirements(content)

        assert len(requirements) == 3
        assert "Install Docker" in requirements
        assert "Configure Kubernetes" in requirements
        assert "Deploy application" in requirements

    @pytest.mark.unit
    def test_extract_solution(self, parser, sample_markdown_content):
        """Test solution extraction."""
        solution = parser._extract_solution(sample_markdown_content)

        assert solution is not None
        assert "Deploy the following resources" in solution
        assert "yaml" in solution
        assert "bash" in solution

    @pytest.mark.unit
    def test_extract_solution_missing(self, parser):
        """Test handling of missing solution section."""
        content = """
        # Task without solution

        ## Requirements
        - Do something
        """
        solution = parser._extract_solution(content)

        assert solution is None

    @pytest.mark.unit
    def test_estimate_difficulty_beginner(self, parser):
        """Test difficulty estimation for beginner tasks."""
        content = """
        # Simple Task

        Deploy a basic pod:
        ```yaml
        apiVersion: v1
        kind: Pod
        ```
        """
        difficulty = parser._estimate_difficulty(content)

        assert difficulty == "beginner"

    @pytest.mark.unit
    def test_estimate_difficulty_intermediate(self, parser):
        """Test difficulty estimation for intermediate tasks."""
        content = """
        # Intermediate Task

        """ + "x" * 2500 + """

        ```yaml
        config1
        ```

        ```yaml
        config2
        ```

        ```yaml
        config3
        ```
        """
        difficulty = parser._estimate_difficulty(content)

        assert difficulty == "intermediate"

    @pytest.mark.unit
    def test_estimate_difficulty_advanced(self, parser):
        """Test difficulty estimation for advanced tasks."""
        content = """
        # Advanced Task

        """ + "x" * 6000 + """

        Configure multi-node cluster with high availability.
        Implement security RBAC and performance optimization.
        Troubleshoot complex issues.

        ```yaml
        config1
        ```
        ```yaml
        config2
        ```
        ```yaml
        config3
        ```
        ```yaml
        config4
        ```
        ```yaml
        config5
        ```
        ```yaml
        config6
        ```
        """
        difficulty = parser._estimate_difficulty(content)

        assert difficulty == "advanced"

    @pytest.mark.unit
    def test_extract_technologies(self, parser):
        """Test technology extraction."""
        content = """
        Deploy Kubernetes cluster with Docker containers.
        Configure Jenkins CI/CD pipeline.
        Set up Nginx as reverse proxy with Redis cache.
        Use Terraform for AWS infrastructure.
        Monitor with Prometheus and Grafana.
        Store data in PostgreSQL and MongoDB.
        """
        technologies = parser._extract_technologies(content)

        assert "Kubernetes" in technologies
        assert "Docker" in technologies
        assert "Jenkins" in technologies
        assert "Nginx" in technologies
        assert "Redis" in technologies
        assert "Terraform" in technologies
        assert "AWS" in technologies
        assert "Prometheus" in technologies
        assert "Grafana" in technologies
        assert "PostgreSQL" in technologies
        assert "MongoDB" in technologies

    @pytest.mark.unit
    def test_parse_directory(self, parser, tmp_path, sample_markdown_content):
        """Test parsing all tasks in a directory."""
        # Create multiple task files
        for i in range(3):
            task_file = tmp_path / f"task{i}.md"
            task_file.write_text(sample_markdown_content)

        # Create a hidden file that should be ignored
        hidden_file = tmp_path / ".hidden.md"
        hidden_file.write_text("Hidden content")

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file') as mock_load:
            mock_load.return_value = sample_markdown_content
            tasks = parser.parse_directory(tmp_path)

        assert len(tasks) == 3
        assert all(task["metadata"]["title"] == "Deploy Kubernetes Application" for task in tasks)

    @pytest.mark.unit
    def test_parse_directory_empty(self, parser, tmp_path):
        """Test parsing empty directory."""
        tasks = parser.parse_directory(tmp_path)

        assert tasks == []

    @pytest.mark.unit
    def test_parse_directory_nested(self, parser, tmp_path, sample_markdown_content):
        """Test parsing nested directory structure."""
        # Create nested structure
        subdir = tmp_path / "kubernetes"
        subdir.mkdir()
        task_file = subdir / "task.md"
        task_file.write_text(sample_markdown_content)

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file') as mock_load:
            mock_load.return_value = sample_markdown_content
            tasks = parser.parse_directory(tmp_path)

        assert len(tasks) == 1
        assert "kubernetes" in tasks[0]["filepath"].lower()

    @pytest.mark.unit
    def test_get_statistics_empty(self, parser):
        """Test statistics with no parsed tasks."""
        stats = parser.get_statistics()

        assert stats == {}

    @pytest.mark.unit
    def test_get_statistics_with_tasks(self, parser):
        """Test statistics with parsed tasks."""
        # Add sample tasks to parser
        parser.parsed_tasks = [
            {
                "metadata": {"category": "Kubernetes"},
                "difficulty": "intermediate",
                "technologies": ["Kubernetes", "Docker"],
                "content": {"commands": ["cmd1", "cmd2"]},
                "solution": "Solution 1"
            },
            {
                "metadata": {"category": "Docker"},
                "difficulty": "beginner",
                "technologies": ["Docker"],
                "content": {"commands": ["cmd3"]},
                "solution": None
            },
            {
                "metadata": {"category": "Kubernetes"},
                "difficulty": "advanced",
                "technologies": ["Kubernetes", "Ansible"],
                "content": {"commands": ["cmd4", "cmd5", "cmd6"]},
                "solution": "Solution 2"
            }
        ]

        stats = parser.get_statistics()

        assert stats["total_tasks"] == 3
        assert stats["categories"]["Kubernetes"] == 2
        assert stats["categories"]["Docker"] == 1
        assert stats["difficulties"]["beginner"] == 1
        assert stats["difficulties"]["intermediate"] == 1
        assert stats["difficulties"]["advanced"] == 1
        assert stats["technologies"]["Kubernetes"] == 2
        assert stats["technologies"]["Docker"] == 2
        assert stats["technologies"]["Ansible"] == 1
        assert stats["avg_commands_per_task"] == 2.0
        assert stats["tasks_with_solutions"] == 2

    @pytest.mark.unit
    def test_extract_sections_no_title(self, parser):
        """Test section extraction without title."""
        content = """
        ## Introduction
        Some intro text.

        ## Requirements
        - Requirement 1
        """
        sections = parser._extract_sections(content)

        assert "title" not in sections
        assert "introduction" in sections
        assert "requirements" in sections

    @pytest.mark.unit
    def test_extract_all_code_blocks_empty(self, parser):
        """Test code block extraction with no code blocks."""
        content = "Just plain text without any code blocks."
        code_blocks = parser._extract_all_code_blocks(content)

        assert code_blocks == {}

    @pytest.mark.unit
    def test_extract_commands_no_commands(self, parser):
        """Test command extraction with no commands."""
        content = """
        # Task without commands

        Just some text description.
        """
        commands = parser._extract_commands(content)

        assert commands == []

    @pytest.mark.unit
    def test_extract_configurations_json(self, parser):
        """Test JSON configuration extraction."""
        content = """
        ```json
        {
          "name": "config",
          "version": "1.0"
        }
        ```
        """
        configs = parser._extract_configurations(content)

        assert len(configs["other"]) == 1
        assert '"name"' in configs["other"][0]

    @pytest.mark.unit
    def test_extract_technologies_case_insensitive(self, parser):
        """Test technology extraction is case insensitive."""
        content = """
        Deploy KUBERNETES cluster.
        Use docker containers.
        Configure ANSIBLE playbook.
        """
        technologies = parser._extract_technologies(content)

        assert "Kubernetes" in technologies
        assert "Docker" in technologies
        assert "Ansible" in technologies

    @pytest.mark.unit
    def test_parse_task_integration(self, parser, tmp_path):
        """Integration test for complete task parsing."""
        content = """# Complete Task

## Requirements
- Requirement 1
- Requirement 2

## Solution
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
```

```bash
kubectl apply -f pod.yaml
```

## Verification
Check the deployment.
"""
        task_file = tmp_path / "complete.md"
        task_file.write_text(content)

        with patch('src.kodekloud_tasks.task_parser.load_markdown_file') as mock_load:
            mock_load.return_value = content
            result = parser.parse_task(task_file)

        assert result["filepath"] == str(task_file)
        assert result["metadata"]["title"] == "Complete Task"
        assert len(result["requirements"]) == 2
        assert result["solution"] is not None
        assert len(result["content"]["code_blocks"]["yaml"]) == 1
        assert len(result["content"]["code_blocks"]["bash"]) == 1
        assert len(result["content"]["commands"]) > 0
        assert result["difficulty"] in ["beginner", "intermediate", "advanced"]
        assert isinstance(result["technologies"], list)