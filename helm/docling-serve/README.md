# Docling Serve Helm Chart

Helm chart for deploying [Docling Serve](https://github.com/docling-project/docling-serve) - a document conversion API service supporting PDF, DOCX, images, and other document formats.

## TL;DR

```bash
helm install docling-serve ./docling-serve \
  --set ingress.host=docling.example.com \
  --set secrets.apiKey=your-api-key
```

## Prerequisites

- Kubernetes 1.19+
- Helm 3.9+
- [cert-manager](https://cert-manager.io/) for TLS (optional)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/) (or your preferred ingress controller)

## Installing the Chart

```bash
helm install docling-serve ./docling-serve
```

## Uninstalling the Chart

```bash
helm uninstall docling-serve
```

## Configuration

### Basic Configuration

```bash
helm install docling-serve ./docling-serve \
  --set image.repository=ghcr.io/docling-project/docling-serve \
  --set image.tag=v1.0.0 \
  --set replicaCount=2 \
  --set ingress.host=docling.example.com \
  --set ingress.tls.enabled=true \
  --set ingress.annotations."cert-manager\.io/cluster-issuer"=letsencrypt-prod
```

### Using an Existing Secret

For production, store secrets in Kubernetes Secrets:

```bash
kubectl create secret generic docling-secrets \
  --from-literal=apiKey=your-api-key \
  --from-literal=externalModelApiKey=your-model-key
```

Then reference it:

```bash
helm install docling-serve ./docling-serve \
  --set secrets.existingSecret=docling-secrets
```

### External Model API (vLLM, Ollama, etc.)

```bash
helm install docling-serve ./docling-serve \
  --set externalModel.enabled=true \
  --set externalModel.baseUrl=http://ollama:11434/v1 \
  --set externalModel.defaultModel=granite-vision \
  --set secrets.externalModelApiKey=your-model-key
```

### Autoscaling

```bash
helm install docling-serve ./docling-serve \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=10 \
  --set autoscaling.targetCPUUtilizationPercentage=70 \
  --set resources.limits.cpu=2000m \
  --set resources.limits.memory=4Gi
```

### Custom Configuration via ConfigMap

Create a config file:

```yaml
# docling-config.yaml
enable_ui: true
log_level: DEBUG
max_document_timeout: 604800
eng_kind: local
eng_loc_num_workers: 4
```

Apply:

```bash
kubectl create configmap docling-config --from-file=config.yaml=docling-config.yaml
helm install docling-serve ./docling-serve \
  --set-file extraVolumes[0].configMap.name=docling-config
```

## Parameters

### Image

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `ghcr.io/docling-project/docling-serve` |
| `image.tag` | Container image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `image.pullSecrets` | Image pull secrets | `[]` |

### Service

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `5001` |

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.host` | Hostname | `docling.example.com` |
| `ingress.tls.enabled` | Enable TLS | `true` |
| `ingress.annotations` | Ingress annotations | cert-manager cluster-issuer |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `2000m` |
| `resources.limits.memory` | Memory limit | `4Gi` |
| `resources.requests.cpu` | CPU request | `500m` |
| `resources.requests.memory` | Memory request | `1Gi` |

### Configuration (config.*)

All `DOCLING_SERVE_*` environment variables are exposed as `config.*` values:

| Parameter | ENV Variable | Default |
|-----------|--------------|---------|
| `config.enable_ui` | `DOCLING_SERVE_ENABLE_UI` | `false` |
| `config.log_level` | `DOCLING_SERVE_LOG_LEVEL` | `INFO` |
| `config.eng_kind` | `DOCLING_SERVE_ENG_KIND` | `local` |
| `config.eng_loc_num_workers` | `DOCLING_SERVE_ENG_LOC_NUM_WORKERS` | `2` |

### Secrets

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.create` | Create default secret | `true` |
| `secrets.existingSecret` | Use existing secret name | `""` |
| `secrets.apiKey` | API key (inline, for dev only) | `""` |
| `secrets.externalModelApiKey` | External model API key | `""` |

### Autoscaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `70` |

### External Model API

| Parameter | Description | Default |
|-----------|-------------|---------|
| `externalModel.enabled` | Enable external model | `false` |
| `externalModel.baseUrl` | Base URL (e.g., http://ollama:11434/v1) | `""` |
| `externalModel.apiKey` | API key for external model | `""` |
| `externalModel.timeout` | Request timeout (seconds) | `60` |
| `externalModel.defaultModel` | Default model name | `""` |

## Production Checklist

- [ ] Set `image.tag` to a specific version
- [ ] Configure `secrets.existingSecret` with real credentials
- [ ] Set appropriate `resources.limits` based on expected workload
- [ ] Configure `ingress.annotations` for your TLS issuer
- [ ] Enable autoscaling for production
- [ ] Set `log_level` to `WARNING` or `ERROR` in production
- [ ] Configure `max_file_size` and `max_sources_per_request` limits
- [ ] Set `cors_origins` to specific domains (not `*`)

## Development/Testing

```bash
# Quick install with defaults
helm install docling-serve ./docling-serve

# Watch pods
kubectl get pods -l app.kubernetes.io/name=docling-serve -w

# Check logs
kubectl logs -l app.kubernetes.io/name=docling-serve -f

# Port forward for local testing
kubectl port-forward svc/docling-serve 5001:5001

# Dry-run to see rendered templates
helm template docling-serve ./docling-serve

# Install with --dry-run=server to validate on cluster
helm install docling-serve ./docling-serve --dry-run=server
```

## Upgrading

```bash
# Check current version
helm list -n default

# Upgrade to new version
helm upgrade docling-serve ./docling-serve --set image.tag=v1.1.0

# Rollback if needed
helm rollback docling-serve
```

## License

Apache 2.0