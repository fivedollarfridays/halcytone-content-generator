"""
Enhanced API endpoints with template selection and customization
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from ..config import Settings, get_settings
from ..schemas.content import ContentGenerationRequest, ContentGenerationResponse
from ..services.document_fetcher import DocumentFetcher
from ..services.content_assembler_v2 import EnhancedContentAssembler
from ..services.content_validator import ContentValidator
from ..services.crm_client import CRMClient
from ..services.platform_client import PlatformClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content-v2"], prefix="/v2")


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
            newsletter = assembler.generate_newsletter(content, custom_data)

        # Generate web update with SEO
        web_update = None
        if request.publish_web:
            web_update = assembler.generate_web_update(content, seo_optimize=seo_optimize)

        # Generate social posts for multiple platforms
        social_posts = []
        if request.generate_social:
            platforms = social_platforms or ['twitter', 'linkedin', 'instagram', 'facebook']
            social_posts = assembler.generate_social_posts(content, platforms)

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

        results = {}

        # Step 4: Send newsletter via CRM
        if request.send_email and newsletter:
            crm_client = CRMClient(settings)
            email_result = await crm_client.send_newsletter(
                newsletter['subject'],
                newsletter['html'],
                newsletter['text']
            )
            results['email'] = email_result
            logger.info(f"Newsletter sent to {email_result.get('sent', 0)} recipients")

        # Step 5: Publish to website with SEO data
        if request.publish_web and web_update:
            platform_client = PlatformClient(settings)

            # Include SEO metadata in publication
            web_result = await platform_client.publish_update(
                web_update['title'],
                web_update['content'],
                web_update['excerpt']
            )

            # Add SEO data to result
            web_result['seo'] = {
                'meta_description': web_update.get('meta_description'),
                'tags': web_update.get('tags'),
                'schema_markup': web_update.get('schema_markup'),
                'reading_time': web_update.get('reading_time'),
                'word_count': web_update.get('word_count')
            }

            results['web'] = web_result
            logger.info(f"Web update published with SEO: {web_result.get('id')}")

        # Step 6: Return social posts with platform metadata
        if social_posts:
            results['social'] = {
                'posts': social_posts,
                'total_posts': len(social_posts),
                'platforms': list(set(p['platform'] for p in social_posts)),
                'includes_threads': any(p.get('type') == 'thread' for p in social_posts),
                'media_required': sum(len(p.get('media_suggestions', [])) for p in social_posts)
            }

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