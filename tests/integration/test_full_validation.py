"""Integration tests for full validation workflow."""

import pytest
from pathlib import Path
from src.kodekloud_tasks.doc_validator import DocumentationValidator
from src.kodekloud_tasks.k8s_validator import KubernetesValidator
from src.kodekloud_tasks.task_parser import TaskParser


class TestFullValidationWorkflow:
    """Test complete validation workflow."""

    @pytest.fixture
    def setup_test_project(self, tmp_path):
        """Create a test project structure."""
        # Create directory structure
        k8s_dir = tmp_path / "Kubernetes"
        k8s_dir.mkdir()
        docker_dir = tmp_path / "Docker"
        docker_dir.mkdir()

        # Create Kubernetes tasks
        k8s_task1 = k8s_dir / "deploy_nginx.md"
        k8s_task1.write_text("""# Deploy Nginx on Kubernetes

## Problem
Deploy an Nginx web server on Kubernetes cluster with 3 replicas.

## Requirements
- Create a deployment with 3 replicas
- Expose the deployment as a service
- Use LoadBalancer type

## Solution
First, create the deployment:

```bash
kubectl create deployment nginx-web --image=nginx:latest
kubectl scale deployment nginx-web --replicas=3
```

Then create the service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: LoadBalancer
  selector:
    app: nginx-web
  ports:
  - port: 80
    targetPort: 80
```

## Verification
```bash
kubectl get deployments
kubectl get services
kubectl get pods -l app=nginx-web
```
""")

        k8s_task2 = k8s_dir / "cronjob_backup.md"
        k8s_task2.write_text("""# Create Backup CronJob

## Problem
Create a CronJob that runs a backup script every hour.

## Solution
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-cronjob
spec:
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command:
            - /bin/sh
            - -c
            - echo "Running backup..."
          restartPolicy: OnFailure
```
""")

        # Create Docker task
        docker_task = docker_dir / "build_image.md"
        docker_task.write_text("""# Build Docker Image

## Problem
Build a custom Docker image for a Node.js application.

## Solution
Create a Dockerfile:

```dockerfile
FROM node:14
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

Build the image:
```bash
docker build -t myapp:latest .
docker run -p 3000:3000 myapp:latest
```
""")

        return tmp_path

    @pytest.mark.integration
    def test_validate_entire_project(self, setup_test_project):
        """Test validating an entire project structure."""
        doc_validator = DocumentationValidator()
        results = doc_validator.validate_directory(setup_test_project)

        assert len(results) == 3
        assert all(r["valid"] for r in results)

        summary = doc_validator.get_summary()
        assert summary["total_files"] == 3
        assert summary["valid_files"] == 3
        assert summary["validation_rate"] == 100.0

    @pytest.mark.integration
    def test_validate_kubernetes_manifests_in_docs(self, setup_test_project):
        """Test extracting and validating K8s manifests from documentation."""
        k8s_validator = KubernetesValidator()
        k8s_dir = setup_test_project / "Kubernetes"

        for filepath in k8s_dir.glob("*.md"):
            results = k8s_validator.validate_from_file(filepath)
            for result in results:
                assert "source_file" in result
                if result["resources"]:
                    assert result["valid"] or len(result["errors"]) > 0

    @pytest.mark.integration
    def test_parse_and_analyze_tasks(self, setup_test_project):
        """Test parsing and analyzing all tasks."""
        parser = TaskParser()
        tasks = parser.parse_directory(setup_test_project)

        assert len(tasks) == 3

        # Check Kubernetes tasks
        k8s_tasks = [t for t in tasks if "Kubernetes" in str(t["filepath"])]
        assert len(k8s_tasks) == 2

        for task in k8s_tasks:
            assert task["metadata"]["category"] == "Kubernetes"
            assert task["metadata"]["has_solution"] is True
            assert task["content"]["commands"] is not None
            assert "Kubernetes" in task["technologies"]

        # Check statistics
        stats = parser.get_statistics()
        assert stats["total_tasks"] == 3
        assert stats["tasks_with_solutions"] == 3
        assert "Kubernetes" in stats["categories"]
        assert "Docker" in stats["categories"]

    @pytest.mark.integration
    def test_combined_validation_workflow(self, setup_test_project):
        """Test combined validation of documentation and K8s resources."""
        doc_validator = DocumentationValidator()
        k8s_validator = KubernetesValidator()
        parser = TaskParser()

        # Parse all tasks
        tasks = parser.parse_directory(setup_test_project)

        validation_results = []
        for task in tasks:
            # Validate documentation
            doc_result = doc_validator.validate_file(Path(task["filepath"]))

            # If it's a Kubernetes task, validate K8s resources
            if task["metadata"]["category"] == "Kubernetes":
                k8s_results = k8s_validator.validate_from_file(Path(task["filepath"]))
                doc_result["k8s_validation"] = k8s_results

            validation_results.append(doc_result)

        # Check results
        assert len(validation_results) == 3
        k8s_validated = [r for r in validation_results if "k8s_validation" in r]
        assert len(k8s_validated) == 2

    @pytest.mark.integration
    def test_error_handling_in_workflow(self, tmp_path):
        """Test error handling in validation workflow."""
        # Create a file with various issues
        problem_file = tmp_path / "problematic.md"
        problem_file.write_text("""## Missing Title

```yaml
apiVersion: v1
kind: Pod
  invalid: yaml indentation
```

[Broken link]()

```
Unspecified code block
```
""")

        doc_validator = DocumentationValidator()
        k8s_validator = KubernetesValidator()

        # Validate documentation
        doc_result = doc_validator.validate_file(problem_file)
        assert doc_result["valid"] is False
        assert len(doc_result["errors"]) > 0
        assert len(doc_result["warnings"]) > 0

        # Try to validate K8s resources
        k8s_results = k8s_validator.validate_from_file(problem_file)
        assert any(not r["valid"] for r in k8s_results if r["resources"])

    @pytest.mark.integration
    def test_large_project_validation(self, tmp_path):
        """Test validation of a large project with many files."""
        # Create multiple task files
        for category in ["Kubernetes", "Docker", "Ansible"]:
            cat_dir = tmp_path / category
            cat_dir.mkdir()

            for i in range(10):
                task_file = cat_dir / f"task_{i}.md"
                task_file.write_text(f"""# {category} Task {i}

## Problem
Task description for {category} task {i}

## Solution
Solution content here

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: task-{i}
data:
  key: value-{i}
```

```bash
echo "Command for task {i}"
```
""")

        doc_validator = DocumentationValidator()
        results = doc_validator.validate_directory(tmp_path)

        assert len(results) == 30
        assert all(r["valid"] for r in results)

        summary = doc_validator.get_summary()
        assert summary["total_files"] == 30
        assert summary["validation_rate"] == 100.0

    @pytest.mark.integration
    def test_cross_validation_consistency(self, setup_test_project):
        """Test consistency across different validators."""
        doc_validator = DocumentationValidator()
        parser = TaskParser()

        # Get metadata from parser
        parsed_tasks = parser.parse_directory(setup_test_project)

        # Get validation from doc validator
        validation_results = doc_validator.validate_directory(setup_test_project)

        # Cross-check consistency
        for parsed, validated in zip(parsed_tasks, validation_results):
            assert parsed["filepath"] == validated["filepath"]

            # Check metadata consistency
            assert parsed["metadata"]["title"] == validated["metadata"]["title"]
            assert parsed["metadata"]["has_solution"] == validated["metadata"]["has_solution"]
            assert parsed["metadata"]["has_yaml"] == validated["metadata"]["has_yaml"]
            assert parsed["metadata"]["has_commands"] == validated["metadata"]["has_commands"]