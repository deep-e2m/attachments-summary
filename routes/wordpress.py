"""
WordPress analyzer API routes.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import httpx

from schemas import AnalyzeRequest, AnalyzeResponse, WordPressSiteInfo
from services import WordPressAnalyzer


router = APIRouter(prefix="/api/v1/wordpress", tags=["WordPress"])


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_wordpress_site(request: AnalyzeRequest):
    """
    Analyze a WordPress site and extract information.

    This endpoint analyzes a WordPress site without requiring authentication.
    It detects:
    - WordPress version
    - Active theme
    - Active plugins
    - PHP version
    - Server information
    - Security configurations

    Args:
        request: AnalyzeRequest containing the URL to analyze

    Returns:
        AnalyzeResponse with detected site information

    Example:
        ```
        POST /api/v1/wordpress/analyze
        {
            "url": "https://example.com",
            "deep_scan": false
        }
        ```
    """
    try:
        async with WordPressAnalyzer() as analyzer:
            site_info = await analyzer.analyze(
                url=str(request.url),
                deep_scan=request.deep_scan
            )

            return AnalyzeResponse(
                success=True,
                data=site_info,
                message="Site analysis completed successfully"
            )

    except httpx.HTTPStatusError as e:
        return AnalyzeResponse(
            success=False,
            error=f"HTTP error occurred: {e.response.status_code}",
            message="Failed to access the site"
        )

    except httpx.RequestError as e:
        return AnalyzeResponse(
            success=False,
            error=f"Request error: {str(e)}",
            message="Failed to connect to the site"
        )

    except Exception as e:
        return AnalyzeResponse(
            success=False,
            error=str(e),
            message="An error occurred during site analysis"
        )


@router.get("/analyze/{url:path}", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_wordpress_site_get(url: str, deep_scan: bool = False):
    """
    Analyze a WordPress site using GET method (convenience endpoint).

    This is a convenience endpoint that allows analyzing a site via GET request.
    For more control, use the POST endpoint instead.

    Args:
        url: The WordPress site URL to analyze
        deep_scan: Whether to perform a deep scan (default: False)

    Returns:
        AnalyzeResponse with detected site information

    Example:
        ```
        GET /api/v1/wordpress/analyze/https://example.com?deep_scan=false
        ```
    """
    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        async with WordPressAnalyzer() as analyzer:
            site_info = await analyzer.analyze(url=url, deep_scan=deep_scan)

            return AnalyzeResponse(
                success=True,
                data=site_info,
                message="Site analysis completed successfully"
            )

    except httpx.HTTPStatusError as e:
        return AnalyzeResponse(
            success=False,
            error=f"HTTP error occurred: {e.response.status_code}",
            message="Failed to access the site"
        )

    except httpx.RequestError as e:
        return AnalyzeResponse(
            success=False,
            error=f"Request error: {str(e)}",
            message="Failed to connect to the site"
        )

    except Exception as e:
        return AnalyzeResponse(
            success=False,
            error=str(e),
            message="An error occurred during site analysis"
        )
