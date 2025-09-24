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
    ContentPreview,
    Content,
    NewsletterContent,
    WebUpdateContent,
    SocialPost
)
from ..services.document_fetcher import DocumentFetcher
from ..services.content_assembler import ContentAssembler
from ..services.publishers.email_publisher import EmailPublisher
from ..services.publishers.web_publisher import WebPublisher
from ..services.publishers.social_publisher import SocialPublisher
from ..services.tone_manager import get_tone_manager
from ..services.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content"])


def get_publishers(settings: Settings):
    """Get all available publishers configured with settings"""
    config = {
        'crm_base_url': settings.CRM_BASE_URL,
        'crm_api_key': settings.CRM_API_KEY,
        'platform_base_url': settings.PLATFORM_BASE_URL,
        'platform_api_key': settings.PLATFORM_API_KEY,
        'dry_run': settings.DRY_RUN
    }

    return {
        'email': EmailPublisher(config),
        'web': WebPublisher(config),
        'social': SocialPublisher(config)
    }


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

        # Step 2: Get tone manager and select appropriate tone
        tone_manager = get_tone_manager()
        selected_tone = None

        if settings.TONE_SYSTEM_ENABLED:
            # Use tone from request or auto-select based on content
            if request.tone:
                selected_tone = tone_manager.get_tone_profile(request.tone)
            elif request.tone_combination:
                selected_tone = tone_manager.blend_tones(request.tone_combination)
            elif settings.TONE_AUTO_SELECTION:
                # Auto-select tone based on content type
                selected_tone = tone_manager.select_tone(
                    content_type="newsletter",
                    channel="email",
                    context={"content_items": len(content.get('breathscape', [])) + len(content.get('hardware', []))}
                )
            else:
                selected_tone = tone_manager.get_tone_profile(settings.DEFAULT_TONE)

            logger.info(f"Selected tone: {selected_tone.name if selected_tone else 'None'}")

        # Step 3: Assemble content for different channels with tone support
        assembler = ContentAssembler()

        # Generate newsletter with tone
        email_tone = selected_tone
        if request.per_channel_tones and 'email' in request.per_channel_tones:
            email_tone = tone_manager.get_tone_profile(request.per_channel_tones['email'])
        newsletter_data = assembler.generate_newsletter(content)

        # Generate web update with tone
        web_tone = selected_tone
        if request.per_channel_tones and 'web' in request.per_channel_tones:
            web_tone = tone_manager.get_tone_profile(request.per_channel_tones['web'])
        web_update_data = assembler.generate_web_update(content)

        # Generate social posts with tone
        social_tone = selected_tone
        if request.per_channel_tones and 'social' in request.per_channel_tones:
            social_tone = tone_manager.get_tone_profile(request.per_channel_tones['social'])
        social_posts_data = assembler.generate_social_posts(content)

        # Convert to Pydantic objects
        newsletter = NewsletterContent(**newsletter_data) if newsletter_data else None
        web_update = WebUpdateContent(**web_update_data) if web_update_data else None
        social_posts = [SocialPost(**post) for post in social_posts_data] if social_posts_data else []

        # If preview only, return without sending
        if request.preview_only:
            return ContentGenerationResponse(
                status="preview",
                newsletter=newsletter,
                web_update=web_update,
                social_posts=social_posts,
                results={
                    'tone_system': {
                        'enabled': settings.TONE_SYSTEM_ENABLED,
                        'selected_tone': selected_tone.name if selected_tone else None,
                        'per_channel_tones': request.per_channel_tones or {},
                        'auto_selection': settings.TONE_AUTO_SELECTION
                    }
                }
            )

        # Get publishers
        publishers = get_publishers(settings)
        results = {}

        # Step 3: Send newsletter via Email Publisher
        if request.send_email and newsletter:
            email_publisher = publishers['email']
            email_content = Content.from_newsletter(newsletter, dry_run=settings.DRY_RUN)

            # Validate content
            validation_result = await email_publisher.validate(email_content)
            if not validation_result.is_valid:
                logger.warning(f"Email validation issues: {validation_result.issues}")
                results['email'] = {"status": "validation_failed", "issues": validation_result.issues}
            else:
                # Publish email
                publish_result = await email_publisher.publish(email_content)
                results['email'] = {
                    "status": publish_result.status.value,
                    "message": publish_result.message,
                    "external_id": publish_result.external_id,
                    "metadata": publish_result.metadata
                }
                logger.info(f"Newsletter published: {publish_result.message}")

        # Step 4: Publish to website via Web Publisher
        if request.publish_web and web_update:
            web_publisher = publishers['web']
            web_content = Content.from_web_update(web_update, dry_run=settings.DRY_RUN)

            # Validate content
            validation_result = await web_publisher.validate(web_content)
            if not validation_result.is_valid:
                logger.warning(f"Web validation issues: {validation_result.issues}")
                results['web'] = {"status": "validation_failed", "issues": validation_result.issues}
            else:
                # Publish web content
                publish_result = await web_publisher.publish(web_content)
                results['web'] = {
                    "status": publish_result.status.value,
                    "message": publish_result.message,
                    "external_id": publish_result.external_id,
                    "metadata": publish_result.metadata
                }
                logger.info(f"Web update published: {publish_result.message}")

        # Step 5: Process social posts via Social Publisher
        if request.generate_social and social_posts:
            social_publisher = publishers['social']
            social_results = []

            for post in social_posts:
                social_content = Content.from_social_post(post, dry_run=settings.DRY_RUN)

                # Validate content
                validation_result = await social_publisher.validate(social_content)
                if not validation_result.is_valid:
                    logger.warning(f"Social validation issues for {post.platform}: {validation_result.issues}")
                    social_results.append({
                        "platform": post.platform,
                        "status": "validation_failed",
                        "issues": validation_result.issues
                    })
                else:
                    # Publish social content
                    publish_result = await social_publisher.publish(social_content)
                    social_results.append({
                        "platform": post.platform,
                        "status": publish_result.status.value,
                        "message": publish_result.message,
                        "external_id": publish_result.external_id,
                        "metadata": publish_result.metadata
                    })

            results['social'] = {
                "posts": social_results,
                "total_posts": len(social_posts),
                "platforms": list(set(post.platform for post in social_posts))
            }
            logger.info(f"Processed {len(social_posts)} social media posts")

        # Step 6: Handle cache invalidation if enabled
        if settings.CACHE_INVALIDATION_ENABLED and request.invalidate_cache:
            try:
                cache_manager = get_cache_manager()
                cache_targets = request.cache_targets or ['local', 'cdn'] if settings.CDN_ENABLED else ['local']

                from ..services.cache_manager import InvalidationRequest, CacheTarget
                invalidation_request = InvalidationRequest(
                    targets=[CacheTarget(target) for target in cache_targets],
                    patterns=settings.CACHE_AUTO_INVALIDATE_PATTERNS,
                    reason="Content generation completed",
                    initiated_by="content_generation_api"
                )

                invalidation_result = await cache_manager.invalidate_cache(invalidation_request)
                results['cache_invalidation'] = {
                    "status": invalidation_result.status.value,
                    "targets_processed": list(invalidation_result.targets_processed.keys()),
                    "keys_invalidated": invalidation_result.keys_invalidated,
                    "request_id": invalidation_result.request_id
                }
                logger.info(f"Cache invalidation completed: {invalidation_result.request_id}")
            except Exception as e:
                logger.error(f"Cache invalidation failed: {e}")
                results['cache_invalidation'] = {
                    "status": "failed",
                    "error": str(e)
                }

        # Add tone information to results
        results['tone_system'] = {
            'enabled': settings.TONE_SYSTEM_ENABLED,
            'selected_tone': selected_tone.name if selected_tone else None,
            'per_channel_tones': request.per_channel_tones or {},
            'auto_selection': settings.TONE_AUTO_SELECTION
        }

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
    tone: Optional[str] = None,
    settings: Settings = Depends(get_settings)
):
    """
    Preview content without generating or sending

    Args:
        tone: Optional tone to apply (professional, encouraging, medical_scientific)
        settings: Application settings

    Returns:
        ContentPreview with latest content from living document
    """
    try:
        # Fetch and preview content
        fetcher = DocumentFetcher(settings)
        content = await fetcher.fetch_content()

        # Get tone manager and select tone if enabled
        selected_tone = None
        if settings.TONE_SYSTEM_ENABLED:
            tone_manager = get_tone_manager()
            if tone:
                selected_tone = tone_manager.get_tone_profile(tone)
            elif settings.TONE_AUTO_SELECTION:
                selected_tone = tone_manager.select_tone("newsletter", "email")
            else:
                selected_tone = tone_manager.get_tone_profile(settings.DEFAULT_TONE)

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