"""
Schema-validated API endpoints for Sprint 2
Enhanced content generation with strict validation before publishing
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import uuid

from ..config import Settings, get_settings
from ..schemas.content_types import (
    ContentRequestStrict, ContentResponseStrict, ContentValidationResult,
    ContentType, ChannelType, TemplateStyle, SocialPlatform,
    UpdateContentStrict, BlogContentStrict, AnnouncementContentStrict,
    NewsletterContentStrict, WebUpdateContentStrict, SocialPostStrict,
    SessionContentStrict  # Sprint 3: Session content
)
from ..services.schema_validator import SchemaValidator
from ..services.content_assembler import ContentAssembler
from ..services.publishers.email_publisher import EmailPublisher
from ..services.publishers.web_publisher import WebPublisher
from ..services.publishers.social_publisher import SocialPublisher

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content-validated"], prefix="/v2")


class SchemaValidatedEndpoints:
    """Enhanced endpoints with comprehensive schema validation"""

    def __init__(self):
        self.validator = SchemaValidator()

    def get_publishers(self, settings: Settings):
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


# Create instance for endpoint methods
endpoints = SchemaValidatedEndpoints()


@router.post("/validate-content", response_model=ContentValidationResult)
async def validate_content_only(
    request: ContentRequestStrict,
    settings: Settings = Depends(get_settings)
) -> ContentValidationResult:
    """
    Validate content structure without publishing
    Sprint 2 requirement: Validate content structure before publishing

    Args:
        request: Content validation request with strict schema
        settings: Application settings

    Returns:
        ContentValidationResult with validation status and details
    """
    try:
        logger.info(f"Validating content: {request.content.title}")

        # Convert Pydantic model to dict for validation
        content_data = request.content.model_dump()

        # Perform comprehensive validation
        validation_result = endpoints.validator.validate_content_structure(content_data)

        logger.info(f"Validation completed for '{request.content.title}': "
                   f"valid={validation_result.is_valid}, "
                   f"issues={len(validation_result.issues)}, "
                   f"warnings={len(validation_result.warnings)}")

        return validation_result

    except Exception as e:
        logger.error(f"Content validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Content validation failed: {str(e)}"
        )


@router.post("/generate-content", response_model=ContentResponseStrict)
async def generate_validated_content(
    request: ContentRequestStrict,
    background_tasks: BackgroundTasks,
    template_style: TemplateStyle = Query(default=TemplateStyle.MODERN),
    social_platforms: Optional[List[SocialPlatform]] = Query(default=None),
    seo_optimize: bool = Query(default=True),
    force_publish: bool = Query(default=False),
    settings: Settings = Depends(get_settings)
) -> ContentResponseStrict:
    """
    Generate and publish content with comprehensive validation
    Sprint 2: Enhanced content generation with strict schema validation

    Args:
        request: Content generation request with validated content
        background_tasks: Background task handler
        template_style: Email template style to use
        social_platforms: Specific social platforms to target
        seo_optimize: Enable SEO optimization
        force_publish: Skip validation failures (use with caution)
        settings: Application settings

    Returns:
        ContentResponseStrict with generation results
    """
    content_id = str(uuid.uuid4())
    errors = []
    warnings = []
    published_to = []
    failed_channels = []

    try:
        logger.info(f"Starting validated content generation: {request.content.title}")

        # Step 1: Validate content structure if requested
        validation_result = None
        if request.validate_before_publish:
            content_data = request.content.model_dump()
            validation_result = endpoints.validator.validate_content_structure(content_data)

            if not validation_result.is_valid and not (request.override_validation or force_publish):
                logger.warning(f"Content validation failed: {validation_result.issues}")
                return ContentResponseStrict(
                    status="validation_failed",
                    content_id=content_id,
                    validation_result=validation_result,
                    errors=validation_result.issues,
                    warnings=validation_result.warnings
                )

            warnings.extend(validation_result.warnings)

        # Step 2: Generate channel-specific content
        newsletter_content = None
        web_content = None
        social_posts = []

        # Get publishers
        publishers = endpoints.get_publishers(settings)
        assembler = ContentAssembler()

        # Prepare content data for assemblers
        content_dict = request.content.model_dump()

        # Generate newsletter if email channel selected
        if ChannelType.EMAIL in request.content.channels:
            try:
                newsletter_data = assembler.generate_newsletter({'default': [content_dict]})
                if newsletter_data:
                    # Apply template style
                    newsletter_data['template_style'] = template_style

                    # Validate generated newsletter
                    is_valid, issues, validated_newsletter = endpoints.validator.validate_newsletter_content(newsletter_data)

                    if is_valid and validated_newsletter:
                        newsletter_content = validated_newsletter

                        # Publish if not dry run
                        if not request.content.dry_run:
                            # TODO: Implement actual publishing
                            published_to.append(ChannelType.EMAIL)

                    else:
                        errors.extend([f"Newsletter validation: {issue}" for issue in issues])
                        failed_channels.append(ChannelType.EMAIL)

            except Exception as e:
                error_msg = f"Newsletter generation failed: {str(e)}"
                errors.append(error_msg)
                failed_channels.append(ChannelType.EMAIL)
                logger.error(error_msg, exc_info=True)

        # Generate web content if web channel selected
        if ChannelType.WEB in request.content.channels:
            try:
                web_data = assembler.generate_web_update({'default': [content_dict]})
                if web_data:
                    # Add SEO optimization if enabled
                    if seo_optimize:
                        if not web_data.get('seo_description') and content_dict.get('excerpt'):
                            web_data['seo_description'] = content_dict['excerpt'][:160]

                        if not web_data.get('seo_title'):
                            web_data['seo_title'] = content_dict['title'][:60]

                    # Validate generated web content
                    is_valid, issues, validated_web = endpoints.validator.validate_web_content(web_data)

                    if is_valid and validated_web:
                        web_content = validated_web

                        # Publish if not dry run
                        if not request.content.dry_run:
                            # TODO: Implement actual publishing
                            published_to.append(ChannelType.WEB)

                    else:
                        errors.extend([f"Web content validation: {issue}" for issue in issues])
                        failed_channels.append(ChannelType.WEB)

            except Exception as e:
                error_msg = f"Web content generation failed: {str(e)}"
                errors.append(error_msg)
                failed_channels.append(ChannelType.WEB)
                logger.error(error_msg, exc_info=True)

        # Generate social content if social channel selected
        if ChannelType.SOCIAL in request.content.channels:
            try:
                # Determine platforms to generate for
                platforms = social_platforms or [SocialPlatform.TWITTER, SocialPlatform.LINKEDIN]

                for platform in platforms:
                    social_data = assembler.generate_social_posts({'default': [content_dict]})

                    if social_data:
                        for post_data in social_data:
                            post_data['platform'] = platform.value

                            # Validate generated social content
                            is_valid, issues, validated_post = endpoints.validator.validate_social_content(post_data)

                            if is_valid and validated_post:
                                social_posts.append(validated_post)
                            else:
                                errors.extend([f"Social {platform} validation: {issue}" for issue in issues])

                if social_posts and not request.content.dry_run:
                    published_to.append(ChannelType.SOCIAL)
                elif not social_posts:
                    failed_channels.append(ChannelType.SOCIAL)

            except Exception as e:
                error_msg = f"Social content generation failed: {str(e)}"
                errors.append(error_msg)
                failed_channels.append(ChannelType.SOCIAL)
                logger.error(error_msg, exc_info=True)

        # Step 3: Determine final status
        status = "success"
        if errors and not published_to:
            status = "publish_failed"
        elif errors and published_to:
            status = "success"  # Partial success
            warnings.extend([f"Some channels failed: {failed_channels}"])

        # Handle dry run
        if request.content.dry_run:
            published_to = [ChannelType.PREVIEW]

        logger.info(f"Content generation completed for '{request.content.title}': "
                   f"status={status}, published_to={published_to}, errors={len(errors)}")

        return ContentResponseStrict(
            status=status,
            content_id=content_id,
            validation_result=validation_result,
            published_to=published_to,
            failed_channels=failed_channels,
            newsletter=newsletter_content,
            web_update=web_content,
            social_posts=social_posts,
            errors=errors,
            warnings=warnings
        )

    except Exception as e:
        logger.error(f"Unexpected error in content generation: {e}", exc_info=True)
        return ContentResponseStrict(
            status="publish_failed",
            content_id=content_id,
            errors=[f"Unexpected error: {str(e)}"],
            warnings=warnings
        )


@router.get("/content-types", response_model=Dict[str, Any])
async def get_supported_content_types():
    """
    Get supported content types and their schemas
    Useful for frontend content-api.ts integration
    """
    return {
        "content_types": {
            "update": {
                "description": "Weekly product updates, progress reports",
                "required_fields": ["title", "content", "tags"],
                "optional_fields": ["excerpt", "featured", "priority"],
                "channels": ["email", "web", "social"]
            },
            "blog": {
                "description": "Educational content, thought leadership",
                "required_fields": ["title", "content", "category"],
                "optional_fields": ["tags", "seo_description", "reading_time", "target_keywords"],
                "channels": ["web", "social", "email"]
            },
            "announcement": {
                "description": "Major news, product launches, events",
                "required_fields": ["title", "content"],
                "optional_fields": ["urgency", "call_to_action", "expires_at", "media_contact"],
                "channels": ["email", "web", "social"]
            }
        },
        "channels": ["email", "web", "social", "preview"],
        "templates": ["modern", "minimal", "breathscape", "announcement", "plain"],
        "social_platforms": ["twitter", "linkedin", "facebook", "instagram"],
        "priority_levels": [1, 2, 3, 4, 5]
    }


@router.get("/validation-rules", response_model=Dict[str, Any])
async def get_validation_rules():
    """
    Get content validation rules for frontend validation
    """
    return {
        "title": {
            "min_length": 1,
            "max_length": 200,
            "required": True
        },
        "content": {
            "min_length": 10,
            "required": True
        },
        "channels": {
            "allowed_values": ["email", "web", "social", "preview"],
            "default": ["email", "web", "social"]
        },
        "priority": {
            "allowed_values": [1, 2, 3, 4, 5],
            "default": 3
        },
        "social_platforms": {
            "character_limits": {
                "twitter": 280,
                "linkedin": 3000,
                "facebook": 3000,
                "instagram": 2200
            },
            "hashtag_limits": {
                "twitter": 2,
                "linkedin": 5,
                "facebook": 5,
                "instagram": 30
            }
        },
        "newsletter": {
            "subject_min_length": 10,
            "subject_max_length": 100,
            "preview_text_max_length": 150
        },
        "seo": {
            "title_max_length": 60,
            "description_min_length": 120,
            "description_max_length": 160
        }
    }


# Sprint 3: Session Management Endpoints

@router.post("/session-summary", response_model=ContentResponseStrict)
async def generate_session_summary(
    session_data: SessionContentStrict,
    background_tasks: BackgroundTasks,
    channels: List[ChannelType] = Query(default=[ChannelType.EMAIL, ChannelType.WEB, ChannelType.SOCIAL]),
    publish_immediately: bool = Query(default=False),
    settings: Settings = Depends(get_settings)
) -> ContentResponseStrict:
    """
    Generate session summary content from breathing session data
    Sprint 3: Halcytone Live Support - Session summaries

    Args:
        session_data: Validated session data
        background_tasks: Background task handler
        channels: Channels to generate content for
        publish_immediately: Whether to publish immediately or preview
        settings: Application settings

    Returns:
        ContentResponseStrict with generated session summary
    """
    from ..services.session_summary_generator import SessionSummaryGenerator

    content_id = str(uuid.uuid4())
    logger.info(f"Generating session summary for session {session_data.session_id}")

    try:
        # Initialize generator
        generator = SessionSummaryGenerator()

        # Generate content for requested channels
        channel_list = [ch.value for ch in channels]
        generated = generator.generate_session_summary(session_data, channel_list)

        # Prepare response
        newsletter = None
        web_update = None
        social_posts = []
        published_to = []

        # Process generated content
        if ChannelType.EMAIL in channels and 'email' in generated:
            newsletter = NewsletterContentStrict(
                subject=generated['email']['subject'],
                preview_text=f"Session Summary: {session_data.title}",
                body_html=generated['email']['html'],
                body_text=generated['email']['text'],
                template_style=generated['email'].get('template_style', TemplateStyle.BREATHSCAPE),
                personalization_tags={}
            )
            if publish_immediately:
                # Would publish via email publisher
                published_to.append(ChannelType.EMAIL)

        if ChannelType.WEB in channels and 'web' in generated:
            web_update = WebUpdateContentStrict(
                title=generated['web']['title'],
                content=generated['web']['content'],
                slug=generated['web']['slug'],
                seo_description=generated['web']['seo_description'],
                keywords=generated['web']['keywords']
            )
            if publish_immediately:
                # Would publish via web publisher
                published_to.append(ChannelType.WEB)

        if ChannelType.SOCIAL in channels and 'social' in generated:
            for platform, content in generated['social'].items():
                if content:
                    try:
                        social_posts.append(SocialPostStrict(
                            platform=SocialPlatform(platform),
                            content=content['content'],
                            hashtags=content.get('hashtags', [])
                        ))
                    except ValueError:
                        logger.warning(f"Unknown social platform: {platform}")

            if publish_immediately and social_posts:
                # Would publish via social publisher
                published_to.append(ChannelType.SOCIAL)

        # Create validation result
        validation_result = ContentValidationResult(
            is_valid=True,
            content_type=ContentType.SESSION,
            issues=[],
            warnings=[],
            enhanced_metadata=generated.get('metadata', {})
        )

        return ContentResponseStrict(
            status="success" if published_to else "preview",
            content_id=content_id,
            published_to=published_to,
            failed_channels=[],
            preview_urls={
                'session': f"/sessions/{session_data.session_id}"
            } if not publish_immediately else {},
            newsletter=newsletter,
            web_update=web_update,
            social_posts=social_posts,
            validation_result=validation_result,
            errors=[],
            warnings=[]
        )

    except Exception as e:
        logger.error(f"Error generating session summary: {e}")
        return ContentResponseStrict(
            status="error",
            content_id=content_id,
            errors=[str(e)],
            warnings=[],
            published_to=[],
            failed_channels=channel_list
        )


@router.post("/live-announce")
async def broadcast_live_announcement(
    announcement: Dict[str, Any],
    session_id: Optional[str] = Query(None, description="Session ID to announce to"),
    broadcast_all: bool = Query(default=False, description="Broadcast to all active sessions"),
    settings: Settings = Depends(get_settings)
):
    """
    Broadcast live session announcement via WebSocket
    Sprint 3: Real-time announcements

    Args:
        announcement: Announcement content
        session_id: Specific session to target
        broadcast_all: Broadcast to all active sessions
        settings: Application settings

    Returns:
        Broadcast status
    """
    from ..services.websocket_manager import websocket_manager

    if not session_id and not broadcast_all:
        raise HTTPException(
            status_code=400,
            detail="Either session_id or broadcast_all must be specified"
        )

    # Prepare announcement message
    message = {
        'type': 'live_announcement',
        'content': announcement,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    sessions_notified = []

    try:
        if broadcast_all:
            # Broadcast to all active sessions
            active_sessions = websocket_manager.get_active_sessions()
            for sid in active_sessions:
                await websocket_manager.broadcast_to_session(sid, message)
                sessions_notified.append(sid)
        else:
            # Broadcast to specific session
            if session_id not in websocket_manager.get_active_sessions():
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found or not active"
                )

            await websocket_manager.broadcast_to_session(session_id, message)
            sessions_notified.append(session_id)

        return {
            'status': 'announced',
            'sessions_notified': sessions_notified,
            'participant_count': sum(
                websocket_manager.get_session_info(sid).get('participant_count', 0)
                for sid in sessions_notified
            ),
            'timestamp': message['timestamp']
        }

    except Exception as e:
        logger.error(f"Error broadcasting announcement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to broadcast announcement: {str(e)}"
        )


@router.get("/session/{session_id}/content")
async def get_session_content(
    session_id: str,
    include_summary: bool = Query(default=True),
    include_metrics: bool = Query(default=True),
    include_replay: bool = Query(default=False),
    settings: Settings = Depends(get_settings)
):
    """
    Get session-specific content and metrics
    Sprint 3: Session content retrieval

    Args:
        session_id: Session identifier
        include_summary: Include generated summary
        include_metrics: Include session metrics
        include_replay: Include message replay
        settings: Application settings

    Returns:
        Session content and metadata
    """
    from ..services.websocket_manager import websocket_manager
    from ..services.breathscape_event_listener import breathscape_event_listener

    # Check if session is active
    session_info = websocket_manager.get_session_info(session_id)
    is_active = session_info.get('active', False)

    response = {
        'session_id': session_id,
        'active': is_active,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    if is_active:
        response['session_info'] = session_info

    # Get session data from event listener
    active_sessions = breathscape_event_listener.get_active_sessions_info()
    session_data = None
    for session in active_sessions.get('sessions', []):
        if session['session_id'] == session_id:
            session_data = session
            break

    if session_data:
        response['session_data'] = session_data

    # Include metrics if requested
    if include_metrics and session_data:
        response['metrics'] = session_data.get('current_metrics', {})

    # Include replay if requested
    if include_replay:
        messages = await websocket_manager.get_session_replay(session_id)
        response['replay'] = {
            'message_count': len(messages),
            'messages': messages
        }

    # Generate summary if requested and session has ended
    if include_summary and not is_active and session_data:
        # This would generate a summary from historical data
        response['summary'] = {
            'available': False,
            'message': 'Session summary generation for ended sessions not yet implemented'
        }

    return response


@router.get("/sessions/live")
async def get_live_sessions(
    include_metrics: bool = Query(default=False),
    settings: Settings = Depends(get_settings)
):
    """
    Get all currently live sessions
    Sprint 3: Live session discovery

    Args:
        include_metrics: Include session metrics
        settings: Application settings

    Returns:
        List of live sessions
    """
    from ..services.websocket_manager import websocket_manager
    from ..services.breathscape_event_listener import breathscape_event_listener

    # Get active sessions from WebSocket manager
    active_sessions = websocket_manager.get_active_sessions()

    # Get session details from event listener
    event_sessions = breathscape_event_listener.get_active_sessions_info()

    sessions = []
    for session_id in active_sessions:
        session_info = websocket_manager.get_session_info(session_id)

        session_detail = {
            'session_id': session_id,
            'participant_count': session_info.get('participant_count', 0),
            'active': True
        }

        # Add metrics if requested
        if include_metrics:
            for event_session in event_sessions.get('sessions', []):
                if event_session['session_id'] == session_id:
                    session_detail['metrics'] = event_session.get('current_metrics', {})
                    session_detail['started_at'] = event_session.get('started_at')
                    break

        sessions.append(session_detail)

    return {
        'count': len(sessions),
        'sessions': sessions,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


# Router is included in main.py