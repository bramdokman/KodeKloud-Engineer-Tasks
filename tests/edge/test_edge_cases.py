"""Edge case tests for KodeKloud tasks validation."""

import pytest
from pathlib import Path
from src.kodekloud_tasks.doc_validator import DocumentationValidator
from src.kodekloud_tasks.k8s_validator import KubernetesValidator
from src.kodekloud_tasks.task_parser import TaskParser
from src.kodekloud_tasks.utils import (
    validate_yaml_syntax,
    extract_code_blocks,
    calculate_similarity,
)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.edge
    def test_empty_file_handling(self, tmp_path):
        """Test handling of empty files."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")

        doc_validator = DocumentationValidator()
        result = doc_validator.validate_file(empty_file)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.edge
    def test_very_large_file(self, tmp_path):
        """Test handling of very large files."""
        # Create a file with 10000 lines
        large_content = "# Large File\n\n"
        large_content += "\n".join([f"Line {i}" for i in range(10000)])

        large_file = tmp_path / "large.md"
        large_file.write_text(large_content)

        parser = TaskParser()
        result = parser.parse_task(large_file)

        assert result is not None
        assert result["metadata"]["title"] == "Large File"

    @pytest.mark.edge
    def test_malformed_yaml_recovery(self):
        """Test recovery from malformed YAML."""
        malformed_yamls = [
            "key: value\n  bad: indentation",
            "- item without list context",
            "key: [unclosed list",
            "{unclosed: dict",
            "key: value\nkey: duplicate key",
        ]

        validator = KubernetesValidator()
        for yaml_content in malformed_yamls:
            result = validator.validate_manifest(yaml_content)
            assert result["valid"] is False
            assert len(result["errors"]) > 0

    @pytest.mark.edge
    def test_unicode_and_special_characters(self, tmp_path):
        """Test handling of Unicode and special characters."""
        unicode_content = """# 部署 Kubernetes 应用 🚀

## 問題
Deploy application with special chars: <>&"'`

## Solution
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: special-config
data:
  message: "Hello 世界 🌍"
  special: '<script>alert("test")</script>'
```
"""
        unicode_file = tmp_path / "unicode.md"
        unicode_file.write_text(unicode_content, encoding='utf-8')

        doc_validator = DocumentationValidator()
        result = doc_validator.validate_file(unicode_file)

        # Should handle Unicode properly
        assert result["metadata"]["title"] is not None
        assert "部署" in result["metadata"]["title"]

    @pytest.mark.edge
    def test_deeply_nested_yaml(self):
        """Test handling of deeply nested YAML structures."""
        deep_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: deep-config
data:
  config: |
    level1:
      level2:
        level3:
          level4:
            level5:
              level6:
                level7:
                  level8:
                    level9:
                      level10: "very deep value"
"""
        is_valid, error = validate_yaml_syntax(deep_yaml)
        assert is_valid is True

        validator = KubernetesValidator()
        result = validator.validate_manifest(deep_yaml)
        assert len(result["resources"]) == 1

    @pytest.mark.edge
    def test_mixed_line_endings(self, tmp_path):
        """Test handling of mixed line endings (CRLF, LF, CR)."""
        mixed_content = "# Title\r\n## Section 1\n### Subsection\r#### Deep section"

        mixed_file = tmp_path / "mixed_endings.md"
        mixed_file.write_bytes(mixed_content.encode('utf-8'))

        doc_validator = DocumentationValidator()
        result = doc_validator.validate_file(mixed_file)

        # Should handle mixed line endings
        assert "Title" in result["metadata"]["title"]

    @pytest.mark.edge
    def test_circular_references_in_yaml(self):
        """Test handling of YAML with anchors and aliases."""
        yaml_with_anchors = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: &name config-with-anchors
  labels:
    app: *name
data:
  default: &default_config
    timeout: 30
    retries: 3
  service1: *default_config
  service2: *default_config
"""
        is_valid, error = validate_yaml_syntax(yaml_with_anchors)
        assert is_valid is True

    @pytest.mark.edge
    def test_extremely_long_lines(self, tmp_path):
        """Test handling of extremely long lines."""
        long_line = "x" * 10000
        content = f"""# Title

{long_line}

## Section
Normal content
"""
        long_line_file = tmp_path / "long_lines.md"
        long_line_file.write_text(content)

        doc_validator = DocumentationValidator()
        result = doc_validator.validate_file(long_line_file)

        # Should handle but warn about long lines
        assert any("exceeds" in warning for warning in result["warnings"])

    @pytest.mark.edge
    def test_binary_file_rejection(self, tmp_path):
        """Test rejection of binary files."""
        binary_file = tmp_path / "binary.md"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')

        doc_validator = DocumentationValidator()
        with pytest.raises(Exception):
            doc_validator.validate_file(binary_file)

    @pytest.mark.edge
    def test_code_blocks_with_special_delimiters(self):
        """Test extraction of code blocks with various delimiters."""
        content = """
```yaml
normal: code block
```

````python
code block with four backticks
````

~~~bash
code block with tildes
~~~

    indented code block
    without delimiters
"""
        blocks = extract_code_blocks(content)
        assert len(blocks) >= 2  # At least the first two should be extracted

    @pytest.mark.edge
    def test_invalid_kubernetes_api_versions(self):
        """Test handling of invalid Kubernetes API versions."""
        invalid_versions = [
            "v1/apps",  # Reversed
            "app/v1",  # Typo
            "v2",  # Non-existent version
            "batch/v2",  # Non-existent version
            "",  # Empty
        ]

        validator = KubernetesValidator()
        for version in invalid_versions:
            yaml_content = f"""
apiVersion: {version}
kind: Deployment
metadata:
  name: test
spec:
  replicas: 1
"""
            result = validator.validate_manifest(yaml_content)
            # Should warn or error on unusual versions
            assert result["warnings"] or result["errors"]

    @pytest.mark.edge
    def test_resource_names_at_boundaries(self):
        """Test Kubernetes resource names at length boundaries."""
        validator = KubernetesValidator()

        # Maximum valid length (63 chars)
        max_name = "a" * 63
        yaml_content = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {max_name}
"""
        result = validator.validate_manifest(yaml_content)
        assert result["valid"] is True

        # Too long (64 chars)
        too_long_name = "a" * 64
        yaml_content = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {too_long_name}
"""
        result = validator.validate_manifest(yaml_content)
        assert result["valid"] is False

    @pytest.mark.edge
    def test_similarity_edge_cases(self):
        """Test text similarity calculation edge cases."""
        # Identical empty strings
        assert calculate_similarity("", "") == 1.0

        # One empty string
        assert calculate_similarity("text", "") == 0.0
        assert calculate_similarity("", "text") == 0.0

        # Only whitespace
        assert calculate_similarity("   ", "   ") == 1.0

        # Different case
        text = "The Quick Brown Fox"
        assert calculate_similarity(text, text.lower()) > 0.5

        # Punctuation differences
        assert calculate_similarity("Hello, world!", "Hello world") > 0.5

    @pytest.mark.edge
    def test_concurrent_file_access(self, tmp_path):
        """Test handling of concurrent file access scenarios."""
        import threading
        import time

        test_file = tmp_path / "concurrent.md"
        test_file.write_text("# Initial Content")

        results = []

        def validate_file():
            doc_validator = DocumentationValidator()
            try:
                result = doc_validator.validate_file(test_file)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        # Start multiple threads trying to validate the same file
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=validate_file)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All validations should complete without errors
        assert len(results) == 10
        assert all("error" not in r for r in results)

    @pytest.mark.edge
    def test_path_traversal_prevention(self, tmp_path):
        """Test prevention of path traversal attacks."""
        # Try to access files outside the project directory
        doc_validator = DocumentationValidator()

        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
        ]

        for dangerous_path in dangerous_paths:
            with pytest.raises((FileNotFoundError, OSError, ValueError)):
                doc_validator.validate_file(Path(dangerous_path))

    @pytest.mark.edge
    def test_recursive_directory_structure(self, tmp_path):
        """Test handling of deeply nested directory structures."""
        # Create deeply nested directories
        current_dir = tmp_path
        for i in range(50):
            current_dir = current_dir / f"level_{i}"
            current_dir.mkdir()

            # Add a task file at each level
            task_file = current_dir / f"task_{i}.md"
            task_file.write_text(f"# Task at Level {i}")

        doc_validator = DocumentationValidator()
        results = doc_validator.validate_directory(tmp_path)

        # Should handle deep nesting
        assert len(results) == 50

    @pytest.mark.edge
    def test_memory_efficient_large_file_processing(self, tmp_path):
        """Test memory-efficient processing of large files."""
        # Create a 100MB file
        large_file = tmp_path / "huge.md"

        with open(large_file, 'w') as f:
            f.write("# Huge File\n\n")
            for i in range(1000000):
                f.write(f"Line {i}: " + "x" * 90 + "\n")

        # Should not cause memory issues
        parser = TaskParser()
        # This should complete without running out of memory
        result = parser.parse_task(large_file)
        assert result is not None

    @pytest.mark.edge
    def test_special_yaml_features(self):
        """Test handling of special YAML features."""
        special_yaml = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: special-features
data:
  # Multi-line strings
  multiline_literal: |
    Line 1
    Line 2
    Line 3
  multiline_folded: >
    This is a very long line
    that will be folded into
    a single line.
  # Special types
  null_value: null
  boolean_true: true
  boolean_false: false
  integer: 42
  float: 3.14159
  scientific: 1.23e-4
  octal: 0o755
  hex: 0xFF
  # Timestamps
  timestamp: 2024-01-01T00:00:00Z
"""
        is_valid, error = validate_yaml_syntax(special_yaml)
        assert is_valid is True