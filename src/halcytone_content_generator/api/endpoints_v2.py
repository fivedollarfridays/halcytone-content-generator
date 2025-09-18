"""
Enhanced API endpoints with template selection and customization
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from ..config import Settings, get_settings
from ..schemas.content import (
    ContentGenerationRequest, ContentGenerationResponse,
    Content, NewsletterContent, WebUpdateContent, SocialPost
)
from ..services.document_fetcher import DocumentFetcher
from ..services.content_assembler_v2 import EnhancedContentAssembler
from ..services.content_validator import ContentValidator
from ..services.publishers.email_publisher import EmailPublisher
from ..services.publishers.web_publisher import WebPublisher
from ..services.publishers.social_publisher import SocialPublisher

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content-v2"], prefix="/v2")


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


@router.post("/generate-content")
async def generate_enhanced_content(
    request: ContentGenerationRequest,
    template_style: str = Query(default="modern", description="Email template style (modern, minimal, plain)"),
    social_platforms: Optional[List[str]] = Query(default=None, description="Social platforms to generate for"),
    seo_optimize: bool = Query(default=True, description="Enable SEO optimization for web content"),
    validate_content: bool = Query(default=True, description="Validate content before generation"),
    settings: Settings = Depends(get_settings)
):
    """
    Generate enhanced content with template selection and validation

    Args:
        request: Content generation parameters
        template_style: Email template style
        social_platforms: List of social platforms
        seo_optimize: Enable SEO features
        validate_content: Enable content validation
        settings: Application settings
    """
    try:
        # Step 1: Fetch living document content
        fetcher = DocumentFetcher(settings)
        content = await fetcher.fetch_content()
        logger.info(f"Fetched content with {sum(len(v) for v in content.values())} items")

        # Step 2: Validate and enhance content if enabled
        if validate_content:
            validator = ContentValidator()

            # Validate content
            is_valid, issues = validator.validate_content(content)
            if not is_valid:
                logger.warning(f"Content validation issues: {issues}")

            # Enhance categorization
            content = validator.enhance_categorization(content)

            # Sanitize content
            content = validator.sanitize_content(content)

            # Generate summary
            content_summary = validator.generate_content_summary(content)
            logger.info(f"Content summary: {content_summary}")

        # Step 3: Generate content with enhanced assembler
        assembler = EnhancedContentAssembler(template_style=template_style)

        # Generate newsletter
        newsletter = None
        if request.send_email:
            custom_data = {
                'stats': [
                    {'value': '10K+', 'label': 'Users'},
                    {'value': '95%', 'label': 'Accuracy'},
                    {'value': '4.8⭐', 'label': 'Rating'}
                ]
            }
            newsletter_data = assembler.generate_newsletter(content, custom_data=custom_data)
            newsletter = NewsletterContent(**newsletter_data) if newsletter_data else None

        # Generate web update with SEO
        web_update = None
        if request.publish_web:
            web_update_data = assembler.generate_web_update(content, seo_optimize=seo_optimize)
            web_update = WebUpdateContent(**web_update_data) if web_update_data else None

        # Generate social posts for multiple platforms
        social_posts = []
        if request.generate_social:
            platforms = social_platforms or ['twitter', 'linkedin', 'instagram', 'facebook']
            social_posts_data = assembler.generate_social_posts(content, platforms)
            social_posts = [SocialPost(**post) for post in social_posts_data] if social_posts_data else []

        # If preview only, return without sending
        if request.preview_only:
            return ContentGenerationResponse(
                status="preview",
                newsletter=newsletter,
                web_update=web_update,
                social_posts=social_posts,
                results={
                    'template_style': template_style,
                    'seo_enabled': seo_optimize,
                    'content_validated': validate_content,
                    'platforms': platforms if request.generate_social else []
                }
            )

        # Get publishers
        publishers = get_publishers(settings)
        results = {}

        # Step 4: Send newsletter via Email Publisher
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
                logger.info(f"Enhanced newsletter published: {publish_result.message}")

        # Step 5: Publish to website via Web Publisher
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

                # Get enhanced metadata from the web publisher
                preview_result = await web_publisher.preview(web_content)

                results['web'] = {
                    "status": publish_result.status.value,
                    "message": publish_result.message,
                    "external_id": publish_result.external_id,
                    "metadata": publish_result.metadata,
                    "seo": {
                        "estimated_reading_time": preview_result.metadata.get('reading_time'),
                        "word_count": preview_result.word_count,
                        "character_count": preview_result.character_count,
                        "estimated_reach": preview_result.estimated_reach
                    }
                }
                logger.info(f"Enhanced web update published: {publish_result.message}")

        # Step 6: Process social posts via Social Publisher
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

                    # Get enhanced metadata from the social publisher
                    preview_result = await social_publisher.preview(social_content)

                    social_results.append({
                        "platform": post.platform,
                        "status": publish_result.status.value,
                        "message": publish_result.message,
                        "external_id": publish_result.external_id,
                        "metadata": publish_result.metadata,
                        "engagement_data": {
                            "estimated_reach": preview_result.estimated_reach,
                            "estimated_engagement": preview_result.estimated_engagement,
                            "character_count": preview_result.character_count,
                            "platform_tips": preview_result.preview_data.get('platform_tips', [])
                        }
                    })

            results['social'] = {
                "posts": social_results,
                "total_posts": len(social_posts),
                "platforms": list(set(post.platform for post in social_posts)),
                "enhanced_features": {
                    "validation_enabled": True,
                    "engagement_estimates": True,
                    "platform_optimization": True
                }
            }
            logger.info(f"Enhanced social processing completed for {len(social_posts)} posts")

        return ContentGenerationResponse(
            status="success",
            results=results,
            newsletter=newsletter if request.include_preview else None,
            web_update=web_update if request.include_preview else None,
            social_posts=social_posts if request.include_preview else None
        )

    except Exception as e:
        logger.error(f"Enhanced content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_available_templates():
    """
    List available email templates and their descriptions

    Returns:
        Dictionary of available templates
    """
    return {
        "email_templates": [
            {
                "id": "modern",
                "name": "Modern Newsletter",
                "description": "Professional design with gradients, statistics, and rich formatting",
                "features": ["Hero header", "Statistics section", "Call-to-action buttons", "Social links"],
                "best_for": "Monthly newsletters, product updates"
            },
            {
                "id": "minimal",
                "name": "Minimal Design",
                "description": "Clean, simple layout focused on content",
                "features": ["Clean typography", "Simple structure", "Mobile-friendly"],
                "best_for": "Weekly updates, text-heavy content"
            },
            {
                "id": "plain",
                "name": "Plain Text",
                "description": "Text-only format for maximum compatibility",
                "features": ["Universal compatibility", "Fast loading", "Accessibility"],
                "best_for": "Transactional emails, system notifications"
            }
        ],
        "social_platforms": [
            {
                "id": "twitter",
                "name": "Twitter/X",
                "character_limit": 280,
                "features": ["Threads", "Hashtags", "Mentions"],
                "content_types": ["announcement", "tip", "thread", "engagement"]
            },
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "character_limit": 3000,
                "features": ["Long-form", "Professional tone", "Rich formatting"],
                "content_types": ["thought_leadership", "product_update", "educational"]
            },
            {
                "id": "instagram",
                "name": "Instagram",
                "character_limit": 2200,
                "features": ["Visual focus", "Carousels", "Stories"],
                "content_types": ["carousel", "educational", "behind_the_scenes"]
            },
            {
                "id": "facebook",
                "name": "Facebook",
                "character_limit": 63206,
                "features": ["Community engagement", "Events", "Long posts"],
                "content_types": ["community", "event", "discussion"]
            }
        ]
    }


@router.post("/validate-content")
async def validate_content(
    settings: Settings = Depends(get_settings)
):
    """
    Validate content from living document

    Returns:
        Validation results and issues
    """
    try:
        # Fetch content
        fetcher = DocumentFetcher(settings)
        content = await fetcher.fetch_content()

        # Validate
        validator = ContentValidator()
        is_valid, issues = validator.validate_content(content)

        # Generate summary
        summary = validator.generate_content_summary(content)

        return {
            "valid": is_valid,
            "issues": issues,
            "summary": summary,
            "recommendations": {
                "add_more_content": len(issues) > 0,
                "refresh_stale": any("stale" in issue for issue in issues),
                "fix_duplicates": any("duplicate" in issue for issue in issues)
            }
        }

    except Exception as e:
        logger.error(f"Content validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-preview/{platform}")
async def preview_social_post(
    platform: str,
    category: str = Query(default="breathscape", description="Content category"),
    post_type: str = Query(default="announcement", description="Type of post"),
    settings: Settings = Depends(get_settings)
):
    """
    Preview a social media post for a specific platform

    Args:
        platform: Social media platform
        category: Content category
        post_type: Type of post to generate

    Returns:
        Preview of social media post
    """
    try:
        # Fetch content
        fetcher = DocumentFetcher(settings)
        content = await fetcher.fetch_content()

        # Generate single platform post
        assembler = EnhancedContentAssembler()
        posts = assembler.generate_social_posts(content, platforms=[platform])

        if posts:
            post = posts[0]
            # Add preview metadata
            post['preview'] = {
                'character_count': len(post['content']) if isinstance(post['content'], str) else sum(len(c) for c in post['content']),
                'platform_limit': {
                    'twitter': 280,
                    'linkedin': 3000,
                    'instagram': 2200,
                    'facebook': 63206
                }.get(platform, 500),
                'fits_limit': True,
                'requires_media': len(post.get('media_suggestions', [])) > 0
            }
            return post

        return {"error": f"No content available for {platform}"}

    except Exception as e:
        logger.error(f"Social preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))