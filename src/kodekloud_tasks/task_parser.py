"""Task parser for extracting and analyzing KodeKloud tasks."""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .utils import load_markdown_file, extract_code_blocks, extract_task_metadata


class TaskParser:
    """Parse and analyze KodeKloud task documentation."""

    def __init__(self):
        """Initialize the task parser."""
        self.parsed_tasks: List[Dict[str, Any]] = []

    def parse_task(self, filepath: Path) -> Dict[str, Any]:
        """Parse a single task file.

        Args:
            filepath: Path to the task markdown file

        Returns:
            Parsed task information
        """
        content = load_markdown_file(filepath)

        task_info = {
            "filepath": str(filepath),
            "metadata": extract_task_metadata(content),
            "content": {
                "raw": content,
                "sections": self._extract_sections(content),
                "code_blocks": self._extract_all_code_blocks(content),
                "commands": self._extract_commands(content),
                "configurations": self._extract_configurations(content),
            },
            "requirements": self._extract_requirements(content),
            "solution": self._extract_solution(content),
            "difficulty": self._estimate_difficulty(content),
            "technologies": self._extract_technologies(content),
        }

        self.parsed_tasks.append(task_info)
        return task_info

    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all task files in a directory.

        Args:
            directory: Directory containing task files

        Returns:
            List of parsed tasks
        """
        from .utils import find_all_files

        task_files = find_all_files(directory, "*.md")
        tasks = []

        for filepath in task_files:
            if not filepath.name.startswith('.'):
                tasks.append(self.parse_task(filepath))

        return tasks

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract markdown sections from content."""
        sections = {}
        current_section = "intro"
        current_content = []

        for line in content.split('\n'):
            if line.startswith('## '):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = line[3:].strip().lower().replace(' ', '_')
                current_content = []
            elif line.startswith('# '):
                sections["title"] = line[2:].strip()
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _extract_all_code_blocks(self, content: str) -> Dict[str, List[str]]:
        """Extract all code blocks categorized by language."""
        code_blocks = {}

        # Find all code blocks with language specification
        pattern = r'```(\w+)\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)

        for language, code in matches:
            if language not in code_blocks:
                code_blocks[language] = []
            code_blocks[language].append(code.strip())

        return code_blocks

    def _extract_commands(self, content: str) -> List[str]:
        """Extract shell commands from the content."""
        commands = []

        # Extract from bash/shell code blocks
        bash_blocks = extract_code_blocks(content, 'bash')
        bash_blocks.extend(extract_code_blocks(content, 'sh'))
        bash_blocks.extend(extract_code_blocks(content, 'shell'))

        for block in bash_blocks:
            # Split multi-line commands
            lines = block.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    commands.append(line)

        # Also look for inline code that might be commands
        inline_pattern = r'`([^`]+)`'
        inline_matches = re.findall(inline_pattern, content)

        for match in inline_matches:
            # Check if it looks like a command
            if any(match.startswith(cmd) for cmd in ['kubectl', 'docker', 'git', 'ansible', 'puppet']):
                commands.append(match)

        return commands

    def _extract_configurations(self, content: str) -> Dict[str, Any]:
        """Extract configuration examples from the content."""
        configs = {
            "kubernetes": [],
            "docker": [],
            "ansible": [],
            "puppet": [],
            "other": [],
        }

        # Extract Kubernetes YAML configurations
        yaml_blocks = extract_code_blocks(content, 'yaml')
        yaml_blocks.extend(extract_code_blocks(content, 'yml'))

        for block in yaml_blocks:
            if any(keyword in block.lower() for keyword in ['apiversion', 'kind:', 'metadata:']):
                configs["kubernetes"].append(block)
            elif 'docker' in block.lower():
                configs["docker"].append(block)
            elif 'ansible' in block.lower() or 'playbook' in block.lower():
                configs["ansible"].append(block)
            elif 'puppet' in block.lower() or 'class {' in block:
                configs["puppet"].append(block)
            else:
                configs["other"].append(block)

        # Extract JSON configurations
        json_blocks = extract_code_blocks(content, 'json')
        configs["other"].extend(json_blocks)

        return configs

    def _extract_requirements(self, content: str) -> List[str]:
        """Extract requirements from the task."""
        requirements = []

        # Look for requirements section
        req_pattern = r'##\s*(?:Requirements?|Prerequisites?|Objectives?)(.*?)(?=##|\Z)'
        req_match = re.search(req_pattern, content, re.IGNORECASE | re.DOTALL)

        if req_match:
            req_content = req_match.group(1)

            # Extract bullet points or numbered items
            item_pattern = r'(?:^|\n)\s*[-*•]\s*(.+?)(?=\n|$)'
            items = re.findall(item_pattern, req_content)
            requirements.extend(items)

            # Also look for numbered items
            num_pattern = r'(?:^|\n)\s*\d+\.\s*(.+?)(?=\n|$)'
            num_items = re.findall(num_pattern, req_content)
            requirements.extend(num_items)

        return [req.strip() for req in requirements if req.strip()]

    def _extract_solution(self, content: str) -> Optional[str]:
        """Extract solution section from the task."""
        sol_pattern = r'##\s*Solution(.*?)(?=##|\Z)'
        sol_match = re.search(sol_pattern, content, re.IGNORECASE | re.DOTALL)

        if sol_match:
            return sol_match.group(1).strip()
        return None

    def _estimate_difficulty(self, content: str) -> str:
        """Estimate task difficulty based on content analysis."""
        score = 0

        # Check content length
        if len(content) > 5000:
            score += 2
        elif len(content) > 2000:
            score += 1

        # Check number of code blocks
        code_blocks = extract_code_blocks(content)
        if len(code_blocks) > 5:
            score += 2
        elif len(code_blocks) > 2:
            score += 1

        # Check for complex keywords
        complex_keywords = [
            'advanced', 'complex', 'multi-node', 'cluster', 'high availability',
            'security', 'rbac', 'performance', 'optimization', 'troubleshoot'
        ]
        for keyword in complex_keywords:
            if keyword in content.lower():
                score += 1

        # Determine difficulty level
        if score >= 6:
            return "advanced"
        elif score >= 3:
            return "intermediate"
        else:
            return "beginner"

    def _extract_technologies(self, content: str) -> List[str]:
        """Extract technologies mentioned in the task."""
        technologies = set()

        tech_patterns = {
            "Kubernetes": r'\b(?:kubernetes|k8s|kubectl)\b',
            "Docker": r'\b(?:docker|dockerfile|container)\b',
            "Ansible": r'\b(?:ansible|playbook)\b',
            "Git": r'\b(?:git|github|gitlab)\b',
            "Puppet": r'\b(?:puppet)\b',
            "Jenkins": r'\b(?:jenkins)\b',
            "Nginx": r'\b(?:nginx)\b',
            "Apache": r'\b(?:apache|httpd)\b',
            "MySQL": r'\b(?:mysql)\b',
            "PostgreSQL": r'\b(?:postgresql|postgres)\b',
            "Redis": r'\b(?:redis)\b',
            "MongoDB": r'\b(?:mongodb|mongo)\b',
            "Prometheus": r'\b(?:prometheus)\b',
            "Grafana": r'\b(?:grafana)\b',
            "Terraform": r'\b(?:terraform)\b',
            "AWS": r'\b(?:aws|amazon web services)\b',
            "GCP": r'\b(?:gcp|google cloud)\b',
            "Azure": r'\b(?:azure)\b',
        }

        for tech, pattern in tech_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                technologies.add(tech)

        return sorted(list(technologies))

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed tasks.

        Returns:
            Statistics dictionary
        """
        if not self.parsed_tasks:
            return {}

        total = len(self.parsed_tasks)
        categories = {}
        difficulties = {"beginner": 0, "intermediate": 0, "advanced": 0}
        technologies = {}

        for task in self.parsed_tasks:
            # Count categories
            category = task["metadata"].get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1

            # Count difficulties
            difficulty = task.get("difficulty", "unknown")
            if difficulty in difficulties:
                difficulties[difficulty] += 1

            # Count technologies
            for tech in task.get("technologies", []):
                technologies[tech] = technologies.get(tech, 0) + 1

        return {
            "total_tasks": total,
            "categories": categories,
            "difficulties": difficulties,
            "technologies": technologies,
            "avg_commands_per_task": sum(
                len(task["content"]["commands"]) for task in self.parsed_tasks
            ) / total if total > 0 else 0,
            "tasks_with_solutions": sum(
                1 for task in self.parsed_tasks if task["solution"]
            ),
        }