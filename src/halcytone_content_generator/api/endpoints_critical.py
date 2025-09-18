"""
Critical API endpoints for production deployment
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from ..config import Settings, get_settings
from ..services.crm_client_v2 import EnhancedCRMClient
from ..services.content_sync import ContentSyncService, Channel, SyncStatus
from ..services.monitoring import monitoring_service
from ..core.auth_middleware import get_api_key, validate_api_key_dep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["critical"])


# Request/Response Models
class NewsletterSendRequest(BaseModel):
    """Request model for sending newsletter"""
    subject: str
    html_content: str
    text_content: str
    recipient_filter: Optional[Dict] = None
    test_mode: bool = False
    schedule_time: Optional[datetime] = None


class NewsletterSendResponse(BaseModel):
    """Response model for newsletter send"""
    status: str
    job_id: str
    recipients: int
    scheduled: bool = False
    scheduled_time: Optional[datetime] = None


class ContentSyncRequest(BaseModel):
    """Request model for content sync"""
    document_id: str
    channels: List[str]
    schedule_time: Optional[datetime] = None
    correlation_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class ContentSyncResponse(BaseModel):
    """Response model for content sync"""
    job_id: str
    status: str
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    channels: List[str]
    correlation_id: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict] = None
    errors: List[str] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    """Response model for metrics"""
    total_jobs: int
    active_jobs: int
    status_breakdown: Dict[str, int]
    channel_breakdown: Dict[str, int]
    success_rate: float
    last_sync_times: Dict[str, str]


# Initialize services
_crm_client = None
_sync_service = None


def get_crm_client(settings: Settings = Depends(get_settings)) -> EnhancedCRMClient:
    """Get CRM client instance"""
    global _crm_client
    if _crm_client is None:
        _crm_client = EnhancedCRMClient(settings)
    return _crm_client


def get_sync_service(settings: Settings = Depends(get_settings)) -> ContentSyncService:
    """Get content sync service instance"""
    global _sync_service
    if _sync_service is None:
        _sync_service = ContentSyncService(settings)
    return _sync_service


@router.post("/v1/newsletter/send", response_model=NewsletterSendResponse)
async def send_newsletter(
    request: NewsletterSendRequest,
    background_tasks: BackgroundTasks,
    crm_client: EnhancedCRMClient = Depends(get_crm_client),
    api_key_data: Dict = Depends(validate_api_key_dep)
):
    """
    Send newsletter via CRM integration

    This endpoint sends a newsletter to recipients via the CRM system.
    Supports test mode and scheduled sending.
    """
    try:
        logger.info(f"Sending newsletter: {request.subject}")

        # Send newsletter through CRM
        job = await crm_client.send_newsletter_bulk(
            subject=request.subject,
            html=request.html_content,
            text=request.text_content,
            recipient_filter=request.recipient_filter,
            test_mode=request.test_mode,
            scheduled_time=request.schedule_time
        )

        # Record metrics
        monitoring_service.record_event(
            event_type=monitoring_service.EventType.EMAIL_SENT,
            operation="newsletter_send",
            metadata={
                "job_id": job.job_id,
                "recipients": job.total_recipients,
                "test_mode": request.test_mode
            },
            success=True
        )

        return NewsletterSendResponse(
            status="success",
            job_id=job.job_id,
            recipients=job.total_recipients,
            scheduled=request.schedule_time is not None,
            scheduled_time=request.schedule_time
        )

    except Exception as e:
        logger.error(f"Failed to send newsletter: {str(e)}")
        monitoring_service.record_event(
            event_type=monitoring_service.EventType.ERROR,
            operation="newsletter_send",
            error=str(e),
            success=False
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/content/sync", response_model=ContentSyncResponse)
async def sync_content(
    request: ContentSyncRequest,
    background_tasks: BackgroundTasks,
    sync_service: ContentSyncService = Depends(get_sync_service),
    api_key_data: Dict = Depends(validate_api_key_dep)
):
    """
    Synchronize content across multiple channels

    This endpoint fetches content from a document source and synchronizes
    it across specified channels (email, website, social media).
    """
    try:
        logger.info(f"Syncing content from {request.document_id} to {request.channels}")

        # Convert channel strings to Channel enums
        channels = []
        for channel_str in request.channels:
            try:
                if channel_str == "email":
                    channels.append(Channel.EMAIL)
                elif channel_str == "website":
                    channels.append(Channel.WEBSITE)
                elif channel_str == "twitter":
                    channels.append(Channel.SOCIAL_TWITTER)
                elif channel_str == "linkedin":
                    channels.append(Channel.SOCIAL_LINKEDIN)
                elif channel_str == "facebook":
                    channels.append(Channel.SOCIAL_FACEBOOK)
                else:
                    logger.warning(f"Unknown channel: {channel_str}")
            except Exception as e:
                logger.error(f"Error processing channel {channel_str}: {e}")

        # Start sync job
        job = await sync_service.sync_content(
            document_id=request.document_id,
            channels=channels,
            correlation_id=request.correlation_id,
            schedule_time=request.schedule_time
        )

        # Process job in background
        if not request.schedule_time or request.schedule_time <= datetime.now():
            background_tasks.add_task(
                sync_service._execute_sync_job,
                job
            )

        return ContentSyncResponse(
            job_id=job.job_id,
            status=job.status.value,
            created_at=job.created_at,
            scheduled_for=job.scheduled_for,
            channels=[c.value for c in job.channels],
            correlation_id=job.correlation_id
        )

    except Exception as e:
        logger.error(f"Failed to sync content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    sync_service: ContentSyncService = Depends(get_sync_service),
    api_key_data: Dict = Depends(validate_api_key_dep)
):
    """
    Get status of a sync job

    Returns the current status and results of a content sync job.
    """
    job = sync_service.get_job_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        created_at=job.created_at,
        completed_at=job.completed_at,
        results=job.results,
        errors=job.errors
    )


@router.get("/v2/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    limit: int = 10,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    sync_service: ContentSyncService = Depends(get_sync_service),
    api_key_data: Dict = Depends(validate_api_key_dep)
):
    """
    List recent sync jobs

    Returns a list of recent content sync jobs with optional filtering.
    """
    jobs = sync_service.get_recent_jobs(limit)

    # Apply filters
    if status:
        jobs = [j for j in jobs if j.status.value == status]
    if channel:
        channel_enum = Channel[channel.upper()]
        jobs = [j for j in jobs if channel_enum in j.channels]

    return [
        JobStatusResponse(
            job_id=job.job_id,
            status=job.status.value,
            created_at=job.created_at,
            completed_at=job.completed_at,
            results=job.results,
            errors=job.errors
        )
        for job in jobs
    ]


@router.get("/v2/metrics", response_model=MetricsResponse)
async def get_metrics(
    sync_service: ContentSyncService = Depends(get_sync_service),
    api_key_data: Dict = Depends(validate_api_key_dep)
):
    """
    Get service metrics and statistics

    Returns overall metrics for the content generation service.
    """
    stats = sync_service.get_sync_statistics()

    return MetricsResponse(
        total_jobs=stats['total_jobs'],
        active_jobs=stats['active_jobs'],
        status_breakdown=stats['status_breakdown'],
        channel_breakdown=stats['channel_breakdown'],
        success_rate=stats['success_rate'],
        last_sync_times=stats.get('last_sync_times', {})
    )


@router.post("/v2/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    sync_service: ContentSyncService = Depends(get_sync_service),
    api_key_data: Dict = Depends(validate_api_key_dep)
):
    """
    Retry a failed or partial job

    Creates a new job to retry a previously failed sync operation.
    """
    original_job = sync_service.get_job_status(job_id)

    if not original_job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if original_job.status not in [SyncStatus.FAILED, SyncStatus.PARTIAL]:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} cannot be retried (status: {original_job.status.value})"
        )

    # Create retry job
    new_job = await sync_service.sync_content(
        document_id=original_job.source_document_id,
        channels=original_job.channels,
        correlation_id=f"retry_{original_job.correlation_id}" if original_job.correlation_id else None
    )

    # Process in background
    background_tasks.add_task(
        sync_service._execute_sync_job,
        new_job
    )

    return {
        "new_job_id": new_job.job_id,
        "status": "pending",
        "original_job_id": job_id,
        "created_at": new_job.created_at.isoformat()
    }


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format

    Returns metrics formatted for Prometheus scraping.
    """
    metrics_text = monitoring_service.export_metrics_prometheus()
    return metrics_text