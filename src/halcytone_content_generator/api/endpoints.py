"""
API endpoints for content generation
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional
import logging

from ..config import Settings, get_settings
from ..schemas.content import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentPreview
)
from ..services.document_fetcher import DocumentFetcher
from ..services.content_assembler import ContentAssembler
from ..services.crm_client import CRMClient
from ..services.platform_client import PlatformClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content"])


@router.post("/generate-content", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
):
    """
    Generate and distribute content across all channels

    Args:
        request: Content generation parameters
        background_tasks: FastAPI background task handler
        settings: Application settings

    Returns:
        ContentGenerationResponse with status and results
    """
    try:
        # Step 1: Fetch living document content
        fetcher = DocumentFetcher(settings)
        content = await fetcher.fetch_content()
        logger.info(f"Fetched content with {sum(len(v) for v in content.values())} items")

        # Step 2: Assemble content for different channels
        assembler = ContentAssembler()
        newsletter = assembler.generate_newsletter(content)
        web_update = assembler.generate_web_update(content)
        social_posts = assembler.generate_social_posts(content)

        # If preview only, return without sending
        if request.preview_only:
            return ContentGenerationResponse(
                status="preview",
                newsletter=newsletter,
                web_update=web_update,
                social_posts=social_posts
            )

        results = {}

        # Step 3: Send newsletter via CRM
        if request.send_email and newsletter:
            crm_client = CRMClient(settings)
            email_result = await crm_client.send_newsletter(
                newsletter['subject'],
                newsletter['html'],
                newsletter['text']
            )
            results['email'] = email_result
            logger.info(f"Newsletter sent to {email_result.get('sent', 0)} recipients")

        # Step 4: Publish to website
        if request.publish_web and web_update:
            platform_client = PlatformClient(settings)
            web_result = await platform_client.publish_update(
                web_update['title'],
                web_update['content'],
                web_update['excerpt']
            )
            results['web'] = web_result
            logger.info(f"Web update published: {web_result.get('id')}")

        # Step 5: Social posts (for manual review initially)
        results['social'] = social_posts
        logger.info(f"Generated {len(social_posts)} social media posts")

        return ContentGenerationResponse(
            status="success",
            results=results,
            newsletter=newsletter if request.include_preview else None,
            web_update=web_update if request.include_preview else None,
            social_posts=social_posts if request.include_preview else None
        )

    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview", response_model=ContentPreview)
async def preview_content(
    settings: Settings = Depends(get_settings)
):
    """
    Preview content without generating or sending

    Returns:
        ContentPreview with latest content from living document
    """
    try:
        # Fetch and preview content
        fetcher = DocumentFetcher(settings)
        content = await fetcher.fetch_content()

        assembler = ContentAssembler()
        newsletter = assembler.generate_newsletter(content)
        web_update = assembler.generate_web_update(content)
        social_posts = assembler.generate_social_posts(content)

        return ContentPreview(
            newsletter=newsletter,
            web_update=web_update,
            social_posts=social_posts,
            content_summary={
                "breathscape": len(content.get('breathscape', [])),
                "hardware": len(content.get('hardware', [])),
                "tips": len(content.get('tips', [])),
                "vision": len(content.get('vision', []))
            }
        )

    except Exception as e:
        logger.error(f"Content preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status(settings: Settings = Depends(get_settings)):
    """
    Get service status and configuration

    Returns:
        Current service status and configuration state
    """
    return {
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT,
        "document_source": settings.LIVING_DOC_TYPE,
        "crm_configured": bool(settings.CRM_BASE_URL and settings.CRM_API_KEY),
        "platform_configured": bool(settings.PLATFORM_BASE_URL and settings.PLATFORM_API_KEY),
        "ai_enabled": bool(settings.OPENAI_API_KEY),
        "social_platforms": settings.SOCIAL_PLATFORMS
    }