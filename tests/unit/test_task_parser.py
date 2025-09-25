"""Unit tests for TaskParser class."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.kodekloud_tasks.task_parser import TaskParser


class TestTaskParser:
    """Test TaskParser class functionality."""

    @pytest.fixture
    def parser(self):
        """Create a TaskParser instance for testing."""
        return TaskParser()

    @pytest.fixture
    def sample_task_content(self):
        """Sample task content for testing."""
        return """# Deploy Kubernetes Application

## Requirements
- Deploy a pod named nginx-pod
- Use nginx:latest image
- Create a service for the pod
- Ensure high availability

## Solution

Here's how to deploy the application:

```bash
kubectl create pod nginx-pod --image=nginx:latest
kubectl expose pod nginx-pod --port=80
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
```

## Verification

Run the following commands to verify:

```bash
kubectl get pods
kubectl get services
```
"""

    @pytest.mark.unit
    def test_init(self, parser):
        """Test TaskParser initialization."""
        assert parser.parsed_tasks == []

    @pytest.mark.unit
    @patch('src.kodekloud_tasks.task_parser.load_markdown_file')
    def test_parse_task(self, mock_load, parser, sample_task_content):
        """Test parsing a single task."""
        mock_load.return_value = sample_task_content
        filepath = Path("/test/task.md")

        result = parser.parse_task(filepath)

        assert result["filepath"] == str(filepath)
        assert "metadata" in result
        assert "content" in result
        assert "requirements" in result
        assert "solution" in result
        assert "difficulty" in result
        assert "technologies" in result
        mock_load.assert_called_once_with(filepath)

    @pytest.mark.unit
    def test_extract_sections(self, parser, sample_task_content):
        """Test extracting sections from markdown content."""
        sections = parser._extract_sections(sample_task_content)

        assert "title" in sections
        assert sections["title"] == "Deploy Kubernetes Application"
        assert "requirements" in sections
        assert "solution" in sections
        assert "verification" in sections

    @pytest.mark.unit
    def test_extract_all_code_blocks(self, parser, sample_task_content):
        """Test extracting all code blocks categorized by language."""
        code_blocks = parser._extract_all_code_blocks(sample_task_content)

        assert "bash" in code_blocks
        assert "yaml" in code_blocks
        assert len(code_blocks["bash"]) == 2
        assert len(code_blocks["yaml"]) == 1
        assert "kubectl create pod" in code_blocks["bash"][0]

    @pytest.mark.unit
    def test_extract_commands(self, parser, sample_task_content):
        """Test extracting shell commands from content."""
        commands = parser._extract_commands(sample_task_content)

        assert len(commands) > 0
        assert any("kubectl create pod" in cmd for cmd in commands)
        assert any("kubectl get pods" in cmd for cmd in commands)

    @pytest.mark.unit
    def test_extract_commands_with_inline_code(self, parser):
        """Test extracting inline commands."""
        content = """
        Run `kubectl get pods` to see the pods.
        Also use `docker ps` to check containers.
        """
        commands = parser._extract_commands(content)

        assert "kubectl get pods" in commands
        assert "docker ps" in commands

    @pytest.mark.unit
    def test_extract_configurations(self, parser, sample_task_content):
        """Test extracting configuration examples."""
        configs = parser._extract_configurations(sample_task_content)

        assert "kubernetes" in configs
        assert len(configs["kubernetes"]) == 1
        assert "apiVersion: v1" in configs["kubernetes"][0]

    @pytest.mark.unit
    def test_extract_configurations_multiple_types(self, parser):
        """Test extracting different types of configurations."""
        content = """
        ```yaml
        apiVersion: v1
        kind: Service
        ```

        ```yaml
        - hosts: all
          ansible.builtin.debug:
            msg: "Ansible playbook"
        ```

        ```json
        {"key": "value"}
        ```
        """
        configs = parser._extract_configurations(content)

        assert len(configs["kubernetes"]) == 1
        assert len(configs["ansible"]) == 1
        assert len(configs["other"]) == 1

    @pytest.mark.unit
    def test_extract_requirements(self, parser, sample_task_content):
        """Test extracting requirements from task."""
        requirements = parser._extract_requirements(sample_task_content)

        assert len(requirements) == 4
        assert "Deploy a pod named nginx-pod" in requirements
        assert "Use nginx:latest image" in requirements

    @pytest.mark.unit
    def test_extract_requirements_numbered(self, parser):
        """Test extracting numbered requirements."""
        content = """
        ## Requirements
        1. First requirement
        2. Second requirement
        3. Third requirement
        """
        requirements = parser._extract_requirements(content)

        assert len(requirements) == 3
        assert "First requirement" in requirements

    @pytest.mark.unit
    def test_extract_solution(self, parser, sample_task_content):
        """Test extracting solution section."""
        solution = parser._extract_solution(sample_task_content)

        assert solution is not None
        assert "deploy the application" in solution

    @pytest.mark.unit
    def test_extract_solution_missing(self, parser):
        """Test extracting solution when not present."""
        content = "# Task\n## Requirements\n- Do something"
        solution = parser._extract_solution(content)

        assert solution is None

    @pytest.mark.unit
    def test_estimate_difficulty_beginner(self, parser):
        """Test difficulty estimation for beginner tasks."""
        content = "# Simple Task\nDeploy a single pod."
        difficulty = parser._estimate_difficulty(content)

        assert difficulty == "beginner"

    @pytest.mark.unit
    def test_estimate_difficulty_intermediate(self, parser):
        """Test difficulty estimation for intermediate tasks."""
        content = "# Task\n" + "x" * 2500 + "\n```bash\ncommand1\n```\n```yaml\nconfig\n```\n```bash\ncommand2\n```"
        difficulty = parser._estimate_difficulty(content)

        assert difficulty == "intermediate"

    @pytest.mark.unit
    def test_estimate_difficulty_advanced(self, parser):
        """Test difficulty estimation for advanced tasks."""
        content = """# Complex Task
        This is a very long task with multi-node cluster setup.
        It involves RBAC configuration and high availability.
        Performance optimization is required.
        """ + "x" * 5000 + "\n".join([f"```bash\ncmd{i}\n```" for i in range(10)])

        difficulty = parser._estimate_difficulty(content)
        assert difficulty == "advanced"

    @pytest.mark.unit
    def test_extract_technologies(self, parser, sample_task_content):
        """Test extracting technologies from task."""
        technologies = parser._extract_technologies(sample_task_content)

        assert "Kubernetes" in technologies
        assert len(technologies) > 0

    @pytest.mark.unit
    def test_extract_technologies_multiple(self, parser):
        """Test extracting multiple technologies."""
        content = """
        Deploy using Docker and Kubernetes.
        Configure Nginx and setup Jenkins CI/CD.
        Use Ansible for configuration management.
        Store data in MySQL and cache in Redis.
        Monitor with Prometheus and Grafana.
        Deploy on AWS using Terraform.
        """
        technologies = parser._extract_technologies(content)

        expected = ["AWS", "Ansible", "Docker", "Grafana", "Jenkins",
                   "Kubernetes", "MySQL", "Nginx", "Prometheus", "Redis", "Terraform"]
        assert technologies == expected

    @pytest.mark.unit
    @patch('src.kodekloud_tasks.utils.find_all_files')
    @patch('src.kodekloud_tasks.task_parser.load_markdown_file')
    def test_parse_directory(self, mock_load, mock_find, parser, sample_task_content):
        """Test parsing all tasks in a directory."""
        mock_find.return_value = [
            Path("/test/task1.md"),
            Path("/test/task2.md"),
            Path("/test/.hidden.md")  # Should be skipped
        ]
        mock_load.return_value = sample_task_content

        tasks = parser.parse_directory(Path("/test"))

        assert len(tasks) == 2
        assert len(parser.parsed_tasks) == 2
        mock_find.assert_called_once_with(Path("/test"), "*.md")

    @pytest.mark.unit
    def test_get_statistics_empty(self, parser):
        """Test getting statistics with no parsed tasks."""
        stats = parser.get_statistics()
        assert stats == {}

    @pytest.mark.unit
    def test_get_statistics_with_tasks(self, parser):
        """Test getting statistics with parsed tasks."""
        parser.parsed_tasks = [
            {
                "metadata": {"category": "Kubernetes"},
                "difficulty": "intermediate",
                "technologies": ["Kubernetes", "Docker"],
                "content": {"commands": ["cmd1", "cmd2"]},
                "solution": "Solution text"
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
                "content": {"commands": []},
                "solution": "Another solution"
            }
        ]

        stats = parser.get_statistics()

        assert stats["total_tasks"] == 3
        assert stats["categories"]["Kubernetes"] == 2
        assert stats["categories"]["Docker"] == 1
        assert stats["difficulties"]["beginner"] == 1
        assert stats["difficulties"]["intermediate"] == 1
        assert stats["difficulties"]["advanced"] == 1
        assert stats["technologies"]["Docker"] == 2
        assert stats["technologies"]["Kubernetes"] == 2
        assert stats["technologies"]["Ansible"] == 1
        assert stats["avg_commands_per_task"] == 1.0
        assert stats["tasks_with_solutions"] == 2

    @pytest.mark.unit
    def test_parse_task_integration(self, parser, tmp_path):
        """Test complete task parsing integration."""
        content = """# Test Task
## Requirements
- Requirement 1
- Requirement 2

## Solution
Test solution

```bash
echo "test"
```

```yaml
key: value
```
"""
        filepath = tmp_path / "test.md"
        filepath.write_text(content)

        result = parser.parse_task(filepath)

        assert result["filepath"] == str(filepath)
        assert result["metadata"]["title"] == "Test Task"
        assert len(result["requirements"]) == 2
        assert result["solution"] is not None
        assert "bash" in result["content"]["code_blocks"]
        assert "yaml" in result["content"]["code_blocks"]
        assert len(result["content"]["commands"]) > 0
        assert result in parser.parsed_tasks