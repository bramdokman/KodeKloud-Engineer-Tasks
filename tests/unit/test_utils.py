"""Unit tests for utility functions."""

import pytest
import tempfile
from pathlib import Path
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


class TestLoadMarkdownFile:
    """Test load_markdown_file function."""

    @pytest.mark.unit
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing markdown file."""
        content = "# Test File\nThis is a test."
        filepath = tmp_path / "test.md"
        filepath.write_text(content)

        result = load_markdown_file(filepath)
        assert result == content

    @pytest.mark.unit
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_markdown_file("/nonexistent/file.md")

    @pytest.mark.unit
    def test_load_with_unicode(self, tmp_path):
        """Test loading file with unicode characters."""
        content = "# Test 文件\n🎉 Unicode content"
        filepath = tmp_path / "unicode.md"
        filepath.write_text(content, encoding='utf-8')

        result = load_markdown_file(filepath)
        assert result == content


class TestExtractCodeBlocks:
    """Test extract_code_blocks function."""

    @pytest.mark.unit
    def test_extract_single_code_block(self):
        """Test extracting a single code block."""
        content = """
        Some text
        ```python
        print("Hello")
        ```
        More text
        """
        blocks = extract_code_blocks(content)
        assert len(blocks) == 1
        assert 'print("Hello")' in blocks[0]

    @pytest.mark.unit
    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks."""
        content = """
        ```bash
        echo "First"
        ```

        ```yaml
        key: value
        ```
        """
        blocks = extract_code_blocks(content)
        assert len(blocks) == 2

    @pytest.mark.unit
    def test_extract_with_language_filter(self):
        """Test extracting code blocks with language filter."""
        content = """
        ```python
        print("Python")
        ```

        ```bash
        echo "Bash"
        ```
        """
        python_blocks = extract_code_blocks(content, "python")
        assert len(python_blocks) == 1
        assert "Python" in python_blocks[0]

        bash_blocks = extract_code_blocks(content, "bash")
        assert len(bash_blocks) == 1
        assert "Bash" in bash_blocks[0]

    @pytest.mark.unit
    def test_extract_no_code_blocks(self):
        """Test extracting from content without code blocks."""
        content = "Just plain text without code blocks"
        blocks = extract_code_blocks(content)
        assert len(blocks) == 0


class TestValidateYamlSyntax:
    """Test validate_yaml_syntax function."""

    @pytest.mark.unit
    def test_valid_yaml(self):
        """Test validation of valid YAML."""
        yaml_content = """
        apiVersion: v1
        kind: Pod
        metadata:
          name: test-pod
        """
        is_valid, error = validate_yaml_syntax(yaml_content)
        assert is_valid is True
        assert error is None

    @pytest.mark.unit
    def test_invalid_yaml(self):
        """Test validation of invalid YAML."""
        yaml_content = """
        key: value
          invalid: indentation
        """
        is_valid, error = validate_yaml_syntax(yaml_content)
        assert is_valid is False
        assert error is not None

    @pytest.mark.unit
    def test_empty_yaml(self):
        """Test validation of empty YAML."""
        is_valid, error = validate_yaml_syntax("")
        assert is_valid is True
        assert error is None


class TestValidateJsonSyntax:
    """Test validate_json_syntax function."""

    @pytest.mark.unit
    def test_valid_json(self):
        """Test validation of valid JSON."""
        json_content = '{"key": "value", "number": 123}'
        is_valid, error = validate_json_syntax(json_content)
        assert is_valid is True
        assert error is None

    @pytest.mark.unit
    def test_invalid_json(self):
        """Test validation of invalid JSON."""
        json_content = '{"key": "value"'  # Missing closing brace
        is_valid, error = validate_json_syntax(json_content)
        assert is_valid is False
        assert error is not None

    @pytest.mark.unit
    def test_empty_json(self):
        """Test validation of empty JSON."""
        is_valid, error = validate_json_syntax("{}")
        assert is_valid is True
        assert error is None


class TestFindAllFiles:
    """Test find_all_files function."""

    @pytest.mark.unit
    def test_find_markdown_files(self, tmp_path):
        """Test finding markdown files in directory."""
        # Create test structure
        (tmp_path / "file1.md").write_text("content1")
        (tmp_path / "file2.md").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.md").write_text("content3")
        (tmp_path / "other.txt").write_text("other")

        files = find_all_files(tmp_path, "*.md")
        assert len(files) == 3
        assert all(f.suffix == ".md" for f in files)

    @pytest.mark.unit
    def test_find_no_matching_files(self, tmp_path):
        """Test finding files when no matches exist."""
        files = find_all_files(tmp_path, "*.nonexistent")
        assert len(files) == 0

    @pytest.mark.unit
    def test_find_in_nonexistent_directory(self):
        """Test finding files in non-existent directory."""
        files = find_all_files("/nonexistent/directory", "*.md")
        assert len(files) == 0


class TestExtractTaskMetadata:
    """Test extract_task_metadata function."""

    @pytest.mark.unit
    def test_extract_title(self):
        """Test extracting task title."""
        content = "# Deploy Kubernetes Application\nSome content"
        metadata = extract_task_metadata(content)
        assert metadata["title"] == "Deploy Kubernetes Application"

    @pytest.mark.unit
    def test_extract_solution_presence(self):
        """Test detecting solution section."""
        content = """
        # Task
        ## Problem
        ## Solution
        Here is the solution
        """
        metadata = extract_task_metadata(content)
        assert metadata["has_solution"] is True

    @pytest.mark.unit
    def test_extract_commands_presence(self):
        """Test detecting shell commands."""
        content = """
        # Task
        ```bash
        kubectl get pods
        ```
        """
        metadata = extract_task_metadata(content)
        assert metadata["has_commands"] is True

    @pytest.mark.unit
    def test_extract_yaml_presence(self):
        """Test detecting YAML content."""
        content = """
        # Task
        ```yaml
        apiVersion: v1
        ```
        """
        metadata = extract_task_metadata(content)
        assert metadata["has_yaml"] is True

    @pytest.mark.unit
    def test_extract_category(self):
        """Test extracting task category."""
        content = "# Kubernetes Deployment Task"
        metadata = extract_task_metadata(content)
        assert metadata["category"] == "Kubernetes"


class TestValidateKubernetesResource:
    """Test validate_kubernetes_resource function."""

    @pytest.mark.unit
    def test_valid_resource(self):
        """Test validation of valid Kubernetes resource."""
        yaml_content = """
        apiVersion: v1
        kind: Pod
        metadata:
          name: test-pod
        spec:
          containers:
          - name: nginx
            image: nginx:latest
        """
        is_valid, error = validate_kubernetes_resource(yaml_content)
        assert is_valid is True
        assert error is None

    @pytest.mark.unit
    def test_missing_api_version(self):
        """Test validation with missing apiVersion."""
        yaml_content = """
        kind: Pod
        metadata:
          name: test-pod
        """
        is_valid, error = validate_kubernetes_resource(yaml_content)
        assert is_valid is False
        assert "apiVersion" in error

    @pytest.mark.unit
    def test_missing_kind(self):
        """Test validation with missing kind."""
        yaml_content = """
        apiVersion: v1
        metadata:
          name: test-pod
        """
        is_valid, error = validate_kubernetes_resource(yaml_content)
        assert is_valid is False
        assert "kind" in error

    @pytest.mark.unit
    def test_missing_metadata_name(self):
        """Test validation with missing metadata.name."""
        yaml_content = """
        apiVersion: v1
        kind: Pod
        metadata:
          labels:
            app: test
        """
        is_valid, error = validate_kubernetes_resource(yaml_content)
        assert is_valid is False
        assert "metadata.name" in error


class TestNormalizeWhitespace:
    """Test normalize_whitespace function."""

    @pytest.mark.unit
    def test_normalize_multiple_spaces(self):
        """Test normalizing multiple spaces."""
        text = "This  has   multiple    spaces"
        result = normalize_whitespace(text)
        assert result == "This has multiple spaces"

    @pytest.mark.unit
    def test_normalize_newlines(self):
        """Test normalizing newlines."""
        text = "Line 1\n\nLine 2\n\n\nLine 3"
        result = normalize_whitespace(text)
        assert result == "Line 1 Line 2 Line 3"

    @pytest.mark.unit
    def test_normalize_tabs(self):
        """Test normalizing tabs."""
        text = "Tab\there\ttabs"
        result = normalize_whitespace(text)
        assert result == "Tab here tabs"


class TestCalculateSimilarity:
    """Test calculate_similarity function."""

    @pytest.mark.unit
    def test_identical_texts(self):
        """Test similarity of identical texts."""
        text = "This is a test"
        similarity = calculate_similarity(text, text)
        assert similarity == 1.0

    @pytest.mark.unit
    def test_completely_different_texts(self):
        """Test similarity of completely different texts."""
        text1 = "apple orange banana"
        text2 = "car bike train"
        similarity = calculate_similarity(text1, text2)
        assert similarity == 0.0

    @pytest.mark.unit
    def test_partial_similarity(self):
        """Test partial similarity."""
        text1 = "The quick brown fox"
        text2 = "The slow brown dog"
        similarity = calculate_similarity(text1, text2)
        assert 0.0 < similarity < 1.0

    @pytest.mark.unit
    def test_empty_texts(self):
        """Test similarity with empty texts."""
        assert calculate_similarity("", "") == 1.0
        assert calculate_similarity("text", "") == 0.0
        assert calculate_similarity("", "text") == 0.0