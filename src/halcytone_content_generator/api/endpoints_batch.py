"""
Batch Content Generation Endpoints
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import ValidationError

from ..schemas.content import (
    BatchContentRequest, BatchContentResponse, BatchContentItem,
    BatchScheduleRequest, BatchScheduleResponse, BatchStatusResponse,
    Content, SocialPost, NewsletterContent, WebUpdateContent
)
from ..services.content_assembler_v2 import EnhancedContentAssembler
from ..services.document_fetcher import DocumentFetcher
from ..services.publishers.email_publisher import EmailPublisher
from ..services.publishers.web_publisher import WebPublisher
from ..services.publishers.social_publisher import SocialPublisher
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/batch", tags=["batch"])

def get_content_assembler():
    """Dependency to get content assembler instance"""
    return EnhancedContentAssembler()

def get_document_fetcher():
    """Dependency to get document fetcher instance"""
    settings = get_settings()
    return DocumentFetcher(settings)

def get_publishers():
    """Get all available publishers"""
    settings = get_settings()
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

@router.post("/generateBatch", response_model=BatchContentResponse)
async def generate_batch_content(
    period: str = Query(..., description="Time period: 'day', 'week', 'month'"),
    channels: List[str] = Query(..., description="Channels to generate content for"),
    count: int = Query(None, description="Number of content items to generate"),
    dry_run: bool = Query(False, description="Preview mode without actual generation"),
    template_variety: bool = Query(True, description="Use different templates across items"),
    include_scheduling: bool = Query(True, description="Include optimal scheduling recommendations"),
    content_themes: List[str] = Query(None, description="Specific content themes to focus on"),
    assembler: EnhancedContentAssembler = Depends(get_content_assembler),
    fetcher: DocumentFetcher = Depends(get_document_fetcher)
):
    """
    Generate batch content for multiple channels and time periods
    """
    settings = get_settings()

    try:
        # Validate request parameters
        if period not in ['day', 'week', 'month']:
            raise HTTPException(status_code=400, detail="Period must be 'day', 'week', or 'month'")

        valid_channels = ['email', 'web', 'social']
        invalid_channels = [ch for ch in channels if ch not in valid_channels]
        if invalid_channels:
            raise HTTPException(status_code=400, detail=f"Invalid channels: {invalid_channels}")

        # Enforce batch limits
        max_items = count or settings.BATCH_MAX_ITEMS
        if max_items > settings.BATCH_MAX_ITEMS:
            raise HTTPException(
                status_code=400,
                detail=f"Count exceeds maximum batch size ({settings.BATCH_MAX_ITEMS})"
            )

        # Create batch request
        batch_request = BatchContentRequest(
            period=period,
            channels=channels,
            count=max_items,
            dry_run=dry_run or settings.DRY_RUN,
            template_variety=template_variety,
            include_scheduling=include_scheduling,
            content_themes=content_themes
        )

        logger.info(f"Starting batch generation: {batch_request.model_dump()}")

        # Generate batch ID
        batch_id = f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Calculate date range based on period
        start_date = datetime.now()
        if period == 'day':
            end_date = start_date + timedelta(days=1)
            item_count = min(max_items, len(channels) * 3)  # 3 items per channel per day
        elif period == 'week':
            end_date = start_date + timedelta(weeks=1)
            item_count = min(max_items, len(channels) * 7)  # 1 item per channel per day
        else:  # month
            end_date = start_date + timedelta(days=30)
            item_count = min(max_items, len(channels) * 15)  # ~0.5 items per channel per day

        # Fetch fresh content from living document
        logger.info("Fetching content from living document")
        try:
            document_content = await fetcher.fetch_content()
        except Exception as e:
            logger.warning(f"Failed to fetch document content: {e}, using fallback data")
            # Provide fallback data for testing/development
            document_content = {
                'breathscape': [{'title': 'Test Update', 'content': 'Test content', 'category': 'breathscape'}],
                'hardware': [{'title': 'Hardware News', 'content': 'Hardware content', 'category': 'hardware'}],
                'tips': [{'title': 'Wellness Tip', 'content': 'Tip content', 'category': 'tips'}],
                'vision': [{'title': 'Vision', 'content': 'Vision content', 'category': 'vision'}]
            }

        # Get available publishers
        publishers = get_publishers()

        # Generate content items
        batch_items = []
        generated_count = 0

        for i in range(item_count):
            if generated_count >= max_items:
                break

            # Rotate through channels
            channel = channels[i % len(channels)]

            try:
                # Generate content for this channel
                if channel == 'email':
                    # Choose template for variety
                    if template_variety:
                        templates = ['modern', 'minimal', 'plain']
                        template_choice = templates[i % len(templates)]
                    else:
                        template_choice = 'modern'  # default template

                    newsletter_data = assembler.generate_newsletter(
                        document_content,
                        template=template_choice
                    )
                    newsletter_content = NewsletterContent(**newsletter_data)
                    content = Content.from_newsletter(
                        newsletter_content,
                        dry_run=batch_request.dry_run
                    )

                elif channel == 'web':
                    web_data = assembler.generate_web_update(
                        document_content,
                        seo_optimize=True
                    )
                    web_content = WebUpdateContent(**web_data)
                    content = Content.from_web_update(
                        web_content,
                        dry_run=batch_request.dry_run
                    )

                elif channel == 'social':
                    # Generate for specific platform
                    platforms = ['twitter', 'linkedin']
                    platform = platforms[i % len(platforms)]

                    # Generate posts for this platform only
                    social_posts = assembler.generate_social_posts(
                        document_content,
                        platforms=[platform]
                    )

                    if social_posts:
                        # Convert dict to SocialPost object
                        post_data = social_posts[0]  # Take first post
                        social_content = SocialPost(
                            platform=post_data['platform'],
                            content=post_data['content'],
                            hashtags=post_data.get('hashtags', []),
                            media_urls=post_data.get('media_urls', [])
                        )
                        content = Content.from_social_post(
                            social_content,
                            dry_run=batch_request.dry_run
                        )
                    else:
                        logger.warning(f"No social content generated for {platform}")
                        continue

                # Validate content with appropriate publisher
                publisher = publishers[channel]
                validation_result = await publisher.validate(content)

                if not validation_result.is_valid:
                    logger.warning(f"Content validation failed for {channel}: {validation_result.issues}")
                    continue

                # Calculate scheduled time if requested
                scheduled_time = None
                if include_scheduling:
                    # Distribute content over the time period
                    time_offset = timedelta(hours=i * 2)  # Spread items 2 hours apart
                    scheduled_time = start_date + time_offset

                # Estimate engagement score
                preview_result = await publisher.preview(content)
                estimated_engagement = preview_result.estimated_engagement or 0.05

                # Create batch item
                batch_item = BatchContentItem(
                    item_id=f"{batch_id}-{channel}-{generated_count:03d}",
                    content_type=channel,
                    content=content,
                    scheduled_for=scheduled_time,
                    priority=1 if channel == 'email' else 2,  # Email priority
                    estimated_engagement=estimated_engagement,
                    metadata={
                        "channel": channel,
                        "generation_index": generated_count,
                        "validation_passed": True,
                        "template_used": "varied" if template_variety else "default"
                    }
                )

                batch_items.append(batch_item)
                generated_count += 1

            except Exception as e:
                logger.error(f"Failed to generate content for {channel}: {e}")
                continue

        # Create scheduling plan if requested
        scheduling_plan = None
        if include_scheduling and batch_items:
            scheduling_plan = {
                "total_items": len(batch_items),
                "time_span": f"{start_date.isoformat()} to {end_date.isoformat()}",
                "distribution": _calculate_distribution(batch_items),
                "next_publish": batch_items[0].scheduled_for.isoformat() if batch_items[0].scheduled_for else None,
                "optimal_times": {
                    "email": "9:00 AM",
                    "web": "10:00 AM",
                    "social": "2:00 PM"
                }
            }

        # Calculate summary statistics
        channel_counts = {}
        for item in batch_items:
            channel_counts[item.content_type] = channel_counts.get(item.content_type, 0) + 1

        total_estimated_reach = sum(
            item.estimated_engagement * 1000  # Assume 1000 base reach
            for item in batch_items
        )

        summary = {
            "channels_generated": channel_counts,
            "total_items": len(batch_items),
            "time_period": period,
            "generation_success_rate": len(batch_items) / max_items if max_items > 0 else 0,
            "estimated_total_reach": int(total_estimated_reach),
            "dry_run_mode": batch_request.dry_run
        }

        logger.info(f"Batch generation completed: {summary}")

        return BatchContentResponse(
            batch_id=batch_id,
            status="completed",
            items=batch_items,
            summary=summary,
            scheduling_plan=scheduling_plan,
            dry_run=batch_request.dry_run,
            total_items=len(batch_items),
            estimated_reach=int(total_estimated_reach)
        )

    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except ValidationError as e:
        logger.error(f"Batch generation validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")

@router.post("/schedule/{batch_id}", response_model=BatchScheduleResponse)
async def schedule_batch(
    batch_id: str,
    request: BatchScheduleRequest
):
    """
    Schedule a previously generated batch for publication
    """
    # This would integrate with a job scheduler in a real implementation
    logger.info(f"Scheduling batch {batch_id}: {request.model_dump()}")

    if request.dry_run:
        return BatchScheduleResponse(
            batch_id=batch_id,
            scheduled_items=[],
            schedule_summary={"dry_run": True, "message": "Scheduling preview only"},
            dry_run=True
        )

    # Simulate scheduling
    return BatchScheduleResponse(
        batch_id=batch_id,
        scheduled_items=[f"{batch_id}-item-{i}" for i in range(5)],
        schedule_summary={
            "total_scheduled": 5,
            "next_execution": (datetime.now() + timedelta(minutes=30)).isoformat()
        },
        next_publish_time=datetime.now() + timedelta(minutes=30),
        dry_run=False
    )

@router.get("/status/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Get the current status of a batch
    """
    # This would query a job status store in a real implementation
    logger.info(f"Getting status for batch {batch_id}")

    return BatchStatusResponse(
        batch_id=batch_id,
        status="completed",
        items_total=10,
        items_published=8,
        items_pending=1,
        items_failed=1,
        last_updated=datetime.now(),
        errors=["Failed to publish social post to Instagram"]
    )

def _calculate_distribution(batch_items: List[BatchContentItem]) -> Dict[str, Any]:
    """Calculate time distribution of batch items"""
    if not batch_items:
        return {}

    scheduled_items = [item for item in batch_items if item.scheduled_for]
    if not scheduled_items:
        return {"message": "No scheduled items"}

    # Group by hour
    hourly_distribution = {}
    for item in scheduled_items:
        hour = item.scheduled_for.hour
        hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1

    return {
        "hourly_distribution": hourly_distribution,
        "peak_hour": max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None,
        "total_scheduled": len(scheduled_items)
    }