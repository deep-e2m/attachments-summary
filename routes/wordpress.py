"""
WordPress analyzer API routes.
"""
from fastapi import APIRouter, HTTPException, status
import httpx

from schemas import AnalyzeResponse
from services import WordPressAnalyzer


router = APIRouter(prefix="/api/v1/wordpress", tags=["WordPress"])


@router.get("/analyze/{url:path}", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_wordpress_site(url: str):
    """
    Analyze a WordPress site and extract comprehensive information.

    Detects WordPress version, active theme, active plugins with descriptions, and site metadata.
    No authentication required.

    Args:
        url: The WordPress site URL to analyze

    Returns:
        AnalyzeResponse with detected site information

    Example:
        GET /api/v1/wordpress/analyze/https://wordpress.org
    """
    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        async with WordPressAnalyzer() as analyzer:
            site_info = await analyzer.analyze(url=url, deep_scan=True)

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
