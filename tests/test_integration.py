"""Integration tests for validating actual task configurations."""

import pytest
from pathlib import Path
from src.config_validator import validate_file, extract_yaml_from_markdown


@pytest.mark.integration
class TestTaskValidation:
    """Integration tests for actual KodeKloud tasks."""

    def get_task_files(self, base_path: Path = None) -> list:
        """Get all markdown task files."""
        if base_path is None:
            base_path = Path(__file__).parent.parent

        task_files = []
        for category in ['Kubernetes', 'Docker', 'Ansible', 'Git', 'Puppet']:
            category_path = base_path / category
            if category_path.exists():
                task_files.extend(list(category_path.glob('*.md')))

        return task_files

    def test_all_kubernetes_tasks_valid_yaml_syntax(self):
        """Test that all Kubernetes tasks have valid YAML syntax."""
        base_path = Path(__file__).parent.parent
        kubernetes_path = base_path / 'Kubernetes'

        if not kubernetes_path.exists():
            pytest.skip("Kubernetes directory not found")

        task_files = list(kubernetes_path.glob('*.md'))
        errors = []

        for task_file in task_files:
            try:
                content = task_file.read_text(encoding='utf-8')
                yaml_blocks = extract_yaml_from_markdown(content)

                for i, yaml_content in enumerate(yaml_blocks):
                    try:
                        from src.config_validator import KubernetesValidator
                        KubernetesValidator.validate_yaml_syntax(yaml_content)
                    except Exception as e:
                        errors.append(f"{task_file.name} - YAML block {i+1}: {e}")

            except Exception as e:
                errors.append(f"{task_file.name}: {e}")

        if errors:
            pytest.fail(f"YAML syntax errors found:\n" + "\n".join(errors))

    def test_kubernetes_cronjob_task_validation(self):
        """Test specific CronJob task validation."""
        base_path = Path(__file__).parent.parent
        cronjob_file = base_path / 'Kubernetes' / 'Create Cronjobs in Kubernetes.md'

        if not cronjob_file.exists():
            pytest.skip("CronJob task file not found")

        result = validate_file(cronjob_file)

        # Should have at least one YAML block
        assert result['yaml_blocks'] > 0, "No YAML blocks found in CronJob task"

        # Check for common issues
        content = cronjob_file.read_text(encoding='utf-8')
        yaml_blocks = extract_yaml_from_markdown(content)

        for yaml_content in yaml_blocks:
            # Check for proper cron schedule format
            if 'schedule:' in yaml_content:
                assert '*/12 * * * *' in yaml_content or '"*/12 * * * *"' in yaml_content, \
                    "CronJob should have proper schedule format"

            # Check for proper image specification
            if 'image:' in yaml_content:
                assert 'nginx:latest' in yaml_content, \
                    "Should use nginx:latest image as specified"

    def test_kubernetes_resource_types_coverage(self):
        """Test that we cover various Kubernetes resource types."""
        base_path = Path(__file__).parent.parent
        kubernetes_path = base_path / 'Kubernetes'

        if not kubernetes_path.exists():
            pytest.skip("Kubernetes directory not found")

        resource_types_found = set()
        task_files = list(kubernetes_path.glob('*.md'))

        for task_file in task_files:
            content = task_file.read_text(encoding='utf-8')
            yaml_blocks = extract_yaml_from_markdown(content)

            for yaml_content in yaml_blocks:
                if 'kind:' in yaml_content:
                    for line in yaml_content.split('\n'):
                        if line.strip().startswith('kind:'):
                            kind = line.split(':')[1].strip()
                            resource_types_found.add(kind)

        # Should have multiple resource types
        assert len(resource_types_found) > 0, "No Kubernetes resources found"

        expected_types = ['CronJob', 'Deployment', 'Service', 'ConfigMap', 'Secret']
        found_expected = resource_types_found.intersection(expected_types)
        assert len(found_expected) > 0, f"No expected resource types found. Found: {resource_types_found}"

    def test_docker_tasks_validation(self):
        """Test Docker tasks validation."""
        base_path = Path(__file__).parent.parent
        docker_path = base_path / 'Docker'

        if not docker_path.exists():
            pytest.skip("Docker directory not found")

        task_files = list(docker_path.glob('*.md'))
        dockerfile_patterns = []

        for task_file in task_files:
            content = task_file.read_text(encoding='utf-8')

            # Look for Dockerfile content patterns
            if 'FROM' in content.upper():
                dockerfile_patterns.append(task_file.name)

        # Should have at least some Docker-related content
        assert len(task_files) > 0 or len(dockerfile_patterns) > 0, \
            "No Docker tasks or Dockerfile patterns found"

    def test_ansible_tasks_validation(self):
        """Test Ansible tasks validation."""
        base_path = Path(__file__).parent.parent
        ansible_path = base_path / 'Ansible'

        if not ansible_path.exists():
            pytest.skip("Ansible directory not found")

        task_files = list(ansible_path.glob('*.md'))
        playbook_patterns = []

        for task_file in task_files:
            content = task_file.read_text(encoding='utf-8')

            # Look for Ansible playbook patterns
            if any(keyword in content.lower() for keyword in ['hosts:', 'tasks:', 'playbook']):
                playbook_patterns.append(task_file.name)

        # Should have at least some Ansible-related content
        assert len(task_files) > 0 or len(playbook_patterns) > 0, \
            "No Ansible tasks or playbook patterns found"

    @pytest.mark.parametrize("category", ["Kubernetes", "Docker", "Ansible", "Git", "Puppet"])
    def test_category_has_content(self, category):
        """Test that each category has actual content."""
        base_path = Path(__file__).parent.parent
        category_path = base_path / category

        if not category_path.exists():
            pytest.skip(f"{category} directory not found")

        task_files = list(category_path.glob('*.md'))
        assert len(task_files) > 0, f"No markdown files found in {category} directory"

        # Check that files have actual content
        non_empty_files = 0
        for task_file in task_files:
            content = task_file.read_text(encoding='utf-8')
            if len(content.strip()) > 100:  # Reasonable content threshold
                non_empty_files += 1

        assert non_empty_files > 0, f"No substantial content found in {category} files"

    def test_image_references_are_valid(self):
        """Test that Docker image references follow proper format."""
        base_path = Path(__file__).parent.parent
        kubernetes_path = base_path / 'Kubernetes'

        if not kubernetes_path.exists():
            pytest.skip("Kubernetes directory not found")

        task_files = list(kubernetes_path.glob('*.md'))
        invalid_images = []

        for task_file in task_files:
            content = task_file.read_text(encoding='utf-8')
            yaml_blocks = extract_yaml_from_markdown(content)

            for yaml_content in yaml_blocks:
                lines = yaml_content.split('\n')
                for line in lines:
                    if 'image:' in line and not line.strip().startswith('#'):
                        image_part = line.split('image:')[1].strip()
                        # Remove quotes if present
                        image_part = image_part.strip('"\'')

                        # Basic validation - should not be empty and should have reasonable format
                        if not image_part or ' ' in image_part:
                            invalid_images.append(f"{task_file.name}: {image_part}")

        if invalid_images:
            pytest.fail(f"Invalid image references found:\n" + "\n".join(invalid_images))

    def test_cron_schedules_are_valid(self):
        """Test that cron schedules in CronJob tasks are valid."""
        base_path = Path(__file__).parent.parent
        kubernetes_path = base_path / 'Kubernetes'

        if not kubernetes_path.exists():
            pytest.skip("Kubernetes directory not found")

        task_files = list(kubernetes_path.glob('*.md'))
        invalid_schedules = []

        for task_file in task_files:
            content = task_file.read_text(encoding='utf-8')
            yaml_blocks = extract_yaml_from_markdown(content)

            for yaml_content in yaml_blocks:
                if 'kind: CronJob' in yaml_content or 'kind:CronJob' in yaml_content:
                    lines = yaml_content.split('\n')
                    for line in lines:
                        if 'schedule:' in line and not line.strip().startswith('#'):
                            schedule_part = line.split('schedule:')[1].strip()
                            # Remove quotes if present
                            schedule_part = schedule_part.strip('"\'')

                            # Basic cron validation - should have 5 parts
                            parts = schedule_part.split()
                            if len(parts) != 5:
                                invalid_schedules.append(f"{task_file.name}: {schedule_part}")

        if invalid_schedules:
            pytest.fail(f"Invalid cron schedules found:\n" + "\n".join(invalid_schedules))


@pytest.mark.integration
class TestSystemIntegration:
    """Test system-level integration scenarios."""

    def test_validation_pipeline_performance(self):
        """Test that validation pipeline performs within acceptable limits."""
        import time
        from src.config_validator import validate_file

        base_path = Path(__file__).parent.parent
        kubernetes_path = base_path / 'Kubernetes'

        if not kubernetes_path.exists():
            pytest.skip("Kubernetes directory not found")

        task_files = list(kubernetes_path.glob('*.md'))[:5]  # Test with first 5 files

        start_time = time.time()

        for task_file in task_files:
            validate_file(task_file)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process files reasonably quickly (adjust threshold as needed)
        avg_time_per_file = processing_time / len(task_files) if task_files else 0
        assert avg_time_per_file < 1.0, f"Validation too slow: {avg_time_per_file:.2f}s per file"

    def test_error_handling_robustness(self):
        """Test that error handling is robust across different file types."""
        base_path = Path(__file__).parent.parent

        # Test with README file (should not crash)
        readme_file = base_path / 'README.md'
        if readme_file.exists():
            result = validate_file(readme_file)
            # Should handle gracefully, not crash
            assert isinstance(result, dict)
            assert 'errors' in result
            assert 'valid' in result

    def test_concurrent_validation(self):
        """Test concurrent validation of multiple files."""
        import concurrent.futures
        from src.config_validator import validate_file

        base_path = Path(__file__).parent.parent
        kubernetes_path = base_path / 'Kubernetes'

        if not kubernetes_path.exists():
            pytest.skip("Kubernetes directory not found")

        task_files = list(kubernetes_path.glob('*.md'))[:3]  # Test with first 3 files

        if not task_files:
            pytest.skip("No task files found")

        def validate_single_file(file_path):
            return validate_file(file_path)

        # Test concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(validate_single_file, task_files))

        # All results should be valid dictionaries
        assert len(results) == len(task_files)
        for result in results:
            assert isinstance(result, dict)
            assert 'valid' in result