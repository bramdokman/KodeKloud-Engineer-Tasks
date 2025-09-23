"""Unit tests for Kubernetes validator."""

import pytest
from pathlib import Path
from src.kodekloud_tasks.k8s_validator import KubernetesValidator


class TestKubernetesValidator:
    """Test KubernetesValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return KubernetesValidator()

    @pytest.mark.unit
    def test_validate_valid_deployment(self, validator):
        """Test validation of valid Deployment manifest."""
        yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-deployment
  namespace: default
  labels:
    app: webapp
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
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: "500m"
            memory: "256Mi"
          requests:
            cpu: "250m"
            memory: "128Mi"
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["resources"]) == 1
        assert result["resources"][0]["kind"] == "Deployment"

    @pytest.mark.unit
    def test_validate_valid_service(self, validator):
        """Test validation of valid Service manifest."""
        yaml_content = """
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
spec:
  type: LoadBalancer
  selector:
    app: webapp
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["resources"][0]["kind"] == "Service"

    @pytest.mark.unit
    def test_validate_multi_document_yaml(self, validator):
        """Test validation of multi-document YAML."""
        yaml_content = """
apiVersion: v1
kind: Namespace
metadata:
  name: test-ns
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: test-ns
data:
  config.yaml: |
    key: value
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is True
        assert len(result["resources"]) == 2
        assert result["resources"][0]["kind"] == "Namespace"
        assert result["resources"][1]["kind"] == "ConfigMap"

    @pytest.mark.unit
    def test_validate_missing_api_version(self, validator):
        """Test validation with missing apiVersion."""
        yaml_content = """
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: nginx
    image: nginx
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("apiVersion" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_missing_kind(self, validator):
        """Test validation with missing kind."""
        yaml_content = """
apiVersion: v1
metadata:
  name: test-resource
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("kind" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_missing_metadata_name(self, validator):
        """Test validation with missing metadata.name."""
        yaml_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  labels:
    app: test
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("metadata.name" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_deployment_missing_selector(self, validator):
        """Test validation of Deployment with missing selector."""
        yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("selector" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_deployment_invalid_replicas(self, validator):
        """Test validation of Deployment with invalid replicas."""
        yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: -1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("replicas" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_service_missing_ports(self, validator):
        """Test validation of Service with missing ports."""
        yaml_content = """
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  selector:
    app: test
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("ports" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_cronjob(self, validator):
        """Test validation of CronJob manifest."""
        yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            command: ["echo", "Hello World"]
          restartPolicy: OnFailure
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is True
        assert result["resources"][0]["kind"] == "CronJob"

    @pytest.mark.unit
    def test_validate_cronjob_invalid_schedule(self, validator):
        """Test validation of CronJob with invalid schedule."""
        yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "invalid"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("schedule" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_persistent_volume(self, validator):
        """Test validation of PersistentVolume."""
        yaml_content = """
apiVersion: v1
kind: PersistentVolume
metadata:
  name: test-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/data
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is True
        assert result["resources"][0]["kind"] == "PersistentVolume"

    @pytest.mark.unit
    def test_validate_invalid_access_mode(self, validator):
        """Test validation with invalid access mode."""
        yaml_content = """
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes:
    - InvalidMode
  resources:
    requests:
      storage: 1Gi
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("access mode" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_pod_missing_containers(self, validator):
        """Test validation of Pod with missing containers."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  restartPolicy: Always
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("containers" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_container_missing_image(self, validator):
        """Test validation of container with missing image."""
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test-container
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("image" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_invalid_resource_name(self, validator):
        """Test validation with invalid resource name."""
        yaml_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: InvalidName_123
"""
        result = validator.validate_manifest(yaml_content)

        assert result["valid"] is False
        assert any("name" in error for error in result["errors"])

    @pytest.mark.unit
    def test_validate_deprecated_fields(self, validator):
        """Test detection of deprecated fields."""
        yaml_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  rollbackTo:
    revision: 1
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx
"""
        result = validator.validate_manifest(yaml_content)

        assert any("deprecated" in warning.lower() for warning in result["warnings"])

    @pytest.mark.unit
    def test_validate_from_file(self, validator, tmp_path):
        """Test validation from markdown file."""
        content = """# Kubernetes Task

Deploy the following resources:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  key: value
```
"""
        filepath = tmp_path / "k8s_task.md"
        filepath.write_text(content)

        results = validator.validate_from_file(filepath)

        assert len(results) == 2
        assert all(r["valid"] for r in results)
        assert all(r["source_file"] == str(filepath) for r in results)