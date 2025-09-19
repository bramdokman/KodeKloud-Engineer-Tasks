"""Edge case and error condition tests."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from src.config_validator import (
    KubernetesValidator,
    ValidationError,
    extract_yaml_from_markdown,
    validate_file
)


@pytest.mark.unit
class TestEdgeCasesAndErrors:
    """Test edge cases and error conditions."""

    def test_empty_configuration_validation(self):
        """Test validation with empty configurations."""
        # Empty dict should fail validation
        with pytest.raises(ValidationError, match="Missing required field: kind"):
            KubernetesValidator.validate_kubernetes_resource({})

    def test_null_values_in_configuration(self):
        """Test validation with null values."""
        config = {
            'apiVersion': None,
            'kind': 'CronJob',
            'metadata': {'name': 'test'},
            'spec': {}
        }
        with pytest.raises(ValidationError):
            KubernetesValidator.validate_kubernetes_resource(config)

    def test_malformed_yaml_blocks_in_markdown(self):
        """Test handling of malformed YAML blocks in markdown."""
        malformed_markdown = """
        # Test Document

        ```yaml
        apiVersion: batch/v1
        kind: CronJob
        metadata:
          name: test
        spec:
          invalid: {unclosed brace
        ```
        """

        yaml_blocks = extract_yaml_from_markdown(malformed_markdown)
        assert len(yaml_blocks) == 1

        # Should handle malformed YAML gracefully
        with pytest.raises(ValidationError):
            KubernetesValidator.validate_yaml_syntax(yaml_blocks[0])

    def test_mixed_yaml_and_json_in_markdown(self):
        """Test handling of mixed YAML and JSON in markdown."""
        mixed_content = """
        # Test Document

        ```yaml
        apiVersion: v1
        kind: Service
        metadata:
          name: test-service
        ```

        ```json
        {
          "apiVersion": "v1",
          "kind": "ConfigMap",
          "metadata": {
            "name": "test-config"
          }
        }
        ```

        ```yaml
        apiVersion: batch/v1
        kind: CronJob
        ```
        """

        yaml_blocks = extract_yaml_from_markdown(mixed_content)
        # Should only extract YAML blocks, not JSON
        assert len(yaml_blocks) == 2

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        unicode_config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': 'unicode-test'},
            'data': {
                'message': 'Hello 世界! 🌍',
                'special': 'Special chars: @#$%^&*()',
                'emoji': '🚀💻🔧',
                'multilang': 'English, Español, 中文, العربية'
            }
        }

        # Should handle unicode gracefully
        assert KubernetesValidator.validate_kubernetes_resource(unicode_config) is True

    def test_very_long_field_values(self):
        """Test handling of very long field values."""
        long_value = 'x' * 10000  # 10KB string
        config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': 'long-test'},
            'data': {'long_field': long_value}
        }

        # Should handle long values without issue
        assert KubernetesValidator.validate_kubernetes_resource(config) is True

    def test_deeply_nested_structures(self):
        """Test handling of deeply nested YAML structures."""
        # Create a deeply nested structure
        nested_config = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {'name': 'nested-test'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{
                            'name': 'app',
                            'image': 'nginx:latest',
                            'env': [
                                {
                                    'name': 'COMPLEX_CONFIG',
                                    'valueFrom': {
                                        'configMapKeyRef': {
                                            'name': 'complex-config',
                                            'key': 'nested.value.deep.structure'
                                        }
                                    }
                                }
                            ]
                        }]
                    }
                }
            }
        }

        assert KubernetesValidator.validate_kubernetes_resource(nested_config) is True

    def test_circular_references_protection(self):
        """Test protection against circular references."""
        # YAML safe_load should protect against circular references
        yaml_with_circular_ref = """
        apiVersion: &api_version v1
        kind: ConfigMap
        metadata:
          name: test
        data:
          ref: *api_version
        """

        # Should handle safely without infinite loops
        result = KubernetesValidator.validate_yaml_syntax(yaml_with_circular_ref)
        assert isinstance(result, dict)

    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp_path = tmp.name

        try:
            # Remove read permissions
            os.chmod(tmp_path, 0o000)

            result = validate_file(Path(tmp_path))
            # Should handle permission error gracefully
            assert result['valid'] is False
            assert len(result['errors']) > 0

        finally:
            # Restore permissions and cleanup
            os.chmod(tmp_path, 0o644)
            os.unlink(tmp_path)

    def test_file_encoding_errors(self):
        """Test handling of file encoding errors."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
            # Write invalid UTF-8 bytes
            tmp.write(b'\xff\xfe\x00\x00invalid utf-8')
            tmp_path = tmp.name

        try:
            result = validate_file(Path(tmp_path))
            # Should handle encoding error gracefully
            assert result['valid'] is False
            assert len(result['errors']) > 0

        finally:
            os.unlink(tmp_path)

    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_io_errors(self, mock_file):
        """Test handling of I/O errors."""
        result = validate_file(Path("test.md"))
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_memory_intensive_yaml(self):
        """Test handling of memory-intensive YAML structures."""
        # Create a large config that might stress memory
        large_data = {}
        for i in range(1000):
            large_data[f'key_{i}'] = f'value_{i}' * 100

        config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': 'large-config'},
            'data': large_data
        }

        # Should handle large configs without memory issues
        assert KubernetesValidator.validate_kubernetes_resource(config) is True

    def test_invalid_cron_schedule_edge_cases(self):
        """Test edge cases for cron schedule validation."""
        invalid_schedules = [
            ("", "Cron schedule cannot be empty"),  # Empty
            (" ", "Cron schedule cannot be empty"),  # Whitespace only
            ("* * * * * *", "Expected 5 fields"),  # Too many fields
            ("* * *", "Expected 5 fields"),  # Too few fields
            ("60 * * * *", "Invalid minute field"),  # Invalid minute
            ("* 25 * * *", "Invalid hour field"),  # Invalid hour
            ("* * 32 * *", "Invalid day field"),  # Invalid day
            ("* * * 13 *", "Invalid month field"),  # Invalid month
            ("* * * * 8", "Invalid day of week field"),  # Invalid day of week
            ("invalid * * * *", "Invalid minute field"),  # Non-numeric
            ("*/0 * * * *", "Invalid minute field"),  # Division by zero
        ]

        for schedule, expected_error in invalid_schedules:
            with pytest.raises(ValidationError, match=expected_error):
                KubernetesValidator.validate_cron_schedule(schedule)

    def test_invalid_image_tag_edge_cases(self):
        """Test edge cases for image tag validation."""
        invalid_images = [
            "",  # Empty
            " ",  # Whitespace only
            "INVALID IMAGE NAME",  # Spaces
            "image::",  # Double colons
            "image:",  # Empty tag
            ":tag",  # Empty image name
            "192.168.1.1:5000/",  # Empty image after registry
            "image name with spaces:tag",  # Spaces in name
        ]

        for image in invalid_images:
            with pytest.raises(ValidationError):
                KubernetesValidator.validate_image_tag(image)

    def test_concurrent_validation_stress(self):
        """Stress test concurrent validation."""
        import threading
        import time

        errors = []

        def validate_repeatedly():
            for _ in range(10):
                try:
                    config = {
                        'apiVersion': 'v1',
                        'kind': 'ConfigMap',
                        'metadata': {'name': f'test-{threading.current_thread().ident}'},
                        'data': {'key': 'value'}
                    }
                    KubernetesValidator.validate_kubernetes_resource(config)
                    time.sleep(0.01)  # Small delay
                except Exception as e:
                    errors.append(str(e))

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=validate_repeatedly)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should not have any concurrency-related errors
        assert len(errors) == 0, f"Concurrency errors: {errors}"

    def test_malicious_yaml_protection(self):
        """Test protection against potentially malicious YAML."""
        # YAML that could potentially cause issues
        potentially_malicious = [
            # Extremely deep nesting
            "a: " + "\n  b: " * 1000 + "value",
            # Very long strings
            f"key: {'x' * 100000}",
            # Many keys
            "\n".join([f"key_{i}: value_{i}" for i in range(10000)])
        ]

        for yaml_content in potentially_malicious:
            try:
                # Should either validate successfully or fail gracefully
                KubernetesValidator.validate_yaml_syntax(yaml_content)
            except ValidationError:
                # Expected for malformed content
                pass
            except Exception as e:
                # Should not raise unexpected exceptions
                pytest.fail(f"Unexpected exception for potentially malicious YAML: {e}")

    def test_boundary_values(self):
        """Test boundary values for various validations."""
        # Test minimum valid cron schedule
        assert KubernetesValidator.validate_cron_schedule("0 0 1 1 0") is True

        # Test maximum valid cron schedule
        assert KubernetesValidator.validate_cron_schedule("59 23 31 12 6") is True

        # Test minimum valid image name
        assert KubernetesValidator.validate_image_tag("a") is True

        # Test edge case resource names
        edge_case_configs = [
            {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {'name': 'a'},  # Single character name
                'data': {}
            },
            {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {'name': 'a' * 253},  # Very long name (DNS limit)
                'data': {}
            }
        ]

        for config in edge_case_configs:
            assert KubernetesValidator.validate_kubernetes_resource(config) is True