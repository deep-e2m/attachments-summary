# Deployment Handoff Document

**Application:** Attachment & Video Summary API
**Date:** December 2024
**Developer Contact:** [Your Name]

---

## Quick Summary

| Item | Value |
|------|-------|
| **Application Type** | Python FastAPI REST API |
| **Internal Port** | 8000 |
| **Health Check** | `GET /health` |
| **Docker Ready** | Yes |
| **Python Version** | 3.11+ |

---

## Files to Provide

```
✅ Dockerfile           - Container build instructions
✅ docker-compose.yml   - Container orchestration
✅ requirements.txt     - Python dependencies
✅ .env.example         - Environment variables template
✅ All source code      - Application code
```

---

## Docker Build & Run

### Build Image
```bash
docker build -t summary-api:latest .
```

### Run Container
```bash
docker run -d \
  --name summary-api \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key_here \
  summary-api:latest
```

### Using Docker Compose
```bash
docker-compose up -d --build
```

---

## Environment Variables (REQUIRED)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENROUTER_API_KEY` | **YES** | OpenRouter API key | `sk-or-...` |
| `DEFAULT_MODEL_TYPE` | No | Default: `openrouter` | `openrouter` |
| `OPENROUTER_DEFAULT_MODEL` | No | Default: `gpt-4o-mini` | `gpt-4o-mini` |
| `MAX_FILE_SIZE_MB` | No | Default: `50` | `50` |
| `WHISPER_MODEL` | No | Default: `base` | `base` |
| `DEBUG` | No | Default: `false` | `false` |

### Production .env File
```env
# REQUIRED
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OPTIONAL
DEFAULT_MODEL_TYPE=openrouter
OPENROUTER_DEFAULT_MODEL=gpt-4o-mini
MAX_FILE_SIZE_MB=50
WHISPER_MODEL=base
DEBUG=false
```

---

## Port Configuration

| Port | Protocol | Description |
|------|----------|-------------|
| **8000** | HTTP | Application port (internal) |

**Reverse Proxy Configuration:**
```
External (443/HTTPS) → Nginx/Load Balancer → Container (8000)
```

---

## Health Check

| Endpoint | Method | Expected Response |
|----------|--------|-------------------|
| `/health` | GET | `{"status": "healthy", "version": "2.1.0"}` |

**Docker Health Check (already configured in Dockerfile):**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/models` | GET | List available models |
| `/api/v1/summarize/attachment` | POST | Document summarization (PDF, DOCX, TXT) |
| `/api/v1/summarize/video` | POST | Video transcription & summarization |
| `/docs` | GET | Swagger API documentation |

---

## Resource Requirements

### Minimum (Document only)
| Resource | Value |
|----------|-------|
| CPU | 1 vCPU |
| RAM | 1 GB |
| Storage | 5 GB |

### Recommended (With Video Processing)
| Resource | Value |
|----------|-------|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Storage | 20 GB |

---

## Dependencies (External Services)

| Service | Required | Purpose | Notes |
|---------|----------|---------|-------|
| **OpenRouter API** | YES | LLM for summaries | Requires API key |
| **Ollama** | NO | Local LLM (dev only) | Not for production |

**IMPORTANT:** This application calls external APIs (OpenRouter). Ensure outbound HTTPS (443) is allowed.

---

## Firewall Rules

### Inbound
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 8000 | TCP | Load Balancer / Internal | Application |

### Outbound
| Port | Protocol | Destination | Purpose |
|------|----------|-------------|---------|
| 443 | TCP | openrouter.ai | OpenRouter API |

---

## Nginx Configuration (if needed)

```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout settings for large file uploads
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;

        # Max upload size
        client_max_body_size 50M;
    }
}
```

---

## Kubernetes Deployment (if applicable)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: summary-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: summary-api
  template:
    metadata:
      labels:
        app: summary-api
    spec:
      containers:
      - name: summary-api
        image: summary-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openrouter-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: summary-api-service
spec:
  selector:
    app: summary-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## Logging

Application logs to stdout/stderr. Recommended log collection:
- Docker: Use `docker logs` or log driver
- Kubernetes: Use centralized logging (ELK, Loki)

---

## Testing After Deployment

### 1. Health Check
```bash
curl https://api.yourdomain.com/health
# Expected: {"status": "healthy", "version": "2.1.0"}
```

### 2. API Documentation
```
Open: https://api.yourdomain.com/docs
```

### 3. Test Attachment Summary
```bash
curl -X POST "https://api.yourdomain.com/api/v1/summarize/attachment" \
  -F "file=@document.pdf"
```

### 4. Test Video Summary
```bash
curl -X POST "https://api.yourdomain.com/api/v1/summarize/video" \
  -F "file=@video.mp4"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container won't start | Check `docker logs summary-api` |
| 500 errors | Check if OPENROUTER_API_KEY is set |
| Timeout on video upload | Increase proxy timeout, check MAX_FILE_SIZE_MB |
| Can't reach OpenRouter API | Check outbound firewall rules |

---

## Checklist for DevOps

- [ ] Docker image built successfully
- [ ] Environment variables configured
- [ ] Port 8000 exposed internally
- [ ] Reverse proxy configured (443 → 8000)
- [ ] SSL certificate installed
- [ ] Outbound HTTPS allowed (for OpenRouter API)
- [ ] Health check endpoint responding
- [ ] Swagger docs accessible at /docs
- [ ] Test API call successful

---

## Contact

For questions about the application:
- **Developer:** [Your Name]
- **Email:** [Your Email]
