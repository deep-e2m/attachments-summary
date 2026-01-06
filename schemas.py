"""
Pydantic schemas for WordPress site data.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class WordPressVersion(BaseModel):
    """WordPress version information."""
    version: Optional[str] = Field(None, description="WordPress version number")
    detected_from: Optional[str] = Field(None, description="Source of version detection (meta, readme, feed, etc.)")


class PHPVersion(BaseModel):
    """PHP version information."""
    version: Optional[str] = Field(None, description="PHP version number")
    detected_from: Optional[str] = Field(None, description="Source of PHP version detection (headers, etc.)")


class ThemeInfo(BaseModel):
    """WordPress theme information."""
    name: Optional[str] = Field(None, description="Theme name")
    slug: Optional[str] = Field(None, description="Theme slug")
    version: Optional[str] = Field(None, description="Theme version")
    author: Optional[str] = Field(None, description="Theme author")
    template_url: Optional[str] = Field(None, description="Theme template URL")
    screenshot_url: Optional[str] = Field(None, description="Theme screenshot URL")


class PluginInfo(BaseModel):
    """WordPress plugin information."""
    name: Optional[str] = Field(None, description="Plugin name")
    version: Optional[str] = Field(None, description="Plugin version")
    description: Optional[str] = Field(None, description="Plugin description")


class ServerInfo(BaseModel):
    """Server information."""
    server: Optional[str] = Field(None, description="Server software (nginx, apache, etc.)")
    php_version: Optional[PHPVersion] = Field(None, description="PHP version details")
    powered_by: Optional[str] = Field(None, description="X-Powered-By header value")


class SecurityInfo(BaseModel):
    """Security-related information."""
    xmlrpc_enabled: bool = Field(False, description="Whether XML-RPC is enabled")
    rest_api_enabled: bool = Field(False, description="Whether REST API is accessible")
    directory_listing: bool = Field(False, description="Whether directory listing is enabled")
    readme_accessible: bool = Field(False, description="Whether readme.html is accessible")
    wp_json_exposed: bool = Field(False, description="Whether /wp-json/ endpoint is accessible")


class SiteMetadata(BaseModel):
    """General site metadata."""
    title: Optional[str] = Field(None, description="Site title")
    description: Optional[str] = Field(None, description="Site description")
    language: Optional[str] = Field(None, description="Site language")
    charset: Optional[str] = Field(None, description="Character encoding")
    generator: Optional[str] = Field(None, description="Generator meta tag value")


class WordPressSiteInfo(BaseModel):
    """Complete WordPress site information."""
    url: str = Field(..., description="The analyzed URL")
    is_wordpress: bool = Field(..., description="Whether the site is detected as WordPress")
    wordpress_version: Optional[WordPressVersion] = Field(None, description="WordPress version information")
    theme: Optional[ThemeInfo] = Field(None, description="Active theme information")
    plugins: List[PluginInfo] = Field(default_factory=list, description="Detected plugins")
    metadata: Optional[SiteMetadata] = Field(None, description="General site metadata")


class AnalyzeRequest(BaseModel):
    """Request model for analyzing a WordPress site."""
    url: HttpUrl = Field(..., description="The WordPress site URL to analyze")


class AnalyzeResponse(BaseModel):
    """Response model for WordPress site analysis."""
    success: bool = Field(..., description="Whether the analysis was successful")
    data: Optional[WordPressSiteInfo] = Field(None, description="The analyzed site information")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    message: Optional[str] = Field(None, description="Additional information")
