"""End-to-end integration tests for complete workflows."""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.kodekloud_tasks.doc_validator import DocumentationValidator
from src.kodekloud_tasks.k8s_validator import KubernetesValidator
from src.kodekloud_tasks.task_parser import TaskParser
from src.kodekloud_tasks.utils import (
    load_markdown_file,
    extract_code_blocks,
    validate_yaml_syntax,
    validate_json_syntax,
)


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def create_complex_project(self, tmp_path):
        """Create a complex project structure for testing."""

        # Create multiple category directories
        categories = {
            "Kubernetes": [
                ("deployment.md", self._create_k8s_deployment_task()),
                ("statefulset.md", self._create_k8s_statefulset_task()),
                ("configmap.md", self._create_k8s_configmap_task()),
                ("network_policy.md", self._create_k8s_network_policy_task()),
            ],
            "Docker": [
                ("multi_stage.md", self._create_docker_multistage_task()),
                ("compose.md", self._create_docker_compose_task()),
            ],
            "Ansible": [
                ("playbook.md", self._create_ansible_playbook_task()),
                ("role.md", self._create_ansible_role_task()),
            ],
            "Git": [
                ("branching.md", self._create_git_branching_task()),
            ],
            "Puppet": [
                ("module.md", self._create_puppet_module_task()),
            ]
        }

        for category, tasks in categories.items():
            cat_dir = tmp_path / category
            cat_dir.mkdir()
            for filename, content in tasks:
                filepath = cat_dir / filename
                filepath.write_text(content)

        # Create a README at root
        readme = tmp_path / "README.md"
        readme.write_text("""# KodeKloud Engineer Tasks

This repository contains various DevOps tasks and solutions.

## Categories
- Kubernetes
- Docker
- Ansible
- Git
- Puppet
""")

        return tmp_path

    def _create_k8s_deployment_task(self):
        """Create a Kubernetes deployment task."""
        return """# Deploy Application with Auto-scaling

## Problem
Deploy a scalable application with horizontal pod autoscaling.

## Requirements
- Create a deployment with resource limits
- Configure HPA for auto-scaling
- Set up readiness and liveness probes
- Use ConfigMap for configuration

## Solution

Create the deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app: webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:1.21
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        envFrom:
        - configMapRef:
            name: webapp-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-config
data:
  APP_ENV: production
  LOG_LEVEL: info
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Deploy the application:

```bash
kubectl apply -f webapp.yaml
kubectl get deployment webapp
kubectl get hpa webapp-hpa
```

## Verification

```bash
# Check deployment status
kubectl rollout status deployment/webapp

# Check HPA metrics
kubectl get hpa webapp-hpa --watch

# Generate load to test auto-scaling
kubectl run -it --rm load-generator --image=busybox /bin/sh
# Inside the pod: while true; do wget -q -O- http://webapp; done
```
"""

    def _create_k8s_statefulset_task(self):
        """Create a Kubernetes StatefulSet task."""
        return """# Deploy Stateful Application

## Problem
Deploy a stateful application with persistent storage.

## Solution

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```
"""

    def _create_k8s_configmap_task(self):
        """Create a Kubernetes ConfigMap task."""
        return """# Configure Application with ConfigMap

## Problem
Create ConfigMaps for application configuration.

## Solution

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database.properties: |
    db.host=mysql.default.svc.cluster.local
    db.port=3306
    db.name=myapp
  application.yaml: |
    server:
      port: 8080
    logging:
      level: INFO
```

```bash
kubectl create configmap app-config --from-file=config/
kubectl describe configmap app-config
```
"""

    def _create_k8s_network_policy_task(self):
        """Create a Kubernetes NetworkPolicy task."""
        return """# Implement Network Security

## Problem
Secure pod-to-pod communication with NetworkPolicy.

## Solution

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-netpol
spec:
  podSelector:
    matchLabels:
      app: webapp
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 3306
```
"""

    def _create_docker_multistage_task(self):
        """Create a Docker multi-stage build task."""
        return """# Multi-stage Docker Build

## Problem
Create an optimized Docker image using multi-stage builds.

## Solution

```dockerfile
# Build stage
FROM golang:1.19 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# Runtime stage
FROM alpine:3.16
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 8080
CMD ["./main"]
```

```bash
docker build -t myapp:latest .
docker run -p 8080:8080 myapp:latest
```
"""

    def _create_docker_compose_task(self):
        """Create a Docker Compose task."""
        return """# Docker Compose Stack

## Problem
Deploy a multi-container application with Docker Compose.

## Solution

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f
```
"""

    def _create_ansible_playbook_task(self):
        """Create an Ansible playbook task."""
        return """# Ansible Configuration Management

## Problem
Configure servers using Ansible playbooks.

## Solution

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  vars:
    http_port: 80
    max_clients: 200

  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present

    - name: Start nginx service
      service:
        name: nginx
        state: started
        enabled: yes

    - name: Configure firewall
      firewalld:
        service: http
        permanent: yes
        state: enabled
```

```bash
ansible-playbook -i inventory.ini playbook.yml
ansible webservers -m ping
```
"""

    def _create_ansible_role_task(self):
        """Create an Ansible role task."""
        return """# Create Ansible Role

## Problem
Create a reusable Ansible role for application deployment.

## Solution

Directory structure:
```
roles/
└── webapp/
    ├── tasks/main.yml
    ├── handlers/main.yml
    ├── templates/
    │   └── nginx.conf.j2
    └── defaults/main.yml
```

```yaml
# tasks/main.yml
---
- name: Install dependencies
  package:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - python3
    - pip

- name: Deploy application
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/sites-available/webapp
  notify: restart nginx
```
"""

    def _create_git_branching_task(self):
        """Create a Git branching task."""
        return """# Git Branching Strategy

## Problem
Implement Git flow branching strategy.

## Solution

```bash
# Create and switch to feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push feature branch
git push origin feature/new-feature

# Create pull request and merge
git checkout main
git pull origin main
git merge feature/new-feature
git push origin main

# Clean up
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```
"""

    def _create_puppet_module_task(self):
        """Create a Puppet module task."""
        return """# Puppet Module Development

## Problem
Create a Puppet module for service configuration.

## Solution

```puppet
class nginx {
  package { 'nginx':
    ensure => installed,
  }

  service { 'nginx':
    ensure  => running,
    enable  => true,
    require => Package['nginx'],
  }

  file { '/etc/nginx/nginx.conf':
    ensure  => present,
    source  => 'puppet:///modules/nginx/nginx.conf',
    notify  => Service['nginx'],
    require => Package['nginx'],
  }
}
```

```bash
puppet apply --modulepath=/etc/puppet/modules -e "include nginx"
puppet module list
```
"""

    @pytest.mark.integration
    def test_complete_project_validation(self, create_complex_project):
        """Test validation of a complete complex project."""
        doc_validator = DocumentationValidator()
        k8s_validator = KubernetesValidator()
        parser = TaskParser()

        # Parse all tasks
        all_tasks = parser.parse_directory(create_complex_project)

        # Validate documents
        doc_results = doc_validator.validate_directory(create_complex_project)

        # Basic assertions
        assert len(all_tasks) > 0
        assert len(doc_results) > 0

        # Check category distribution
        stats = parser.get_statistics()
        assert "Kubernetes" in stats["categories"]
        assert "Docker" in stats["categories"]
        assert stats["total_tasks"] == len(all_tasks)

    @pytest.mark.integration
    def test_cross_category_analysis(self, create_complex_project):
        """Test analysis across different task categories."""
        parser = TaskParser()
        tasks = parser.parse_directory(create_complex_project)

        # Group by category
        categories = {}
        for task in tasks:
            category = task["metadata"]["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(task)

        # Verify each category has specific characteristics
        if "Kubernetes" in categories:
            k8s_tasks = categories["Kubernetes"]
            for task in k8s_tasks:
                assert "Kubernetes" in task["technologies"]
                assert any("kubectl" in cmd or "apiVersion" in str(task["content"])
                          for cmd in task["content"]["commands"])

        if "Docker" in categories:
            docker_tasks = categories["Docker"]
            for task in docker_tasks:
                assert "Docker" in task["technologies"]
                assert any("docker" in cmd.lower()
                          for cmd in task["content"]["commands"])

    @pytest.mark.integration
    def test_validation_report_generation(self, create_complex_project):
        """Test generation of comprehensive validation reports."""
        doc_validator = DocumentationValidator()
        k8s_validator = KubernetesValidator()

        # Validate all files
        results = doc_validator.validate_directory(create_complex_project)

        # Generate report
        report = {
            "summary": doc_validator.get_summary(),
            "details": results,
            "kubernetes_resources": [],
        }

        # Add K8s validation for relevant files
        for result in results:
            if "Kubernetes" in result["filepath"]:
                k8s_results = k8s_validator.validate_from_file(Path(result["filepath"]))
                report["kubernetes_resources"].extend(k8s_results)

        # Verify report structure
        assert "summary" in report
        assert "total_files" in report["summary"]
        assert "validation_rate" in report["summary"]
        assert len(report["details"]) > 0
        if report["kubernetes_resources"]:
            assert all("resources" in r for r in report["kubernetes_resources"])

    @pytest.mark.integration
    def test_incremental_validation(self, create_complex_project):
        """Test incremental validation after file modifications."""
        doc_validator = DocumentationValidator()

        # Initial validation
        initial_results = doc_validator.validate_directory(create_complex_project)
        initial_count = len(initial_results)

        # Add a new file
        new_file = create_complex_project / "Kubernetes" / "new_task.md"
        new_file.write_text("""# New Task

## Problem
New task description

## Solution
Solution here
""")

        # Re-validate
        updated_results = doc_validator.validate_directory(create_complex_project)

        assert len(updated_results) == initial_count + 1

    @pytest.mark.integration
    def test_parallel_validation_simulation(self, create_complex_project):
        """Test simulated parallel validation of multiple files."""
        import concurrent.futures
        from src.kodekloud_tasks.doc_validator import DocumentationValidator

        def validate_file(filepath):
            validator = DocumentationValidator()
            return validator.validate_file(filepath)

        # Get all markdown files
        md_files = list(create_complex_project.rglob("*.md"))

        # Validate in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(validate_file, md_files))

        assert len(results) == len(md_files)
        assert all(r["filepath"] for r in results)

    @pytest.mark.integration
    def test_error_recovery_workflow(self, tmp_path):
        """Test workflow recovery from various error conditions."""
        # Create files with different types of errors
        error_files = {
            "syntax_error.md": """# Task
```yaml
key: value
  bad: indentation
```""",
            "missing_sections.md": """Just some text without proper structure""",
            "invalid_k8s.md": """# K8s Task
```yaml
apiVersion: invalid/v1
kind: NonExistent
metadata:
  name: test
```""",
        }

        for filename, content in error_files.items():
            filepath = tmp_path / filename
            filepath.write_text(content)

        doc_validator = DocumentationValidator()
        k8s_validator = KubernetesValidator()

        # Validate and collect errors
        all_errors = []
        for filepath in tmp_path.glob("*.md"):
            try:
                doc_result = doc_validator.validate_file(filepath)
                if not doc_result["valid"]:
                    all_errors.extend(doc_result["errors"])

                if "k8s" in filepath.name.lower():
                    k8s_results = k8s_validator.validate_from_file(filepath)
                    for r in k8s_results:
                        if not r["valid"]:
                            all_errors.extend(r["errors"])
            except Exception as e:
                all_errors.append(f"Exception in {filepath}: {str(e)}")

        # Should have collected errors but not crashed
        assert len(all_errors) > 0

    @pytest.mark.integration
    @patch('kubernetes.client.ApiClient')
    def test_live_kubernetes_validation(self, mock_k8s_client, create_complex_project):
        """Test validation against a mocked Kubernetes API."""
        mock_k8s_client.return_value = MagicMock()

        k8s_validator = KubernetesValidator()
        k8s_dir = create_complex_project / "Kubernetes"

        for filepath in k8s_dir.glob("*.md"):
            results = k8s_validator.validate_from_file(filepath)
            # Even with mocked client, basic validation should work
            assert isinstance(results, list)

    @pytest.mark.integration
    def test_validation_with_custom_rules(self, create_complex_project):
        """Test validation with custom validation rules."""
        doc_validator = DocumentationValidator()

        # Add custom validation rules
        custom_rules = {
            "require_verification": True,
            "min_requirements": 2,
            "require_code_blocks": True,
        }

        results = []
        for filepath in create_complex_project.rglob("*.md"):
            result = doc_validator.validate_file(filepath)

            # Apply custom rules
            if custom_rules["require_verification"]:
                content = load_markdown_file(filepath)
                if "## Verification" not in content:
                    result["warnings"].append("Missing Verification section")

            if custom_rules["require_code_blocks"]:
                if not result["metadata"].get("has_commands") and \
                   not result["metadata"].get("has_yaml"):
                    result["warnings"].append("No code blocks found")

            results.append(result)

        # Check that custom rules were applied
        warnings_with_custom = [r for r in results if r["warnings"]]
        assert len(warnings_with_custom) > 0

    @pytest.mark.integration
    def test_validation_performance_metrics(self, create_complex_project):
        """Test and measure validation performance."""
        import time

        doc_validator = DocumentationValidator()
        parser = TaskParser()

        # Measure parsing time
        start_time = time.time()
        tasks = parser.parse_directory(create_complex_project)
        parse_time = time.time() - start_time

        # Measure validation time
        start_time = time.time()
        results = doc_validator.validate_directory(create_complex_project)
        validate_time = time.time() - start_time

        # Performance assertions
        files_count = len(list(create_complex_project.rglob("*.md")))

        # Should process at reasonable speed (adjust thresholds as needed)
        assert parse_time < files_count * 0.1  # Max 100ms per file
        assert validate_time < files_count * 0.1  # Max 100ms per file

        # Calculate metrics
        metrics = {
            "total_files": files_count,
            "parse_time": parse_time,
            "validate_time": validate_time,
            "files_per_second_parse": files_count / parse_time if parse_time > 0 else 0,
            "files_per_second_validate": files_count / validate_time if validate_time > 0 else 0,
        }

        # Metrics should be reasonable
        assert metrics["files_per_second_parse"] > 10  # At least 10 files/second
        assert metrics["files_per_second_validate"] > 10