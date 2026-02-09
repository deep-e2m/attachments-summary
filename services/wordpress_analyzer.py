"""
WordPress site analyzer service.
Detects WordPress installations and extracts information without authentication.
"""
import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urljoin, urlparse

from schemas import (
    WordPressSiteInfo,
    WordPressVersion,
    ThemeInfo,
    PluginInfo,
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
                return result

            # Extract information IN PARALLEL
            version_task = self._detect_wordpress_version(url, html_content, soup)
            theme_task = self._detect_theme(url, html_content, soup)
            plugins_task = self._detect_plugins(url, html_content, soup, deep_scan)

            result.wordpress_version, result.theme, result.plugins = await asyncio.gather(
                version_task, theme_task, plugins_task
            )
            result.metadata = self._extract_metadata(soup)

            return result

        except Exception as e:
            raise Exception(f"Failed to analyze site: {str(e)}")

    async def _is_wordpress(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        """Check if the site is running WordPress."""
        # Check 1: Meta generator tag (instant, no HTTP)
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator and 'wordpress' in generator.get('content', '').lower():
            return True

        # Check 2: wp-content or wp-includes in HTML (instant, no HTTP)
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

        # Check 4: Common WordPress files - CHECK IN PARALLEL
        common_files = ['/wp-login.php', '/xmlrpc.php', '/wp-admin/']

        async def check_wp_file(file_path: str) -> bool:
            try:
                check_url = urljoin(url, file_path)
                response = await self.client.head(check_url)
                return response.status_code in [200, 302, 403]
            except:
                return False

        results = await asyncio.gather(*[check_wp_file(f) for f in common_files])
        if any(results):
            return True

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
            most_common = Counter(matches).most_common(1)
            if most_common:
                theme_slug = most_common[0][0]
                theme_info.slug = theme_slug
                theme_info.name = theme_slug.replace('-', ' ').title()

                # Try to get theme URL
                theme_info.template_url = urljoin(url, f'/wp-content/themes/{theme_slug}/')

                # Check screenshot and style.css IN PARALLEL
                async def fetch_screenshot():
                    screenshot_url = urljoin(url, f'/wp-content/themes/{theme_slug}/screenshot.png')
                    try:
                        response = await self.client.head(screenshot_url)
                        if response.status_code == 200:
                            return screenshot_url
                    except:
                        pass
                    return None

                async def fetch_style():
                    style_url = urljoin(url, f'/wp-content/themes/{theme_slug}/style.css')
                    try:
                        response = await self.client.get(style_url)
                        if response.status_code == 200:
                            content = response.text[:2000]
                            version_match = re.search(r'Version:\s*([\d.]+)', content)
                            author_match = re.search(r'Author:\s*([^\n]+)', content)
                            return (
                                version_match.group(1).strip() if version_match else None,
                                author_match.group(1).strip() if author_match else None
                            )
                    except:
                        pass
                    return (None, None)

                screenshot_result, style_result = await asyncio.gather(
                    fetch_screenshot(), fetch_style()
                )

                if screenshot_result:
                    theme_info.screenshot_url = screenshot_result
                version_val, author_val = style_result
                if version_val:
                    theme_info.version = version_val
                if author_val:
                    theme_info.author = author_val

                return theme_info

        return None

    async def _detect_plugins(
        self,
        url: str,
        html: str,
        soup: BeautifulSoup,
        deep_scan: bool = False
    ) -> List[PluginInfo]:
        """Detect active WordPress plugins using multiple methods."""
        plugins = []
        detected_slugs = set()

        # Method 1: Look for plugin paths in HTML source (CSS, JS, images, etc.)
        plugin_pattern = re.compile(r'/wp-content/plugins/([^/\'"?\s]+)', re.IGNORECASE)
        matches = plugin_pattern.findall(html)
        for slug in matches:
            if slug and slug not in detected_slugs:
                detected_slugs.add(slug)

        # Method 2: Check link tags (CSS files)
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            match = re.search(r'/wp-content/plugins/([^/]+)/', href)
            if match:
                slug = match.group(1)
                if slug not in detected_slugs:
                    detected_slugs.add(slug)

        # Method 3: Check script tags (JavaScript files)
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            match = re.search(r'/wp-content/plugins/([^/]+)/', src)
            if match:
                slug = match.group(1)
                if slug not in detected_slugs:
                    detected_slugs.add(slug)

        # Method 4: Check for plugin-specific HTML comments
        comments = soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in str(text))
        comment_slugs_to_verify = []
        for comment in comments:
            comment_text = str(comment).lower()
            if 'plugin' in comment_text or 'wp-' in comment_text:
                match = re.search(r'(?:plugin[:\s]+|wp-)([a-z0-9-]+)', comment_text)
                if match:
                    potential_slug = match.group(1)
                    if len(potential_slug) > 3 and potential_slug not in detected_slugs:
                        if deep_scan:
                            comment_slugs_to_verify.append(potential_slug)

        # Verify comment-found slugs IN PARALLEL
        if comment_slugs_to_verify:
            async def verify_plugin_slug(slug: str) -> Optional[str]:
                plugin_path = urljoin(url, f'/wp-content/plugins/{slug}/')
                try:
                    response = await self.client.head(plugin_path, timeout=5)
                    if response.status_code in [200, 403]:
                        return slug
                except:
                    pass
                return None

            results = await asyncio.gather(*[verify_plugin_slug(s) for s in comment_slugs_to_verify])
            for slug in results:
                if slug:
                    detected_slugs.add(slug)

        # Method 5: Check for plugin-specific meta tags
        for meta in soup.find_all('meta'):
            content = meta.get('content', '') + meta.get('name', '')
            match = re.search(r'/wp-content/plugins/([^/]+)/', content)
            if match:
                slug = match.group(1)
                if slug not in detected_slugs:
                    detected_slugs.add(slug)

        # Method 6: Look for plugin-specific CSS classes and IDs
        plugin_indicators = {
            'yoast': 'wordpress-seo',
            'woocommerce': 'woocommerce',
            'elementor': 'elementor',
            'wpforms': 'wpforms',
            'wp-rocket': 'wp-rocket',
            'jetpack': 'jetpack',
            'akismet': 'akismet',
            'wordfence': 'wordfence',
            'contact-form-7': 'contact-form-7',
            'wp-super-cache': 'wp-super-cache',
            'all-in-one-seo': 'all-in-one-seo-pack',
            'rankmath': 'seo-by-rank-math',
            'wp-optimize': 'wp-optimize',
            'smush': 'wp-smushit',
            'updraft': 'updraftplus',
        }

        html_lower = html.lower()
        for indicator, slug in plugin_indicators.items():
            if indicator in html_lower and slug not in detected_slugs:
                detected_slugs.add(slug)

        # Method 7: Check inline scripts for plugin identifiers
        for script in soup.find_all('script', src=False):
            script_text = script.string if script.string else ''
            if script_text:
                match = re.search(r'/wp-content/plugins/([^/\'"]+)', script_text)
                if match:
                    slug = match.group(1)
                    if slug not in detected_slugs:
                        detected_slugs.add(slug)

        # Method 8: Check for plugin-specific generator tags
        for meta in soup.find_all('meta', attrs={'name': 'generator'}):
            content = meta.get('content', '').lower()
            if 'plugin' in content or any(ind in content for ind in plugin_indicators.keys()):
                for indicator, slug in plugin_indicators.items():
                    if indicator in content and slug not in detected_slugs:
                        detected_slugs.add(slug)

        # Method 9: Deep scan - check common plugin directories IN PARALLEL
        if deep_scan:
            common_plugins = [
                'wordpress-seo', 'akismet', 'jetpack', 'contact-form-7',
                'woocommerce', 'elementor', 'wpforms-lite', 'wordfence',
                'wp-super-cache', 'classic-editor', 'duplicate-post',
                'google-analytics-for-wordpress', 'all-in-one-seo-pack',
                'wp-mail-smtp', 'updraftplus', 'wp-optimize', 'smush',
                'really-simple-ssl', 'redirection', 'wpforms', 'sucuri-scanner'
            ]

            plugins_to_check = [p for p in common_plugins if p not in detected_slugs]

            async def check_plugin_exists(plugin_slug: str) -> Optional[str]:
                plugin_url = urljoin(url, f'/wp-content/plugins/{plugin_slug}/')
                try:
                    response = await self.client.head(plugin_url, timeout=5)
                    if response.status_code in [200, 403]:
                        return plugin_slug
                except:
                    pass
                return None

            results = await asyncio.gather(*[check_plugin_exists(p) for p in plugins_to_check])
            for slug in results:
                if slug:
                    detected_slugs.add(slug)

        # Now create PluginInfo objects - fetch all readme.txt IN PARALLEL
        valid_slugs = [
            s for s in detected_slugs
            if s and len(s) >= 2 and re.match(r'^[a-z0-9\-_]+$', s, re.IGNORECASE)
        ]

        async def fetch_plugin_info(plugin_slug: str) -> Optional[PluginInfo]:
            plugin_info = PluginInfo(
                name=plugin_slug.replace('-', ' ').replace('_', ' ').title()
            )
            try:
                readme_url = urljoin(url, f'/wp-content/plugins/{plugin_slug}/readme.txt')
                response = await self.client.get(readme_url, timeout=5)
                if response.status_code == 200:
                    content = response.text[:3000]

                    # Skip if response is HTML instead of a real readme.txt
                    if content.strip().lower().startswith(('<!doctype', '<html')):
                        return plugin_info

                    version_match = re.search(r'Stable tag:\s*([\d.]+)', content, re.IGNORECASE)
                    if version_match:
                        plugin_info.version = version_match.group(1).strip()

                    desc_patterns = [
                        r'(?:===\s*Description\s*===\s*)(.*?)(?=\n===|\Z)',
                        r'(?:Description:\s*)(.*?)(?=\n[A-Z][a-z]+:|\n===|\Z)',
                        r'(?:^|\n)(.*?)(?:\n===|\Z)'
                    ]

                    for pattern in desc_patterns:
                        desc_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                        if desc_match:
                            description = desc_match.group(1).strip()
                            # Strip any stray HTML tags
                            description = re.sub(r'<[^>]+>', '', description)
                            description = ' '.join(description.split())
                            if len(description) > 10:
                                plugin_info.description = description[:200]
                                break
            except:
                pass
            return plugin_info

        plugin_infos = await asyncio.gather(*[fetch_plugin_info(s) for s in valid_slugs])
        plugins = [p for p in plugin_infos if p is not None]

        return plugins

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
