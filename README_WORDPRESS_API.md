# WordPress Analyzer API

A FastAPI-based REST API for analyzing WordPress sites without authentication, similar to Wappalyzer or HackerTarget.

## Features

- **No Authentication Required**: Analyzes WordPress sites using only publicly accessible information
- **Comprehensive Detection**: Detects WordPress version, theme, plugins, PHP version, and security configurations
- **Fast Analysis**: Typically completes in 2-5 seconds
- **Optional Deep Scan**: More thorough plugin detection with version information
- **REST API**: Clean JSON responses
- **Interactive Docs**: Swagger UI at `/docs`

## What It Detects

- ✅ WordPress version
- ✅ Active theme (name, version, author, screenshot)
- ✅ Active plugins (with optional version detection)
- ✅ PHP version (if exposed in headers)
- ✅ Server information (nginx, apache, etc.)
- ✅ Security configurations:
  - XML-RPC enabled/disabled
  - REST API accessibility
  - Directory listing
  - readme.html accessibility
- ✅ Site metadata (title, description, language)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python3 main.py
```

The API will start on `http://localhost:8000`

## API Endpoints

### 1. Analyze WordPress Site (POST)

**Endpoint**: `POST /api/v1/wordpress/analyze`

**Request Body**:
```json
{
  "url": "https://example.com",
  "deep_scan": false
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/wordpress/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://wordpress.org", "deep_scan": false}'
```

**Response**:
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
      "slug": "wporg-parent-2021",
      "version": "1.0.0",
      "author": "WordPress.org",
      "template_url": "https://wordpress.org/wp-content/themes/wporg-parent-2021/",
      "screenshot_url": "https://wordpress.org/wp-content/themes/wporg-parent-2021/screenshot.png"
    },
    "plugins": [
      {
        "name": "Gutenberg",
        "slug": "gutenberg",
        "version": null,
        "detected_from": "html_source"
      }
    ],
    "server_info": {
      "server": "nginx",
      "php_version": null,
      "powered_by": null
    },
    "security_info": {
      "xmlrpc_enabled": true,
      "rest_api_enabled": true,
      "directory_listing": false,
      "readme_accessible": false,
      "wp_json_exposed": true
    },
    "metadata": {
      "title": "Blog Tool, Publishing Platform, and CMS – WordPress.org",
      "description": "Open source software which you can use to easily create a beautiful website, blog, or app.",
      "language": "en-US",
      "charset": "UTF-8",
      "generator": "WordPress 7.0-alpha-61437"
    },
    "scan_timestamp": "2026-01-06T09:25:06.471153",
    "scan_duration_ms": 3206
  },
  "error": null,
  "message": "Site analysis completed successfully"
}
```

### 2. Analyze WordPress Site (GET)

**Endpoint**: `GET /api/v1/wordpress/analyze/{url}`

**Parameters**:
- `url`: The WordPress site URL (can be with or without protocol)
- `deep_scan`: Optional boolean (default: false)

**Example**:
```bash
curl "http://localhost:8000/api/v1/wordpress/analyze/techcrunch.com"
```

### 3. Health Check

**Endpoint**: `GET /health`

**Example**:
```bash
curl "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test the API directly from your browser.

## Detection Methods

The analyzer uses multiple detection methods to ensure accurate results:

### WordPress Detection
1. Meta generator tag
2. `wp-content` or `wp-includes` in HTML
3. WordPress REST API endpoint (`/wp-json/`)
4. Common WordPress files (`/wp-login.php`, `/xmlrpc.php`)

### Version Detection
1. Meta generator tag
2. RSS feed generator
3. readme.html file
4. CSS/JS asset version strings

### Theme Detection
1. Theme stylesheet links in HTML
2. Theme directory paths
3. style.css header information

### Plugin Detection
1. Plugin asset URLs in HTML (CSS, JS)
2. Plugin directory paths
3. Plugin readme.txt (in deep scan mode)

### PHP Version Detection
1. X-Powered-By HTTP header
2. Server HTTP header

## Configuration

Edit `config.py` to customize:

```python
# HTTP Client Settings
request_timeout: int = 30  # Request timeout in seconds
max_retries: int = 3  # Maximum number of HTTP retries
user_agent: str = "Mozilla/5.0 (compatible; WordPress-Analyzer/1.0)"

# WordPress Detection Settings
enable_plugin_detection: bool = True
enable_theme_detection: bool = True
enable_version_detection: bool = True
```

## Testing

Run the tests:

```bash
# Test with WordPress site
curl -X POST "http://localhost:8000/api/v1/wordpress/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://wordpress.org", "deep_scan": false}'

# Test with non-WordPress site
curl "http://localhost:8000/api/v1/wordpress/analyze/google.com"
```

## Example Use Cases

1. **Security Auditing**: Check if WordPress sites have XML-RPC or directory listing enabled
2. **Competitive Analysis**: Identify themes and plugins used by competitors
3. **Site Profiling**: Gather information about WordPress installations
4. **Version Tracking**: Monitor WordPress version across multiple sites
5. **Migration Planning**: Understand site configuration before migration

## Limitations

- Some information may not be detectable if:
  - The site uses heavy caching or CDN
  - WordPress files are in non-standard locations
  - The site has aggressive security measures
  - PHP version is not exposed in headers
- Plugin detection is based on loaded assets, so inactive plugins won't be detected
- Some security-hardened sites may block detection attempts

## Response Structure

### Successful Analysis
```json
{
  "success": true,
  "data": { /* WordPressSiteInfo object */ },
  "error": null,
  "message": "Site analysis completed successfully"
}
```

### Failed Analysis
```json
{
  "success": false,
  "data": null,
  "error": "Error message",
  "message": "An error occurred during site analysis"
}
```

### Non-WordPress Site
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "is_wordpress": false,
    "wordpress_version": null,
    "theme": null,
    "plugins": [],
    ...
  },
  "error": null,
  "message": "Site analysis completed successfully"
}
```

## Production Deployment

For production deployment, consider:

1. **Rate Limiting**: Add rate limiting to prevent abuse
2. **Caching**: Cache results for frequently analyzed sites
3. **Authentication**: Add API key authentication
4. **Monitoring**: Set up logging and monitoring
5. **HTTPS**: Use HTTPS in production
6. **Environment Variables**: Use `.env` file for configuration

## License

This is a custom API built for WordPress site analysis.

## Support

For issues or questions, please refer to the codebase documentation.
