"""Utility functions for KodeKloud tasks testing."""

import os
import re
import yaml
import json
import markdown
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


def load_markdown_file(filepath: Union[str, Path]) -> str:
    """Load and return content of a markdown file.

    Args:
        filepath: Path to the markdown file

    Returns:
        Content of the markdown file

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Markdown file not found: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading markdown file {filepath}: {e}")


def extract_code_blocks(markdown_content: str, language: Optional[str] = None) -> List[str]:
    """Extract code blocks from markdown content.

    Args:
        markdown_content: Markdown text content
        language: Optional language filter (e.g., 'yaml', 'bash')

    Returns:
        List of code blocks
    """
    pattern = r'```(?:(\w+))?\n(.*?)```'
    matches = re.findall(pattern, markdown_content, re.DOTALL)

    if language:
        return [code for lang, code in matches if lang == language]
    return [code for _, code in matches]


def validate_yaml_syntax(yaml_content: str) -> tuple[bool, Optional[str]]:
    """Validate YAML syntax.

    Args:
        yaml_content: YAML content string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        yaml.safe_load(yaml_content)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)


def validate_json_syntax(json_content: str) -> tuple[bool, Optional[str]]:
    """Validate JSON syntax.

    Args:
        json_content: JSON content string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        json.loads(json_content)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)


def find_all_files(directory: Union[str, Path], pattern: str = "*.md") -> List[Path]:
    """Find all files matching pattern in directory.

    Args:
        directory: Directory to search
        pattern: File pattern to match

    Returns:
        List of file paths
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    return list(directory.rglob(pattern))


def extract_task_metadata(markdown_content: str) -> Dict[str, Any]:
    """Extract metadata from task documentation.

    Args:
        markdown_content: Markdown content

    Returns:
        Dictionary with task metadata
    """
    metadata = {
        "title": None,
        "difficulty": None,
        "category": None,
        "tags": [],
        "has_solution": False,
        "has_commands": False,
        "has_yaml": False,
    }

    # Extract title
    title_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()

    # Check for solution sections
    if re.search(r'##\s+Solution', markdown_content, re.IGNORECASE):
        metadata["has_solution"] = True

    # Check for commands
    if re.search(r'```(?:bash|shell|sh)', markdown_content):
        metadata["has_commands"] = True

    # Check for YAML configurations
    if re.search(r'```(?:yaml|yml)', markdown_content):
        metadata["has_yaml"] = True

    # Extract category from directory structure
    if "Kubernetes" in markdown_content or "kubernetes" in markdown_content.lower():
        metadata["category"] = "Kubernetes"
    elif "Docker" in markdown_content or "docker" in markdown_content.lower():
        metadata["category"] = "Docker"
    elif "Ansible" in markdown_content or "ansible" in markdown_content.lower():
        metadata["category"] = "Ansible"
    elif "Git" in markdown_content or "git" in markdown_content.lower():
        metadata["category"] = "Git"
    elif "Puppet" in markdown_content or "puppet" in markdown_content.lower():
        metadata["category"] = "Puppet"

    return metadata


def validate_kubernetes_resource(yaml_content: str) -> tuple[bool, Optional[str]]:
    """Validate Kubernetes resource definition.

    Args:
        yaml_content: YAML content of K8s resource

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        resource = yaml.safe_load(yaml_content)

        # Basic validation
        if not isinstance(resource, dict):
            return False, "Invalid resource format"

        # Check required fields
        required_fields = ["apiVersion", "kind"]
        for field in required_fields:
            if field not in resource:
                return False, f"Missing required field: {field}"

        # Validate metadata if present
        if "metadata" in resource:
            if not isinstance(resource["metadata"], dict):
                return False, "Invalid metadata format"
            if "name" not in resource["metadata"]:
                return False, "Missing metadata.name"

        return True, None

    except Exception as e:
        return False, str(e)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    return ' '.join(text.split())


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    text1_normalized = normalize_whitespace(text1.lower())
    text2_normalized = normalize_whitespace(text2.lower())

    if not text1_normalized or not text2_normalized:
        return 0.0

    # Simple word-based similarity
    words1 = set(text1_normalized.split())
    words2 = set(text2_normalized.split())

    if not words1 and not words2:
        return 1.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0