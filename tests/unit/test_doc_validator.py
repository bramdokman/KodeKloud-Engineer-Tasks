"""Unit tests for documentation validator."""

import pytest
from pathlib import Path
from src.kodekloud_tasks.doc_validator import DocumentationValidator


class TestDocumentationValidator:
    """Test DocumentationValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return DocumentationValidator(strict_mode=True)

    @pytest.fixture
    def sample_markdown_file(self, tmp_path):
        """Create a sample markdown file."""
        content = """# Deploy Application on Kubernetes

## Problem
Deploy a web application on Kubernetes cluster.

## Solution
Here is how to deploy the application:

```bash
kubectl create deployment webapp --image=nginx
kubectl expose deployment webapp --port=80 --type=LoadBalancer
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
```

## Verification
Check the deployment status:

```bash
kubectl get deployments
kubectl get services
```
"""
        filepath = tmp_path / "deploy_app.md"
        filepath.write_text(content)
        return filepath

    @pytest.mark.unit
    def test_validate_valid_file(self, validator, sample_markdown_file):
        """Test validation of a valid documentation file."""
        result = validator.validate_file(sample_markdown_file)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["metadata"]["title"] == "Deploy Application on Kubernetes"
        assert result["metadata"]["has_solution"] is True
        assert result["metadata"]["has_commands"] is True
        assert result["metadata"]["has_yaml"] is True

    @pytest.mark.unit
    def test_validate_missing_title(self, validator, tmp_path):
        """Test validation with missing title."""
        content = """## Solution
        Some solution here
        """
        filepath = tmp_path / "no_title.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert result["valid"] is False
        assert any("title" in error.lower() for error in result["errors"])

    @pytest.mark.unit
    def test_validate_invalid_yaml(self, validator, tmp_path):
        """Test validation with invalid YAML."""
        content = """# Task

```yaml
apiVersion: v1
kind: Pod
  invalid: indentation
```
"""
        filepath = tmp_path / "invalid_yaml.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert result["valid"] is False
        assert any("yaml" in error.lower() for error in result["errors"])

    @pytest.mark.unit
    def test_validate_unspecified_code_blocks(self, validator, tmp_path):
        """Test detection of unspecified code blocks."""
        content = """# Task

```
echo "No language specified"
```
"""
        filepath = tmp_path / "unspecified_code.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert any("language specification" in warning for warning in result["warnings"])

    @pytest.mark.unit
    def test_check_excessive_blank_lines(self, validator, tmp_path):
        """Test detection of excessive blank lines."""
        content = """# Task




Too many blank lines above
"""
        filepath = tmp_path / "excessive_blanks.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert any("blank lines" in warning for warning in result["warnings"])

    @pytest.mark.unit
    def test_check_long_lines(self, validator, tmp_path):
        """Test detection of long lines."""
        long_line = "x" * 150
        content = f"""# Task

{long_line}
"""
        filepath = tmp_path / "long_lines.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert any("exceeds" in warning and "characters" in warning for warning in result["warnings"])

    @pytest.mark.unit
    def test_check_trailing_whitespace(self, validator, tmp_path):
        """Test detection of trailing whitespace."""
        content = """# Task

Content with trailing spaces
"""
        filepath = tmp_path / "trailing_space.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert any("trailing whitespace" in warning.lower() for warning in result["warnings"])

    @pytest.mark.unit
    def test_check_broken_links(self, validator, tmp_path):
        """Test detection of broken links."""
        content = """# Task

[Empty link]()
[Internal link](#nonexistent-anchor)
[Valid link](https://example.com)
"""
        filepath = tmp_path / "links.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        assert any("empty link" in error.lower() for error in result["errors"])
        assert any("broken anchor" in warning.lower() for warning in result["warnings"])

    @pytest.mark.unit
    def test_validate_directory(self, validator, tmp_path):
        """Test validation of multiple files in a directory."""
        # Create multiple test files
        for i in range(3):
            content = f"""# Task {i}

## Solution
Solution content {i}
"""
            filepath = tmp_path / f"task_{i}.md"
            filepath.write_text(content)

        # Create a hidden file that should be ignored
        hidden_file = tmp_path / ".hidden.md"
        hidden_file.write_text("# Hidden")

        results = validator.validate_directory(tmp_path)

        assert len(results) == 3  # Hidden file should be ignored
        assert all(r["valid"] for r in results)

    @pytest.mark.unit
    def test_get_summary(self, validator, tmp_path):
        """Test getting validation summary."""
        # Create a mix of valid and invalid files
        valid_content = """# Valid Task

## Solution
Valid solution
"""
        invalid_content = """Missing title

Content without proper structure
"""

        (tmp_path / "valid.md").write_text(valid_content)
        (tmp_path / "invalid.md").write_text(invalid_content)

        validator.validate_directory(tmp_path)
        summary = validator.get_summary()

        assert summary["total_files"] == 2
        assert summary["valid_files"] == 1
        assert summary["invalid_files"] == 1
        assert summary["validation_rate"] == 50.0

    @pytest.mark.unit
    def test_strict_mode_disabled(self, tmp_path):
        """Test validator with strict mode disabled."""
        validator = DocumentationValidator(strict_mode=False)

        content = """# Task

Basic content without recommended sections
"""
        filepath = tmp_path / "basic.md"
        filepath.write_text(content)

        result = validator.validate_file(filepath)
        # Should have fewer warnings in non-strict mode
        assert len(result["warnings"]) < 3