"""Documentation validator for KodeKloud tasks."""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from .utils import load_markdown_file, extract_code_blocks, extract_task_metadata


class DocumentationValidator:
    """Validate documentation files for completeness and correctness."""

    def __init__(self, strict_mode: bool = True):
        """Initialize the documentation validator.

        Args:
            strict_mode: If True, enforce strict validation rules
        """
        self.strict_mode = strict_mode
        self.validation_results: List[Dict[str, Any]] = []

    def validate_file(self, filepath: Path) -> Dict[str, Any]:
        """Validate a single documentation file.

        Args:
            filepath: Path to the markdown file

        Returns:
            Validation results dictionary
        """
        result = {
            "filepath": str(filepath),
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        try:
            content = load_markdown_file(filepath)
            result["metadata"] = extract_task_metadata(content)

            # Check for required sections
            self._check_required_sections(content, result)

            # Validate code blocks
            self._validate_code_blocks(content, result)

            # Check formatting
            self._check_formatting(content, result)

            # Check for broken links
            self._check_links(content, result)

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error processing file: {e}")

        result["valid"] = len(result["errors"]) == 0

        self.validation_results.append(result)
        return result

    def validate_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Validate all documentation files in a directory.

        Args:
            directory: Directory path

        Returns:
            List of validation results
        """
        from .utils import find_all_files

        markdown_files = find_all_files(directory, "*.md")
        results = []

        for filepath in markdown_files:
            if not filepath.name.startswith('.'):
                results.append(self.validate_file(filepath))

        return results

    def _check_required_sections(self, content: str, result: Dict[str, Any]):
        """Check for required sections in documentation."""
        required_sections = ["#", "##"]  # Title and at least one section

        if not re.search(r'^#\s+\S', content, re.MULTILINE):
            result["errors"].append("Missing main title (# Title)")

        if self.strict_mode:
            # Check for specific sections
            recommended_sections = [
                ("Problem", r'##\s+(?:Problem|Task|Description)', False),
                ("Solution", r'##\s+Solution', False),
                ("Commands", r'(?:```bash|```shell|```sh)', False),
            ]

            for section_name, pattern, is_required in recommended_sections:
                if not re.search(pattern, content, re.IGNORECASE):
                    if is_required:
                        result["errors"].append(f"Missing required section: {section_name}")
                    else:
                        result["warnings"].append(f"Missing recommended section: {section_name}")

    def _validate_code_blocks(self, content: str, result: Dict[str, Any]):
        """Validate code blocks in documentation."""
        code_blocks = extract_code_blocks(content)

        if not code_blocks and result["metadata"].get("has_solution"):
            result["warnings"].append("Solution section exists but no code blocks found")

        # Check for language specification
        unspecified_blocks = re.findall(r'```\n[^`]+```', content)
        if unspecified_blocks:
            result["warnings"].append(f"Found {len(unspecified_blocks)} code blocks without language specification")

        # Validate YAML blocks
        yaml_blocks = extract_code_blocks(content, 'yaml') + extract_code_blocks(content, 'yml')
        for yaml_block in yaml_blocks:
            from .utils import validate_yaml_syntax
            is_valid, error = validate_yaml_syntax(yaml_block)
            if not is_valid:
                result["errors"].append(f"Invalid YAML syntax: {error}")

    def _check_formatting(self, content: str, result: Dict[str, Any]):
        """Check documentation formatting."""
        lines = content.split('\n')

        # Check for excessive blank lines
        blank_count = 0
        max_blank = 2
        for i, line in enumerate(lines):
            if not line.strip():
                blank_count += 1
                if blank_count > max_blank:
                    result["warnings"].append(f"Excessive blank lines at line {i + 1}")
            else:
                blank_count = 0

        # Check line length
        max_line_length = 120
        for i, line in enumerate(lines):
            if len(line) > max_line_length and not line.startswith('```'):
                result["warnings"].append(f"Line {i + 1} exceeds {max_line_length} characters")

        # Check for trailing whitespace
        for i, line in enumerate(lines):
            if line != line.rstrip():
                result["warnings"].append(f"Trailing whitespace at line {i + 1}")

    def _check_links(self, content: str, result: Dict[str, Any]):
        """Check for broken or invalid links."""
        # Find all markdown links
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = re.findall(link_pattern, content)

        for text, url in links:
            if not url:
                result["errors"].append(f"Empty link URL for text: {text}")
            elif url.startswith('#'):
                # Internal anchor link - check if anchor exists
                anchor = url[1:].lower().replace(' ', '-')
                if not re.search(rf'#+\s+.*{re.escape(anchor)}', content, re.IGNORECASE):
                    result["warnings"].append(f"Possible broken anchor link: {url}")
            elif not (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
                result["warnings"].append(f"Unusual link format: {url}")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results.

        Returns:
            Summary dictionary
        """
        total = len(self.validation_results)
        valid = sum(1 for r in self.validation_results if r["valid"])
        total_errors = sum(len(r["errors"]) for r in self.validation_results)
        total_warnings = sum(len(r["warnings"]) for r in self.validation_results)

        return {
            "total_files": total,
            "valid_files": valid,
            "invalid_files": total - valid,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "validation_rate": (valid / total * 100) if total > 0 else 0,
        }