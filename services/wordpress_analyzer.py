"""
WordPress site analyzer service.
Detects WordPress installations and extracts information without authentication.
"""
import re
import httpx
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urljoin, urlparse
import time

from schemas import (
    WordPressSiteInfo,
    WordPressVersion,
    PHPVersion,
    ThemeInfo,
    PluginInfo,
    ServerInfo,
    SecurityInfo,
    SiteMetadata
)
from config import get_settings


class WordPressAnalyzer:
    """Analyzes WordPress sites and extracts information."""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": self.settings.user_agent
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def analyze(self, url: str, deep_scan: bool = False) -> WordPressSiteInfo:
        """
        Analyze a WordPress site and extract information.

        Args:
            url: The URL to analyze
            deep_scan: Whether to perform a deep scan (more thorough but slower)

        Returns:
            WordPressSiteInfo object with all detected information
        """
        start_time = time.time()

        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        # Initialize result
        result = WordPressSiteInfo(
            url=url,
            is_wordpress=False
        )

        try:
            # Fetch homepage
            response = await self.client.get(url)
            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')

            # Check if it's WordPress
            is_wp = await self._is_wordpress(url, html_content, soup)
            result.is_wordpress = is_wp

            if not is_wp:
                result.scan_duration_ms = int((time.time() - start_time) * 1000)
                return result

            # Extract information
            result.wordpress_version = await self._detect_wordpress_version(url, html_content, soup)
            result.theme = await self._detect_theme(url, html_content, soup)
            result.plugins = await self._detect_plugins(url, html_content, soup, deep_scan)
            result.server_info = await self._detect_server_info(response.headers)
            result.security_info = await self._check_security(url)
            result.metadata = self._extract_metadata(soup)

            result.scan_duration_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            result.scan_duration_ms = int((time.time() - start_time) * 1000)
            raise Exception(f"Failed to analyze site: {str(e)}")

    async def _is_wordpress(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        """Check if the site is running WordPress."""
        # Check 1: Meta generator tag
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator and 'wordpress' in generator.get('content', '').lower():
            return True

        # Check 2: wp-content or wp-includes in HTML
        if 'wp-content' in html or 'wp-includes' in html:
            return True

        # Check 3: WordPress REST API endpoint
        try:
            wp_json_url = urljoin(url, '/wp-json/')
            response = await self.client.get(wp_json_url)
            if response.status_code == 200:
                data = response.json()
                if 'namespaces' in data or 'authentication' in data:
                    return True
        except:
            pass

        # Check 4: Common WordPress files
        common_files = ['/wp-login.php', '/xmlrpc.php', '/wp-admin/']
        for file_path in common_files:
            try:
                check_url = urljoin(url, file_path)
                response = await self.client.head(check_url)
                if response.status_code in [200, 302, 403]:
                    return True
            except:
                continue

        return False

    async def _detect_wordpress_version(
        self,
        url: str,
        html: str,
        soup: BeautifulSoup
    ) -> Optional[WordPressVersion]:
        """Detect WordPress version."""
        version = None
        source = None

        # Method 1: Meta generator tag
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator:
            content = generator.get('content', '')
            match = re.search(r'WordPress\s+([\d.]+)', content, re.IGNORECASE)
            if match:
                version = match.group(1)
                source = "meta_generator"
                return WordPressVersion(version=version, detected_from=source)

        # Method 2: RSS feed
        try:
            feed_url = urljoin(url, '/feed/')
            response = await self.client.get(feed_url)
            if response.status_code == 200:
                match = re.search(r'generator>https://wordpress\.org/\?v=([\d.]+)', response.text)
                if match:
                    version = match.group(1)
                    source = "rss_feed"
                    return WordPressVersion(version=version, detected_from=source)
        except:
            pass

        # Method 3: readme.html
        try:
            readme_url = urljoin(url, '/readme.html')
            response = await self.client.get(readme_url)
            if response.status_code == 200:
                match = re.search(r'Version\s+([\d.]+)', response.text)
                if match:
                    version = match.group(1)
                    source = "readme_html"
                    return WordPressVersion(version=version, detected_from=source)
        except:
            pass

        # Method 4: CSS/JS version strings
        version_pattern = re.compile(r'ver=([\d.]+)')
        matches = version_pattern.findall(html)
        if matches:
            # Get most common version
            from collections import Counter
            most_common = Counter(matches).most_common(1)
            if most_common:
                version = most_common[0][0]
                source = "asset_version"
                return WordPressVersion(version=version, detected_from=source)

        return None

    async def _detect_theme(
        self,
        url: str,
        html: str,
        soup: BeautifulSoup
    ) -> Optional[ThemeInfo]:
        """Detect active WordPress theme."""
        theme_info = ThemeInfo()

        # Look for theme stylesheet link
        theme_pattern = re.compile(r'/wp-content/themes/([^/]+)/')
        matches = theme_pattern.findall(html)

        if matches:
            from collections import Counter
            # Get most common theme slug (likely the active theme)
            most_common = Counter(matches).most_common(1)
            if most_common:
                theme_slug = most_common[0][0]
                theme_info.slug = theme_slug
                theme_info.name = theme_slug.replace('-', ' ').title()

                # Try to get theme URL
                theme_info.template_url = urljoin(url, f'/wp-content/themes/{theme_slug}/')

                # Try to get screenshot
                screenshot_url = urljoin(url, f'/wp-content/themes/{theme_slug}/screenshot.png')
                try:
                    response = await self.client.head(screenshot_url)
                    if response.status_code == 200:
                        theme_info.screenshot_url = screenshot_url
                except:
                    pass

                # Try to get version from style.css
                try:
                    style_url = urljoin(url, f'/wp-content/themes/{theme_slug}/style.css')
                    response = await self.client.get(style_url)
                    if response.status_code == 200:
                        # Parse style.css header
                        content = response.text[:2000]  # Only read first 2000 chars
                        version_match = re.search(r'Version:\s*([\d.]+)', content)
                        author_match = re.search(r'Author:\s*([^\n]+)', content)

                        if version_match:
                            theme_info.version = version_match.group(1).strip()
                        if author_match:
                            theme_info.author = author_match.group(1).strip()
                except:
                    pass

                return theme_info

        return None

    async def _detect_plugins(
        self,
        url: str,
        html: str,
        soup: BeautifulSoup,
        deep_scan: bool = False
    ) -> List[PluginInfo]:
        """Detect active WordPress plugins."""
        plugins = []
        detected_slugs = set()

        # Look for plugin assets in HTML
        plugin_pattern = re.compile(r'/wp-content/plugins/([^/]+)/')
        matches = plugin_pattern.findall(html)

        for plugin_slug in matches:
            if plugin_slug not in detected_slugs:
                detected_slugs.add(plugin_slug)

                plugin_info = PluginInfo(
                    slug=plugin_slug,
                    name=plugin_slug.replace('-', ' ').title(),
                    detected_from="html_source"
                )

                # Try to get version from readme.txt
                if deep_scan:
                    try:
                        readme_url = urljoin(url, f'/wp-content/plugins/{plugin_slug}/readme.txt')
                        response = await self.client.get(readme_url)
                        if response.status_code == 200:
                            content = response.text[:1000]
                            version_match = re.search(r'Stable tag:\s*([\d.]+)', content, re.IGNORECASE)
                            if version_match:
                                plugin_info.version = version_match.group(1).strip()
                    except:
                        pass

                plugins.append(plugin_info)

        return plugins

    async def _detect_server_info(self, headers: Dict[str, str]) -> ServerInfo:
        """Extract server information from HTTP headers."""
        server_info = ServerInfo()

        # Server header
        server_info.server = headers.get('server', headers.get('Server'))

        # X-Powered-By header
        powered_by = headers.get('x-powered-by', headers.get('X-Powered-By'))
        if powered_by:
            server_info.powered_by = powered_by

            # Try to extract PHP version
            php_match = re.search(r'PHP/([\d.]+)', powered_by)
            if php_match:
                server_info.php_version = PHPVersion(
                    version=php_match.group(1),
                    detected_from="x_powered_by_header"
                )

        return server_info

    async def _check_security(self, url: str) -> SecurityInfo:
        """Check various security-related configurations."""
        security = SecurityInfo()

        # Check XML-RPC
        try:
            xmlrpc_url = urljoin(url, '/xmlrpc.php')
            response = await self.client.post(xmlrpc_url, content="")
            security.xmlrpc_enabled = response.status_code in [200, 405]
        except:
            pass

        # Check REST API
        try:
            rest_url = urljoin(url, '/wp-json/')
            response = await self.client.get(rest_url)
            security.rest_api_enabled = response.status_code == 200
            security.wp_json_exposed = response.status_code == 200
        except:
            pass

        # Check readme.html accessibility
        try:
            readme_url = urljoin(url, '/readme.html')
            response = await self.client.get(readme_url)
            security.readme_accessible = response.status_code == 200
        except:
            pass

        # Check directory listing on wp-content
        try:
            wp_content_url = urljoin(url, '/wp-content/')
            response = await self.client.get(wp_content_url)
            # If we see "Index of" in response, directory listing is enabled
            if response.status_code == 200 and 'index of' in response.text.lower():
                security.directory_listing = True
        except:
            pass

        return security

    def _extract_metadata(self, soup: BeautifulSoup) -> SiteMetadata:
        """Extract general site metadata."""
        metadata = SiteMetadata()

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata.title = title_tag.get_text(strip=True)

        # Description
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            metadata.description = desc_meta.get('content', '').strip()

        # Language
        html_tag = soup.find('html')
        if html_tag:
            metadata.language = html_tag.get('lang')

        # Charset
        charset_meta = soup.find('meta', attrs={'charset': True})
        if charset_meta:
            metadata.charset = charset_meta.get('charset')

        # Generator
        generator_meta = soup.find('meta', attrs={'name': 'generator'})
        if generator_meta:
            metadata.generator = generator_meta.get('content', '').strip()

        return metadata
