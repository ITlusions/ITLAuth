# Cluster Configuration API

A lightweight Flask API service that distributes Kubernetes cluster configurations with up-to-date certificates for ITlusions OIDC setup.

## Features

- ✅ **Automatic certificate fetching** from kubectl
- ✅ **Auto-refresh** with configurable interval
- ✅ Serves cluster configuration as YAML or JSON
- ✅ Manual refresh endpoint
- ✅ Optional API key authentication
- ✅ CORS enabled for browser access
- ✅ Health check endpoint
- ✅ Access logging
- ✅ Docker support

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Cluster Configuration

**Option A: Auto-fetch from kubectl (Recommended)**

The API will automatically fetch the cluster config from your current kubectl context:

```bash
# Make sure kubectl is configured
kubectl cluster-info

# The API will auto-fetch when started with AUTO_REFRESH=true
export AUTO_REFRESH=true
python app.py
```

**Option B: Manual configuration**

Create `configs/cluster.yaml` with your cluster details:

```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: <BASE64_ENCODED_CA_CERT>
    server: https://your-cluster-api:6443
  name: itlusions-cluster
contexts:
- context:
    cluster: itlusions-cluster
    user: default-user
  name: itlusions-cluster
current-context: itlusions-cluster
users:
- name: default-user
  user: {}
```

### 3. Run the API

```bash
# Development
python app.py

# Production with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T10:30:00.000000"
}
```

### `GET /api/v1/cluster-config`
Download cluster configuration as YAML.

**Headers:**
- `Authorization: Bearer <API_KEY>` (optional, if API_KEY is set)

**Response:**
- Content-Type: `application/x-yaml`
- Downloads `cluster.yaml` file

### `GET /api/v1/cluster-config/json`
Get cluster configuration as JSON.

**Response:**
```json
{
  "apiVersion": "v1",
  "kind": "Config",
  "clusters": [...],
  "contexts": [...],
  "users": [...]
}
```

### `GET /api/v1/cluster-config/info`
Get cluster metadata without downloading the full config.

**Response:**
```json
{
  "clusters": ["itlusions-cluster"],
  "contexts": ["itlusions-cluster"],
  "current_context": "itlusions-cluster",
  "last_updated": "2026-01-22T10:30:00",
  "api_version": "v1",
  "auto_refresh": true
}
```

### `POST /api/v1/cluster-config/refresh`
Manually trigger a refresh of cluster configuration from kubectl.

**Headers:**
- `Authorization: Bearer <API_KEY>` (required if API_KEY is set)

**Response:**
```json
{
  "status": "success",
  "message": "Cluster configuration refreshed",
  "timestamp": "2026-01-22T10:30:00.000000"
}
```

## Configuration

### Environment Variables

- `PORT` - Server port (default: 5000)
- `DEBUG` - Enable debug mode (default: false)
- `API_KEY` - Optional API key for authentication
- `AUTO_REFRESH` - Automatically refresh config from kubectl (default: false)
- `REFRESH_INTERVAL` - Seconds between auto-refreshes (default: 3600)

```bash
# With auto-refresh every hour
export AUTO_REFRESH=true
export REFRESH_INTERVAL=3600
python app.py

# With authentication
export API_KEY="your-secret-key-here"
python app.py

# Custom port
export PORT=8080
python app.py
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY configs/ configs/

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t cluster-config-api .
docker run -p 5000:5000 -v $(pwd)/configs:/app/configs cluster-config-api
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-config-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cluster-config-api
  template:
    metadata:
      labels:
        app: cluster-config-api
    spec:
      containers:
      - name: api
        image: your-registry/cluster-config-api:latest
        ports:
        - containerPort: 5000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: api-key
        volumeMounts:
        - name: config
          mountPath: /app/configs
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: cluster-config
---
apiVersion: v1
kind: Service
metadata:
  name: cluster-config-api
spec:
  selector:
    app: cluster-config-api
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### Azure App Service / AWS Elastic Beanstalk

1. Package the application
2. Set environment variables via portal/console
3. Mount `configs/` directory with your cluster config
4. Deploy

## Updating Certificates

### Automatic (Recommended)

Enable auto-refresh to fetch certificates from kubectl automatically:

```bash
# Docker
docker run -e AUTO_REFRESH=true -e REFRESH_INTERVAL=3600 \
  -v ~/.kube:/root/.kube:ro \
  cluster-config-api

# Docker Compose (already configured)
docker-compose up -d
```

The API will:
1. Run `kubectl config view --flatten --minify` 
2. Extract cluster certificates
3. Update the config file
4. Repeat every `REFRESH_INTERVAL` seconds

### Manual Trigger

Call the refresh endpoint:

```bash
curl -X POST -H "Authorization: Bearer your-key" \
  https://your-api.com/api/v1/cluster-config/refresh
```

### Manual File Update

To update cluster certificates manually:

1. Generate new certificate:
   ```bash
   base64 -w 0 new-ca.crt
   ```

2. Update `configs/cluster.yaml`:
   ```yaml
   certificate-authority-data: <NEW_BASE64_CERT>
   ```

3. Restart the API (or it picks up changes automatically in some setups)

## Usage with itl-kubectl-oidc-setup

Update the tool to use this API:

```python
# In __main__.py
self.default_cluster_config_url = "https://your-api.example.com/api/v1/cluster-config"
```

Users can then install with:
```bash
itl-kubectl-oidc-setup --download-config
```

With authentication:
```bash
export API_KEY="your-key"
itl-kubectl-oidc-setup --config-url "https://your-api.example.com/api/v1/cluster-config?key=$API_KEY"
```

## Security Best Practices

1. **Use HTTPS** - Always run behind a reverse proxy with SSL
2. **API Key Authentication** - Set `API_KEY` environment variable
3. **Network Restrictions** - Limit access to corporate network/VPN
4. **Rate Limiting** - Add rate limiting middleware in production
5. **Audit Logging** - Monitor access logs for suspicious activity
6. **Regular Rotation** - Update certificates on a schedule

## Monitoring

### Health Check
```bash
curl https://your-api.example.com/health
```

### Test Config Download
```bash
curl -H "Authorization: Bearer your-key" \
  https://your-api.example.com/api/v1/cluster-config \
  -o test-cluster.yaml
```

### Check Last Update
```bash
curl https://your-api.example.com/api/v1/cluster-config/info
```

## Troubleshooting

**"Cluster configuration not found"**
- Ensure `configs/cluster.yaml` exists
- Check file permissions
- Verify YAML syntax: `python -c "import yaml; yaml.safe_load(open('configs/cluster.yaml'))"`

**"Unauthorized"**
- Check API_KEY environment variable
- Verify Authorization header format: `Bearer <key>`

**CORS errors**
- CORS is enabled by default
- Check browser console for specific errors
- Verify the API is accessible from your domain

## Development

Run tests:
```bash
python -m pytest tests/
```

Run with auto-reload:
```bash
export FLASK_ENV=development
python app.py
```

## License

MIT License - See LICENSE file
