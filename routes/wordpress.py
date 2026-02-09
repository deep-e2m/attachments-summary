"""
WordPress analyzer API routes.
"""
import asyncio
from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
import httpx

from services import WordPressAnalyzer
from config import get_settings


router = APIRouter(prefix="/api/v1/wordpress", tags=["WordPress"])


@router.get("/analyze", status_code=status.HTTP_200_OK)
async def analyze_wordpress_site(url: str = Query(..., description="WordPress site URL to analyze")):
    """
    Analyze a WordPress site and generate a summary.

    Returns a text summary with WordPress version, theme information, plugins, and PHP version.
    No authentication required.

    Args:
        url: The WordPress site URL to analyze (query parameter)

    Returns:
        JSON with success status and summary

    Example:
        GET /api/v1/wordpress/analyze?url=https://wordpress.org
    """
    settings = get_settings()

    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        async def _run_analysis():
            async with WordPressAnalyzer() as analyzer:
                return await analyzer.analyze(url=url, deep_scan=True)

        # Wrap entire analysis with a timeout to prevent 504 gateway errors
        site_info = await asyncio.wait_for(
            _run_analysis(),
            timeout=settings.analysis_timeout
        )

        # Check if it's WordPress
        if not site_info.is_wordpress:
            return {
                "success": False,
                "summary": f"The site '{url}' is not a WordPress site."
            }

        # Generate summary
        summary_parts = []

        # WordPress version
        if site_info.wordpress_version:
            summary_parts.append(f"WordPress Version: {site_info.wordpress_version.version}")

        # Theme information
        if site_info.theme:
            theme_info = f"Theme: {site_info.theme.name}"
            if site_info.theme.version:
                theme_info += f" (v{site_info.theme.version})"
            if site_info.theme.author:
                theme_info += f" by {site_info.theme.author}"
            summary_parts.append(theme_info)

        # Plugins information
        if site_info.plugins and len(site_info.plugins) > 0:
            summary_parts.append(f"\nActive Plugins ({len(site_info.plugins)}):")
            for plugin in site_info.plugins:
                plugin_info = f"  - {plugin.name}"
                if plugin.version:
                    plugin_info += f" (v{plugin.version})"
                if plugin.description:
                    # Clean and truncate description
                    desc = plugin.description.replace('\n', ' ').strip()
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    plugin_info += f": {desc}"
                summary_parts.append(plugin_info)

        # Site metadata
        if site_info.metadata:
            if site_info.metadata.title:
                summary_parts.append(f"\nSite Title: {site_info.metadata.title}")
            if site_info.metadata.description:
                summary_parts.append(f"Description: {site_info.metadata.description}")

        summary = "\n".join(summary_parts)

        return {
            "success": True,
            "summary": summary
        }

    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "summary": f"Analysis timed out after {settings.analysis_timeout} seconds. The site '{url}' is taking too long to respond. Try again later."
            }
        )

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "summary": f"Failed to access the site. HTTP error: {e.response.status_code}"
        }

    except httpx.RequestError as e:
        return {
            "success": False,
            "summary": f"Failed to connect to the site: {str(e)}"
        }

    except Exception as e:
        return {
            "success": False,
            "summary": f"An error occurred during site analysis: {str(e)}"
        }
