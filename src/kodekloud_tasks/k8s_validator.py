"""Kubernetes configuration validator for KodeKloud tasks."""

import yaml
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .utils import extract_code_blocks, validate_kubernetes_resource


class KubernetesValidator:
    """Validate Kubernetes configurations and manifests."""

    REQUIRED_FIELDS = {
        "Deployment": ["apiVersion", "kind", "metadata", "spec"],
        "Service": ["apiVersion", "kind", "metadata", "spec"],
        "Pod": ["apiVersion", "kind", "metadata", "spec"],
        "ConfigMap": ["apiVersion", "kind", "metadata"],
        "Secret": ["apiVersion", "kind", "metadata"],
        "PersistentVolume": ["apiVersion", "kind", "metadata", "spec"],
        "PersistentVolumeClaim": ["apiVersion", "kind", "metadata", "spec"],
        "Namespace": ["apiVersion", "kind", "metadata"],
        "ServiceAccount": ["apiVersion", "kind", "metadata"],
        "Role": ["apiVersion", "kind", "metadata", "rules"],
        "RoleBinding": ["apiVersion", "kind", "metadata", "roleRef", "subjects"],
        "ClusterRole": ["apiVersion", "kind", "metadata", "rules"],
        "ClusterRoleBinding": ["apiVersion", "kind", "metadata", "roleRef", "subjects"],
        "Ingress": ["apiVersion", "kind", "metadata", "spec"],
        "Job": ["apiVersion", "kind", "metadata", "spec"],
        "CronJob": ["apiVersion", "kind", "metadata", "spec"],
        "StatefulSet": ["apiVersion", "kind", "metadata", "spec"],
        "DaemonSet": ["apiVersion", "kind", "metadata", "spec"],
        "ReplicaSet": ["apiVersion", "kind", "metadata", "spec"],
        "ReplicationController": ["apiVersion", "kind", "metadata", "spec"],
    }

    VALID_API_VERSIONS = {
        "Deployment": ["apps/v1", "apps/v1beta1", "apps/v1beta2"],
        "Service": ["v1"],
        "Pod": ["v1"],
        "ConfigMap": ["v1"],
        "Secret": ["v1"],
        "PersistentVolume": ["v1"],
        "PersistentVolumeClaim": ["v1"],
        "Namespace": ["v1"],
        "ServiceAccount": ["v1"],
        "Role": ["rbac.authorization.k8s.io/v1"],
        "RoleBinding": ["rbac.authorization.k8s.io/v1"],
        "ClusterRole": ["rbac.authorization.k8s.io/v1"],
        "ClusterRoleBinding": ["rbac.authorization.k8s.io/v1"],
        "Ingress": ["networking.k8s.io/v1", "networking.k8s.io/v1beta1"],
        "Job": ["batch/v1"],
        "CronJob": ["batch/v1", "batch/v1beta1"],
        "StatefulSet": ["apps/v1"],
        "DaemonSet": ["apps/v1"],
        "ReplicaSet": ["apps/v1"],
        "ReplicationController": ["v1"],
    }

    def __init__(self):
        """Initialize the Kubernetes validator."""
        self.validation_results: List[Dict[str, Any]] = []

    def validate_manifest(self, yaml_content: str) -> Dict[str, Any]:
        """Validate a Kubernetes manifest.

        Args:
            yaml_content: YAML content of the manifest

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "resources": [],
        }

        try:
            # Parse YAML (could be multi-document)
            documents = list(yaml.safe_load_all(yaml_content))

            for doc in documents:
                if doc:
                    resource_result = self._validate_resource(doc)
                    result["resources"].append(resource_result)

                    if resource_result["errors"]:
                        result["errors"].extend(resource_result["errors"])
                        result["valid"] = False

                    if resource_result["warnings"]:
                        result["warnings"].extend(resource_result["warnings"])

        except yaml.YAMLError as e:
            result["valid"] = False
            result["errors"].append(f"YAML parsing error: {e}")

        self.validation_results.append(result)
        return result

    def _validate_resource(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single Kubernetes resource.

        Args:
            resource: Kubernetes resource dictionary

        Returns:
            Validation result for the resource
        """
        result = {
            "kind": resource.get("kind", "Unknown"),
            "name": resource.get("metadata", {}).get("name", "Unnamed"),
            "errors": [],
            "warnings": [],
        }

        # Check kind
        kind = resource.get("kind")
        if not kind:
            result["errors"].append("Missing 'kind' field")
            return result

        # Check API version
        api_version = resource.get("apiVersion")
        if not api_version:
            result["errors"].append("Missing 'apiVersion' field")
        elif kind in self.VALID_API_VERSIONS:
            if api_version not in self.VALID_API_VERSIONS[kind]:
                result["warnings"].append(
                    f"Unusual API version '{api_version}' for {kind}. "
                    f"Expected one of: {', '.join(self.VALID_API_VERSIONS[kind])}"
                )

        # Check required fields
        if kind in self.REQUIRED_FIELDS:
            for field in self.REQUIRED_FIELDS[kind]:
                if field not in resource:
                    result["errors"].append(f"Missing required field '{field}' for {kind}")

        # Validate metadata
        self._validate_metadata(resource.get("metadata", {}), result)

        # Validate spec based on kind
        if "spec" in resource:
            self._validate_spec(kind, resource["spec"], result)

        # Check for deprecated fields
        self._check_deprecated_fields(kind, resource, result)

        return result

    def _validate_metadata(self, metadata: Dict[str, Any], result: Dict[str, Any]):
        """Validate metadata section."""
        if not metadata:
            result["errors"].append("Missing or empty metadata")
            return

        if "name" not in metadata:
            result["errors"].append("Missing metadata.name")
        elif not self._is_valid_name(metadata["name"]):
            result["errors"].append(f"Invalid resource name: {metadata['name']}")

        if "namespace" in metadata and not self._is_valid_name(metadata["namespace"]):
            result["errors"].append(f"Invalid namespace name: {metadata['namespace']}")

        # Check labels
        if "labels" in metadata:
            if not isinstance(metadata["labels"], dict):
                result["errors"].append("Labels must be a dictionary")
            else:
                for key, value in metadata["labels"].items():
                    if not self._is_valid_label(key, value):
                        result["warnings"].append(f"Invalid label: {key}={value}")

    def _validate_spec(self, kind: str, spec: Dict[str, Any], result: Dict[str, Any]):
        """Validate spec section based on resource kind."""
        if kind == "Deployment":
            self._validate_deployment_spec(spec, result)
        elif kind == "Service":
            self._validate_service_spec(spec, result)
        elif kind == "Pod":
            self._validate_pod_spec(spec, result)
        elif kind == "CronJob":
            self._validate_cronjob_spec(spec, result)
        elif kind in ["PersistentVolume", "PersistentVolumeClaim"]:
            self._validate_storage_spec(kind, spec, result)

    def _validate_deployment_spec(self, spec: Dict[str, Any], result: Dict[str, Any]):
        """Validate Deployment spec."""
        if "replicas" in spec:
            if not isinstance(spec["replicas"], int) or spec["replicas"] < 0:
                result["errors"].append("Invalid replicas value")

        if "selector" not in spec:
            result["errors"].append("Missing selector in Deployment spec")

        if "template" not in spec:
            result["errors"].append("Missing template in Deployment spec")
        else:
            # Validate pod template
            template = spec["template"]
            if "spec" in template:
                self._validate_pod_spec(template["spec"], result)

    def _validate_service_spec(self, spec: Dict[str, Any], result: Dict[str, Any]):
        """Validate Service spec."""
        if "ports" not in spec:
            result["errors"].append("Missing ports in Service spec")
        else:
            for port in spec["ports"]:
                if "port" not in port:
                    result["errors"].append("Missing port number in Service port definition")
                if "targetPort" not in port:
                    result["warnings"].append("Missing targetPort in Service port definition")

        service_type = spec.get("type", "ClusterIP")
        valid_types = ["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"]
        if service_type not in valid_types:
            result["errors"].append(f"Invalid Service type: {service_type}")

    def _validate_pod_spec(self, spec: Dict[str, Any], result: Dict[str, Any]):
        """Validate Pod spec."""
        if "containers" not in spec:
            result["errors"].append("Missing containers in Pod spec")
            return

        for container in spec["containers"]:
            if "name" not in container:
                result["errors"].append("Missing container name")
            if "image" not in container:
                result["errors"].append("Missing container image")
            elif not container["image"]:
                result["errors"].append("Empty container image")

            # Check resource limits
            if "resources" in container:
                if "limits" not in container["resources"] and "requests" not in container["resources"]:
                    result["warnings"].append("Container has resources section but no limits or requests")

    def _validate_cronjob_spec(self, spec: Dict[str, Any], result: Dict[str, Any]):
        """Validate CronJob spec."""
        if "schedule" not in spec:
            result["errors"].append("Missing schedule in CronJob spec")
        else:
            if not self._is_valid_cron_schedule(spec["schedule"]):
                result["errors"].append(f"Invalid cron schedule: {spec['schedule']}")

        if "jobTemplate" not in spec:
            result["errors"].append("Missing jobTemplate in CronJob spec")

    def _validate_storage_spec(self, kind: str, spec: Dict[str, Any], result: Dict[str, Any]):
        """Validate PersistentVolume or PersistentVolumeClaim spec."""
        if "capacity" not in spec and kind == "PersistentVolume":
            result["errors"].append("Missing capacity in PersistentVolume spec")

        if "accessModes" not in spec:
            result["errors"].append(f"Missing accessModes in {kind} spec")
        else:
            valid_modes = ["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"]
            for mode in spec["accessModes"]:
                if mode not in valid_modes:
                    result["errors"].append(f"Invalid access mode: {mode}")

    def _check_deprecated_fields(self, kind: str, resource: Dict[str, Any], result: Dict[str, Any]):
        """Check for deprecated fields."""
        deprecated_fields = {
            "Deployment": ["spec.rollbackTo", "spec.selector.matchExpressions"],
            "Service": ["spec.portalIP"],
            "Pod": ["spec.serviceAccount"],
        }

        if kind in deprecated_fields:
            for field_path in deprecated_fields[kind]:
                if self._field_exists(resource, field_path):
                    result["warnings"].append(f"Using deprecated field: {field_path}")

    def _field_exists(self, obj: Dict[str, Any], path: str) -> bool:
        """Check if a field exists in nested dictionary."""
        parts = path.split('.')
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True

    def _is_valid_name(self, name: str) -> bool:
        """Check if a resource name is valid."""
        pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
        return bool(re.match(pattern, name)) and len(name) <= 63

    def _is_valid_label(self, key: str, value: str) -> bool:
        """Check if a label key-value pair is valid."""
        if not key:
            return False

        # Label key validation
        if '/' in key:
            prefix, name = key.split('/', 1)
            if not self._is_valid_dns_subdomain(prefix):
                return False
            key = name

        if not re.match(r'^[a-z0-9A-Z]([a-z0-9A-Z\-_\.]*[a-z0-9A-Z])?$', key):
            return False

        # Label value validation
        if value and not re.match(r'^[a-z0-9A-Z]([a-z0-9A-Z\-_\.]*[a-z0-9A-Z])?$', value):
            return False

        return len(key) <= 63 and len(value) <= 63

    def _is_valid_dns_subdomain(self, name: str) -> bool:
        """Check if a string is a valid DNS subdomain."""
        pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
        return bool(re.match(pattern, name)) and len(name) <= 253

    def _is_valid_cron_schedule(self, schedule: str) -> bool:
        """Check if a cron schedule is valid."""
        # Simple validation - check if it has 5 fields
        fields = schedule.strip().split()
        return len(fields) == 5

    def validate_from_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """Validate Kubernetes manifests from a markdown file.

        Args:
            filepath: Path to the markdown file

        Returns:
            List of validation results
        """
        from .utils import load_markdown_file

        content = load_markdown_file(filepath)
        yaml_blocks = extract_code_blocks(content, 'yaml') + extract_code_blocks(content, 'yml')

        results = []
        for yaml_block in yaml_blocks:
            result = self.validate_manifest(yaml_block)
            result["source_file"] = str(filepath)
            results.append(result)

        return results