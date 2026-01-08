# Deployment Handoff Document

**Application:** WordPress Analyzer API
**Date:** January 2026
**Purpose:** Analyze WordPress sites without authentication

---

## DevOps Responsibilities

### What You Need To Configure

| Task | Required? | Details |
|------|-----------|---------|
| **External Port Mapping** | YES | Change `8000:8000` to your desired port (e.g., `80:8000`, `8080:8000`) |
| **Domain/DNS** | YES | Point your domain to server IP |
| **SSL/TLS Certificate** | Recommended | For HTTPS access |
| **Reverse Proxy (Nginx)** | Recommended | For SSL termination and load balancing |
| **Firewall Rules** | YES | Allow inbound on your external port, outbound on 80/443 |
| **Environment Variables** | NO | All have defaults, optional to customize |

### What's Already Done (No Changes Needed)

| Item | Status |
|------|--------|
| Application code | Ready |
| Internal port (8000) | Hardcoded, don't change |
| Dockerfile | Ready |
| Health checks | Configured |
| CORS | Enabled (allows all origins) |

---

## Quick Summary

| Item | Value |
|------|-------|
| **Application Type** | Python FastAPI REST API |
| **Internal Port** | 8000 (DO NOT CHANGE) |
| **Health Check** | `GET /health` |
| **Docker Ready** | Yes |
| **Python Version** | 3.11+ |
| **Authentication Required** | No |
| **External Dependencies** | None (only makes HTTP requests) |

---

## Files Included

```
✅ Dockerfile           - Container build instructions
✅ docker-compose.yml   - Container orchestration (EDIT PORT HERE)
✅ requirements.txt     - Python dependencies
✅ .env.example         - Environment variables template (optional)
✅ All source code      - Application code (NO CHANGES NEEDED)
```

---

## Quick Start (3 Steps)

### Step 1: Configure External Port
Edit `docker-compose.yml` to set your desired external port:
```yaml
ports:
  - "80:8000"      # Option A: Expose on port 80
  - "8080:8000"    # Option B: Expose on port 8080
  - "443:8000"     # Option C: Behind SSL (use with reverse proxy)
```

### Step 2: Build and Run
```bash
docker-compose up -d --build
```

### Step 3: Verify
```bash
curl http://YOUR_SERVER_IP:YOUR_PORT/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

---

## Docker Build & Run (Alternative Methods)

### Build Image Manually
```bash
docker build -t wordpress-analyzer-api:latest .
```

### Run Container Manually
```bash
docker run -d \
  --name wordpress-analyzer \
  -p 80:8000 \
  wordpress-analyzer-api:latest
```

### Using Docker Compose (Recommended)
```bash
docker-compose up -d --build
```

**Access the API (replace with your configured port):**
- API: `http://YOUR_SERVER:PORT`
- Docs: `http://YOUR_SERVER:PORT/docs`
- Health: `http://YOUR_SERVER:PORT/health`

---

## Environment Variables (Optional)

All environment variables have defaults. You can override them as needed.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `WordPress Analyzer API` | Application name |
| `DEBUG` | No | `false` | Enable debug mode |
| `REQUEST_TIMEOUT` | No | `30` | HTTP request timeout (seconds) |
| `MAX_RETRIES` | No | `3` | Max HTTP retries |
| `USER_AGENT` | No | `Mozilla/5.0...` | User agent for requests |
| `ENABLE_PLUGIN_DETECTION` | No | `true` | Enable plugin detection |
| `ENABLE_THEME_DETECTION` | No | `true` | Enable theme detection |
| `ENABLE_VERSION_DETECTION` | No | `true` | Enable version detection |
| `RATE_LIMIT_REQUESTS` | No | `10` | Requests per minute per IP |

### Production .env File (Optional)
```env
# API Settings
APP_NAME="WordPress Analyzer API"
DEBUG=false

# HTTP Client Settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
USER_AGENT="Mozilla/5.0 (compatible; WordPress-Analyzer/1.0)"

# WordPress Detection Settings
ENABLE_PLUGIN_DETECTION=true
ENABLE_THEME_DETECTION=true
ENABLE_VERSION_DETECTION=true

# Rate Limiting
RATE_LIMIT_REQUESTS=10
```

---

## Port Configuration

| Port | Type | Description |
|------|------|-------------|
| **8000** | Internal (Container) | Application port - DO NOT CHANGE |
| **Your Choice** | External (Host) | Configure in docker-compose.yml |

### How Port Mapping Works

```
Internet → Your External Port → Container Port 8000 → Application
```

**Example Configurations:**

| Use Case | docker-compose.yml | Access URL |
|----------|-------------------|------------|
| Development | `"8000:8000"` | http://localhost:8000 |
| Production (HTTP) | `"80:8000"` | http://yourdomain.com |
| Production (behind Nginx) | `"8000:8000"` | Nginx handles external port |
| Custom Port | `"3000:8000"` | http://yourdomain.com:3000 |

**Recommended Production Setup:**
```
Internet (443/HTTPS) → Nginx (SSL termination) → Container (8000)
```

**Docker Compose Port Mapping:**
```yaml
ports:
  - "80:8000"  # Host port 80 → Container port 8000
```

---

## Health Check

| Endpoint | Method | Expected Response |
|----------|--------|-------------------|
| `/health` | GET | `{"status": "healthy", "version": "1.0.0"}` |

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
| `/api/v1/wordpress/analyze` | POST | Analyze WordPress site (JSON body) |
| `/api/v1/wordpress/analyze/{url}` | GET | Analyze WordPress site (URL param) |
| `/docs` | GET | Swagger API documentation |

### Example API Calls

**POST Method:**
```bash
curl -X POST "https://api.yourdomain.com/api/v1/wordpress/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "deep_scan": false}'
```

**GET Method:**
```bash
curl "https://api.yourdomain.com/api/v1/wordpress/analyze/example.com"
```

---

## Resource Requirements

### Minimum (Production)
| Resource | Value |
|----------|-------|
| CPU | 0.5 vCPU |
| RAM | 512 MB |
| Storage | 2 GB |

### Recommended (Production with Traffic)
| Resource | Value |
|----------|-------|
| CPU | 1 vCPU |
| RAM | 1 GB |
| Storage | 5 GB |

**Notes:**
- Very lightweight application
- No database required
- No file storage needed
- Scales horizontally easily

---

## Dependencies (External Services)

| Service | Required | Purpose | Notes |
|---------|----------|---------|-------|
| **Target WordPress Sites** | YES | Sites to analyze | Must be publicly accessible |
| **Internet Access** | YES | HTTP/HTTPS requests | Outbound 80/443 required |

**IMPORTANT:** This application makes outbound HTTP/HTTPS requests to analyze WordPress sites. Ensure outbound traffic on ports 80 and 443 is allowed.

---

## Firewall Rules

### Inbound
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 8000 | TCP | Load Balancer / Internal | Application API |

### Outbound
| Port | Protocol | Destination | Purpose |
|------|----------|-------------|---------|
| 80 | TCP | Internet | HTTP requests to WordPress sites |
| 443 | TCP | Internet | HTTPS requests to WordPress sites |

---

## Nginx Configuration (Reverse Proxy)

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Redirect HTTP to HTTPS
    if ($scheme = http) {
        return 301 https://$server_name$request_uri;
    }

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

        # Timeout settings for site analysis
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;

        # CORS headers (if needed)
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type' always;
    }

    # Rate limiting (optional)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/m;
    limit_req zone=api_limit burst=20 nodelay;
}
```

---

## Kubernetes Deployment (Optional)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress-analyzer
  labels:
    app: wordpress-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wordpress-analyzer
  template:
    metadata:
      labels:
        app: wordpress-analyzer
    spec:
      containers:
      - name: wordpress-analyzer
        image: wordpress-analyzer-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "false"
        - name: REQUEST_TIMEOUT
          value: "30"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
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
  name: wordpress-analyzer-service
spec:
  selector:
    app: wordpress-analyzer
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wordpress-analyzer-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "10"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: wordpress-analyzer-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: wordpress-analyzer-service
            port:
              number: 80
```

---

## Logging

Application logs to stdout/stderr. Recommended log collection:

**Docker:**
```bash
# View logs
docker logs wordpress-analyzer

# Follow logs
docker logs -f wordpress-analyzer

# Docker Compose
docker-compose logs -f wordpress-analyzer
```

**Kubernetes:**
```bash
kubectl logs -f deployment/wordpress-analyzer
```

**Centralized Logging:**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- CloudWatch (AWS)
- Stackdriver (GCP)

---

## Monitoring

### Recommended Metrics

| Metric | Description |
|--------|-------------|
| Response Time | API endpoint latency |
| Request Rate | Requests per minute |
| Error Rate | Failed requests percentage |
| Health Check | Uptime monitoring |
| Memory Usage | Container memory |
| CPU Usage | Container CPU |

### Prometheus Example

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'wordpress-analyzer'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'  # If you add Prometheus endpoint
```

---

## Testing After Deployment

Replace `YOUR_SERVER` with your actual server IP or domain, and `PORT` with your configured port.

### 1. Health Check
```bash
# If using port 80:
curl http://YOUR_SERVER/health

# If using custom port (e.g., 8080):
curl http://YOUR_SERVER:8080/health

# If using HTTPS with domain:
curl https://api.yourdomain.com/health

# Expected: {"status": "healthy", "version": "1.0.0"}
```

### 2. API Documentation
```
Open in browser: http://YOUR_SERVER:PORT/docs
```

### 3. Test WordPress Site Analysis (POST)
```bash
curl -X POST "http://YOUR_SERVER:PORT/api/v1/wordpress/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://wordpress.org", "deep_scan": false}'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://wordpress.org/",
    "is_wordpress": true,
    "wordpress_version": {
      "version": "7.0",
      "detected_from": "meta_generator"
    },
    "theme": {
      "name": "Wporg Parent 2021",
      "slug": "wporg-parent-2021"
    },
    "plugins": [...]
  }
}
```

### 4. Test WordPress Site Analysis (GET)
```bash
curl "http://YOUR_SERVER:PORT/api/v1/wordpress/analyze?url=https://techcrunch.com"
```

### 5. Test Non-WordPress Site
```bash
curl "http://YOUR_SERVER:PORT/api/v1/wordpress/analyze?url=https://google.com"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://google.com",
    "is_wordpress": false
  }
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container won't start | Check `docker logs wordpress-analyzer` |
| Health check failing | Verify port 8000 is accessible inside container |
| Timeout errors | Check outbound firewall rules (80/443) |
| Can't analyze HTTPS sites | Ensure SSL certificates are trusted |
| High memory usage | Check for memory leaks, restart container |
| Slow responses | Increase `REQUEST_TIMEOUT`, check target site speed |

### Common Error Messages

**"Request error: Connection refused"**
- Target WordPress site is down
- Target site blocked the request
- Network connectivity issue

**"HTTP error occurred: 403"**
- Target site blocked the request (WAF, rate limiting)
- User-Agent blocked
- IP blocked

**"An error occurred during site analysis"**
- Check logs: `docker logs wordpress-analyzer`
- Increase timeout settings
- Verify target URL is valid

---

## Security Considerations

### Application Security
- ✅ Runs as non-root user (UID 1000)
- ✅ No sensitive data stored
- ✅ No database required
- ✅ Read-only filesystem possible
- ✅ Minimal attack surface

### Network Security
- Use HTTPS (TLS) for external access
- Rate limiting recommended (prevent abuse)
- Firewall rules (restrict inbound to load balancer only)
- Consider IP whitelisting if internal use only

### Data Privacy
- No personal data collected
- No data stored persistently
- Only analyzes public information
- GDPR compliant (no PII)

---

## Backup & Recovery

**No backup required:**
- Stateless application
- No database
- No file storage
- Configuration in environment variables

**Disaster Recovery:**
1. Rebuild container from Docker image
2. Deploy with same environment variables
3. Application ready immediately

---

## Scaling

### Horizontal Scaling
- ✅ Fully stateless - scales easily
- ✅ No session management
- ✅ No shared state
- ✅ Use load balancer for multiple replicas

**Docker Compose Scaling:**
```bash
docker-compose up -d --scale wordpress-analyzer=3
```

**Kubernetes Scaling:**
```bash
kubectl scale deployment wordpress-analyzer --replicas=5
```

### Vertical Scaling
- Not typically needed
- Increase CPU/RAM if analyzing many sites concurrently

---

## Performance Optimization

### Caching (Optional)
Implement Redis caching for frequently analyzed sites:

```python
# Example: Cache results for 1 hour
@cache(ttl=3600)
async def analyze(url: str):
    # ... analysis logic
```

### CDN (Optional)
Place API behind CDN for geographic distribution:
- Cloudflare
- AWS CloudFront
- Fastly

---

## Checklist for DevOps

- [ ] Docker image built successfully
- [ ] Environment variables configured (if needed)
- [ ] Port 8000 exposed internally
- [ ] Reverse proxy configured (443 → 8000)
- [ ] SSL certificate installed
- [ ] Outbound HTTP/HTTPS allowed (80, 443)
- [ ] Health check endpoint responding
- [ ] Swagger docs accessible at /docs
- [ ] Test API call successful (WordPress.org)
- [ ] Test API call successful (non-WordPress site)
- [ ] Rate limiting configured (optional)
- [ ] Monitoring setup (optional)
- [ ] Logging configured
- [ ] Horizontal scaling tested (optional)

---

## Support & Contact

For questions about the application:
- **Documentation:** See `DEVELOPER_GUIDE.md` for technical details
- **API Docs:** Available at `/docs` endpoint
- **GitHub Issues:** [Repository URL if applicable]

---

## What Makes This API Different

Unlike WordPress REST API or authenticated APIs:

✅ **No authentication required** - Analyzes public data only
✅ **Works with any WordPress site** - No plugins needed
✅ **Fast** - Typically 2-5 seconds per site
✅ **Ethical** - Only accesses public information
✅ **Legal** - Similar to browser viewing public pages
✅ **Privacy-friendly** - No tracking, no data storage

Similar to: Wappalyzer, BuiltWith, HackerTarget, WPScan (passive mode)

---

## License & Legal

This API analyzes only publicly accessible information, similar to viewing a website in a browser. It does not:
- Attempt to bypass security measures
- Perform unauthorized access
- Store or share private information
- Violate terms of service

**Recommended Use Cases:**
- Security auditing (authorized)
- Competitor analysis
- Site profiling
- Version tracking
- Migration planning

**Not Recommended:**
- Mass scanning without permission
- Exploiting vulnerabilities
- Bypassing security measures
