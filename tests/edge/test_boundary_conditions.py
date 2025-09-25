"""Boundary condition and edge case tests."""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from src.kodekloud_tasks.task_parser import TaskParser
from src.kodekloud_tasks.doc_validator import DocumentationValidator
from src.kodekloud_tasks.k8s_validator import KubernetesValidator
from src.kodekloud_tasks.utils import (
    load_markdown_file,
    extract_code_blocks,
    validate_yaml_syntax,
    validate_json_syntax,
    normalize_whitespace,
    calculate_similarity,
)


class TestBoundaryConditions:
    """Test boundary conditions and extreme edge cases."""

    @pytest.mark.edge
    def test_maximum_file_size_handling(self, tmp_path):
        """Test handling of files at maximum size limits."""
        # Create a file near typical size limits
        large_file = tmp_path / "large.md"

        # 50MB file (adjust based on your limits)
        content = "# Large File\n\n"
        chunk = "x" * 1000 + "\n"

        with open(large_file, 'w') as f:
            f.write(content)
            for _ in range(50000):  # 50MB approximately
                f.write(chunk)

        parser = TaskParser()
        # Should handle large file without crashing
        result = parser.parse_task(large_file)
        assert result is not None

    @pytest.mark.edge
    def test_minimum_valid_content(self, tmp_path):
        """Test minimum content required for valid task."""
        minimal_file = tmp_path / "minimal.md"
        minimal_file.write_text("# T")  # Shortest possible title

        doc_validator = DocumentationValidator()
        result = doc_validator.validate_file(minimal_file)

        # Should be valid but with warnings
        assert result["metadata"]["title"] == "T"

    @pytest.mark.edge
    def test_resource_exhaustion_protection(self, tmp_path):
        """Test protection against resource exhaustion attacks."""
        # Create a file with excessive nesting
        nested_yaml = "a:\n"
        for i in range(1000):
            nested_yaml += "  " * i + f"level{i}:\n"

        malicious_file = tmp_path / "malicious.md"
        malicious_file.write_text(f"""# Task
```yaml
{nested_yaml}
```""")

        parser = TaskParser()
        # Should handle without stack overflow
        result = parser.parse_task(malicious_file)
        assert result is not None

    @pytest.mark.edge
    def test_special_filesystem_characters(self, tmp_path):
        """Test handling of special characters in filenames."""
        special_chars = ['@', '#', '$', '%', '^', '&', '(', ')', '[', ']', '{', '}']

        for char in special_chars:
            if char not in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:  # Invalid path chars
                filename = f"task{char}test.md"
                filepath = tmp_path / filename
                filepath.write_text(f"# Task with {char}")

                doc_validator = DocumentationValidator()
                result = doc_validator.validate_file(filepath)
                assert result["filepath"] == str(filepath)

    @pytest.mark.edge
    def test_concurrent_modifications(self, tmp_path):
        """Test handling of files being modified during processing."""
        test_file = tmp_path / "concurrent.md"
        test_file.write_text("# Initial Content")

        doc_validator = DocumentationValidator()

        # Simulate file modification during read
        with patch('builtins.open', side_effect=[
            mock_open(read_data="# Initial Content")(),
            mock_open(read_data="# Modified Content")()
        ]):
            result1 = doc_validator.validate_file(test_file)
            result2 = doc_validator.validate_file(test_file)

            # Should handle gracefully
            assert result1 is not None
            assert result2 is not None

    @pytest.mark.edge
    def test_zero_byte_files(self, tmp_path):
        """Test handling of zero-byte files."""
        empty_file = tmp_path / "empty.md"
        empty_file.touch()  # Creates zero-byte file

        doc_validator = DocumentationValidator()
        result = doc_validator.validate_file(empty_file)

        assert result["valid"] is False
        assert "empty" in str(result["errors"]).lower()

    @pytest.mark.edge
    def test_symlink_handling(self, tmp_path):
        """Test handling of symbolic links."""
        if sys.platform != "win32":  # Skip on Windows
            real_file = tmp_path / "real.md"
            real_file.write_text("# Real File")

            symlink = tmp_path / "link.md"
            symlink.symlink_to(real_file)

            doc_validator = DocumentationValidator()
            result = doc_validator.validate_file(symlink)

            assert result["metadata"]["title"] == "Real File"

    @pytest.mark.edge
    def test_circular_symlinks(self, tmp_path):
        """Test handling of circular symbolic links."""
        if sys.platform != "win32":  # Skip on Windows
            link1 = tmp_path / "link1.md"
            link2 = tmp_path / "link2.md"

            # Create circular symlinks
            link1.symlink_to(link2)
            link2.symlink_to(link1)

            doc_validator = DocumentationValidator()
            with pytest.raises((OSError, IOError)):
                doc_validator.validate_file(link1)

    @pytest.mark.edge
    def test_permission_denied_handling(self, tmp_path):
        """Test handling of permission denied errors."""
        if sys.platform != "win32":  # Unix-specific test
            restricted_file = tmp_path / "restricted.md"
            restricted_file.write_text("# Restricted")
            restricted_file.chmod(0o000)

            try:
                doc_validator = DocumentationValidator()
                with pytest.raises((PermissionError, IOError)):
                    doc_validator.validate_file(restricted_file)
            finally:
                restricted_file.chmod(0o644)  # Restore permissions for cleanup

    @pytest.mark.edge
    def test_memory_stress_with_many_small_files(self, tmp_path):
        """Test memory handling with many small files."""
        # Create 1000 small files
        for i in range(1000):
            small_file = tmp_path / f"small_{i}.md"
            small_file.write_text(f"# Task {i}\nContent {i}")

        doc_validator = DocumentationValidator()
        results = doc_validator.validate_directory(tmp_path)

        assert len(results) == 1000
        # Memory should not grow excessively

    @pytest.mark.edge
    def test_deeply_nested_markdown_structure(self, tmp_path):
        """Test handling of deeply nested markdown headings."""
        deep_markdown = "# Level 1\n"
        for i in range(2, 10):
            deep_markdown += "#" * min(i, 6) + f" Level {i}\n"
            deep_markdown += f"Content at level {i}\n\n"

        deep_file = tmp_path / "deep.md"
        deep_file.write_text(deep_markdown)

        parser = TaskParser()
        result = parser.parse_task(deep_file)

        assert result["metadata"]["title"] == "Level 1"
        assert result["content"]["sections"] is not None

    @pytest.mark.edge
    def test_mixed_encoding_files(self, tmp_path):
        """Test handling of files with mixed encodings."""
        encodings = ['utf-8', 'latin-1', 'ascii']

        for encoding in encodings:
            try:
                encoded_file = tmp_path / f"{encoding}_file.md"
                content = f"# File in {encoding}\nContent"
                encoded_file.write_text(content, encoding=encoding)

                doc_validator = DocumentationValidator()
                result = doc_validator.validate_file(encoded_file)
                assert result is not None
            except UnicodeEncodeError:
                pass  # Some encodings might not support all characters

    @pytest.mark.edge
    def test_infinite_loop_prevention(self):
        """Test prevention of infinite loops in parsing."""
        # Create content that might cause infinite loops
        circular_content = """# Task

```yaml
anchor: &ref
  key: *ref  # Circular reference
```"""

        # Should handle without infinite loop
        is_valid, error = validate_yaml_syntax(circular_content)
        # YAML might be invalid but shouldn't hang
        assert isinstance(is_valid, bool)

    @pytest.mark.edge
    def test_maximum_nesting_depth(self):
        """Test maximum nesting depth in various structures."""
        # Test YAML nesting limit
        max_depth = 100
        yaml_content = ""
        for i in range(max_depth):
            yaml_content = f"level{i}:\n  " + yaml_content
        yaml_content += "value: deepest"

        is_valid, error = validate_yaml_syntax(yaml_content)
        # Should handle deep nesting
        assert isinstance(is_valid, bool)

    @pytest.mark.edge
    def test_code_block_edge_cases(self):
        """Test edge cases in code block extraction."""
        edge_cases = [
            # Nested code blocks
            "````markdown\n```python\nprint('nested')\n```\n````",
            # Unclosed code block
            "```python\nprint('unclosed')",
            # Empty language specification
            "```\ncode without language\n```",
            # Code block with special characters
            "```bash\nrm -rf / # Don't run this!\n```",
            # Multiple code blocks without separation
            "```python\ncode1\n``````bash\ncode2\n```",
        ]

        for content in edge_cases:
            blocks = extract_code_blocks(content)
            # Should handle without crashing
            assert isinstance(blocks, list)

    @pytest.mark.edge
    def test_similarity_calculation_edge_cases(self):
        """Test edge cases in similarity calculation."""
        edge_cases = [
            ("", "", 1.0),  # Empty strings
            ("a", "a", 1.0),  # Single character
            ("abc", "xyz", 0.0),  # Completely different
            ("  spaces  ", "spaces", None),  # Whitespace differences
            ("UPPERCASE", "uppercase", None),  # Case differences
            ("a" * 10000, "a" * 10001, None),  # Very long strings
        ]

        for text1, text2, expected in edge_cases:
            similarity = calculate_similarity(text1, text2)
            assert 0.0 <= similarity <= 1.0
            if expected is not None:
                assert similarity == expected

    @pytest.mark.edge
    def test_yaml_bomb_protection(self):
        """Test protection against YAML bombs (billion laughs attack)."""
        yaml_bomb = """
a: &a ["lol", "lol", "lol", "lol", "lol"]
b: &b [*a, *a, *a, *a, *a]
c: &c [*b, *b, *b, *b, *b]
d: &d [*c, *c, *c, *c, *c]
e: &e [*d, *d, *d, *d, *d]
"""

        # Should handle without memory explosion
        is_valid, error = validate_yaml_syntax(yaml_bomb)
        assert isinstance(is_valid, bool)

    @pytest.mark.edge
    def test_json_edge_cases(self):
        """Test JSON validation edge cases."""
        json_cases = [
            ('{}', True),  # Empty object
            ('[]', True),  # Empty array
            ('null', True),  # Null value
            ('true', True),  # Boolean
            ('123', True),  # Number
            ('"string"', True),  # String
            ('{"key": null}', True),  # Null value in object
            ('{"key": "\\u0000"}', True),  # Unicode escape
            ('{"key": 1e308}', True),  # Large number
            ('{"key": -1e308}', True),  # Large negative number
            ('{key: "value"}', False),  # Unquoted key
            ("{'key': 'value'}", False),  # Single quotes
            ('{"key": undefined}', False),  # Undefined value
        ]

        for json_str, expected_valid in json_cases:
            is_valid, error = validate_json_syntax(json_str)
            assert is_valid == expected_valid

    @pytest.mark.edge
    def test_whitespace_normalization_edge_cases(self):
        """Test whitespace normalization edge cases."""
        cases = [
            ("", ""),  # Empty string
            ("   ", " "),  # Only spaces
            ("\t\n\r", " "),  # Only whitespace characters
            ("no  extra", "no extra"),  # Internal spaces
            ("  leading", " leading"),  # Leading spaces
            ("trailing  ", "trailing "),  # Trailing spaces
            ("line\nbreak", "line break"),  # Line breaks
            ("tab\there", "tab here"),  # Tabs
            ("multiple\n\n\nlines", "multiple lines"),  # Multiple line breaks
        ]

        for input_text, expected in cases:
            result = normalize_whitespace(input_text)
            assert result == expected

    @pytest.mark.edge
    def test_kubernetes_resource_name_validation(self):
        """Test Kubernetes resource name validation edge cases."""
        validator = KubernetesValidator()

        name_cases = [
            ("valid-name", True),
            ("valid.name", True),
            ("123-starts-with-number", True),
            ("a", True),  # Single character
            ("a" * 63, True),  # Maximum length
            ("a" * 64, False),  # Too long
            ("Capital-Name", False),  # Capital letters
            ("name_with_underscore", False),  # Underscore
            ("name-", False),  # Ends with dash
            ("-name", False),  # Starts with dash
            ("name..dots", False),  # Consecutive dots
            ("", False),  # Empty name
        ]

        for name, expected_valid in name_cases:
            yaml_content = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {name}
data:
  key: value
"""
            result = validator.validate_manifest(yaml_content)
            if expected_valid:
                assert result["valid"] is True or "name" not in str(result["errors"])
            else:
                assert result["valid"] is False or "name" in str(result["warnings"])

    @pytest.mark.edge
    def test_race_condition_in_directory_validation(self, tmp_path):
        """Test handling of race conditions during directory validation."""
        import threading

        # Create initial files
        for i in range(10):
            file = tmp_path / f"file{i}.md"
            file.write_text(f"# File {i}")

        doc_validator = DocumentationValidator()

        def modify_files():
            """Modify files during validation."""
            for i in range(10):
                file = tmp_path / f"file{i}.md"
                file.write_text(f"# Modified File {i}")

        # Start validation and modification concurrently
        modifier_thread = threading.Thread(target=modify_files)
        modifier_thread.start()

        results = doc_validator.validate_directory(tmp_path)

        modifier_thread.join()

        # Should complete without errors
        assert len(results) == 10