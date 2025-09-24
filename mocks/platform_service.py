#!/usr/bin/env python3
"""
Mock Platform Service for Halcytone Content Generator
Simulates Platform API for dry run testing without external dependencies
Port: 8002
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import asyncio
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-platform")

app = FastAPI(
    title="Mock Platform Service",
    version="1.0.0",
    description="Mock Platform API for Halcytone Content Generator dry run testing",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request/Response Models
class ContentPublishRequest(BaseModel):
    title: str
    content: str
    content_type: str  # "web_update", "blog_post", "newsletter", "social_post"
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []
    publish_immediately: Optional[bool] = True
    scheduled_at: Optional[datetime] = None

class ContentPublishResponse(BaseModel):
    content_id: str
    url: str
    status: str
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None

class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []

class SocialPostRequest(BaseModel):
    platform: str  # "twitter", "linkedin", "facebook"
    content: str
    media_urls: Optional[List[str]] = []
    scheduled_at: Optional[datetime] = None
    hashtags: Optional[List[str]] = []

class SocialPostResponse(BaseModel):
    post_id: str
    platform: str
    url: str
    status: str
    posted_at: Optional[datetime] = None

class WebhookRequest(BaseModel):
    event_type: str
    content_id: str
    data: Dict[str, Any]

# Mock Database
mock_content = {}
mock_social_posts = {}
mock_analytics = {}

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()

    # Log request
    logger.info(f"Mock Platform Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Mock Platform Response: {response.status_code} - {process_time:.3f}s")

    return response

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mock-platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# Content Publishing Endpoints
@app.post("/api/v1/content/publish", response_model=ContentPublishResponse)
async def publish_content(request: ContentPublishRequest):
    """Simulate content publishing with various test scenarios"""

    # Simulate error scenarios
    if "error" in request.title.lower():
        raise HTTPException(status_code=400, detail="Invalid content format")

    if "forbidden" in request.title.lower():
        raise HTTPException(status_code=403, detail="Content violates platform policies")

    if "timeout" in request.title.lower():
        raise HTTPException(status_code=408, detail="Publishing timeout")

    # Simulate slow publishing
    if "slow" in request.title.lower():
        await asyncio.sleep(3)

    # Generate content ID and URL
    content_id = str(uuid.uuid4())
    published_at = datetime.utcnow() if request.publish_immediately else None
    scheduled_at = request.scheduled_at if not request.publish_immediately else None

    # Determine status
    if "draft" in request.title.lower():
        status = "draft"
    elif not request.publish_immediately and request.scheduled_at:
        status = "scheduled"
    else:
        status = "published"

    # Store content in mock database
    content_record = {
        "content_id": content_id,
        "title": request.title,
        "content": request.content,
        "content_type": request.content_type,
        "status": status,
        "metadata": request.metadata or {},
        "tags": request.tags or [],
        "created_at": datetime.utcnow(),
        "published_at": published_at,
        "scheduled_at": scheduled_at,
        "url": f"https://halcytone.com/content/{content_id}"
    }
    mock_content[content_id] = content_record

    logger.info(f"Mock content published: {content_id} - {request.title} - {status}")

    return ContentPublishResponse(
        content_id=content_id,
        url=f"https://halcytone.com/content/{content_id}",
        status=status,
        published_at=published_at,
        scheduled_at=scheduled_at
    )

@app.get("/api/v1/content/{content_id}")
async def get_content(content_id: str):
    """Get content by ID"""

    if content_id not in mock_content:
        raise HTTPException(status_code=404, detail="Content not found")

    return mock_content[content_id]

@app.put("/api/v1/content/{content_id}")
async def update_content(content_id: str, request: ContentUpdateRequest):
    """Update existing content"""

    if content_id not in mock_content:
        raise HTTPException(status_code=404, detail="Content not found")

    content = mock_content[content_id]

    # Update fields if provided
    if request.title:
        content["title"] = request.title
    if request.content:
        content["content"] = request.content
    if request.metadata:
        content["metadata"].update(request.metadata)
    if request.tags:
        content["tags"] = request.tags

    content["updated_at"] = datetime.utcnow()
    mock_content[content_id] = content

    logger.info(f"Mock content updated: {content_id}")

    return content

@app.delete("/api/v1/content/{content_id}")
async def delete_content(content_id: str):
    """Delete content"""

    if content_id not in mock_content:
        raise HTTPException(status_code=404, detail="Content not found")

    del mock_content[content_id]
    logger.info(f"Mock content deleted: {content_id}")

    return {"status": "success", "message": "Content deleted"}

# Social Media Endpoints
@app.post("/api/v1/social/post", response_model=SocialPostResponse)
async def post_social_content(request: SocialPostRequest):
    """Post content to social media platforms"""

    # Simulate platform-specific errors
    if request.platform not in ["twitter", "linkedin", "facebook"]:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    if "banned" in request.content.lower():
        raise HTTPException(status_code=403, detail="Content violates platform policies")

    # Generate post ID
    post_id = str(uuid.uuid4())
    posted_at = datetime.utcnow() if not request.scheduled_at else None

    # Generate platform-specific URL
    platform_urls = {
        "twitter": f"https://twitter.com/halcytone/status/{post_id}",
        "linkedin": f"https://linkedin.com/company/halcytone/posts/{post_id}",
        "facebook": f"https://facebook.com/halcytone/posts/{post_id}"
    }

    # Store social post
    post_record = {
        "post_id": post_id,
        "platform": request.platform,
        "content": request.content,
        "media_urls": request.media_urls or [],
        "hashtags": request.hashtags or [],
        "status": "scheduled" if request.scheduled_at else "posted",
        "created_at": datetime.utcnow(),
        "posted_at": posted_at,
        "scheduled_at": request.scheduled_at,
        "url": platform_urls.get(request.platform, f"https://{request.platform}.com/post/{post_id}")
    }
    mock_social_posts[post_id] = post_record

    logger.info(f"Mock social post created: {post_id} on {request.platform}")

    return SocialPostResponse(
        post_id=post_id,
        platform=request.platform,
        url=post_record["url"],
        status=post_record["status"],
        posted_at=posted_at
    )

@app.get("/api/v1/social/{post_id}")
async def get_social_post(post_id: str):
    """Get social media post by ID"""

    if post_id not in mock_social_posts:
        raise HTTPException(status_code=404, detail="Social post not found")

    return mock_social_posts[post_id]

# Analytics Endpoints
@app.get("/api/v1/analytics/content/{content_id}")
async def get_content_analytics(content_id: str):
    """Get content performance analytics"""

    if content_id not in mock_content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Generate mock analytics
    import random

    analytics = {
        "content_id": content_id,
        "views": random.randint(500, 5000),
        "unique_views": random.randint(400, 4500),
        "engagement_rate": round(random.uniform(0.02, 0.15), 3),
        "avg_time_on_page": random.randint(30, 300),
        "bounce_rate": round(random.uniform(0.20, 0.80), 3),
        "social_shares": random.randint(5, 150),
        "comments": random.randint(0, 50),
        "likes": random.randint(10, 200),
        "last_updated": datetime.utcnow().isoformat(),
        "traffic_sources": {
            "organic": random.randint(100, 1000),
            "social": random.randint(50, 500),
            "direct": random.randint(20, 200),
            "referral": random.randint(10, 100)
        }
    }

    mock_analytics[content_id] = analytics
    return analytics

@app.get("/api/v1/analytics/social/{post_id}")
async def get_social_analytics(post_id: str):
    """Get social media post analytics"""

    if post_id not in mock_social_posts:
        raise HTTPException(status_code=404, detail="Social post not found")

    import random
    post = mock_social_posts[post_id]

    # Platform-specific mock analytics
    platform_multipliers = {
        "twitter": {"likes": 50, "shares": 10, "comments": 5},
        "linkedin": {"likes": 20, "shares": 5, "comments": 8},
        "facebook": {"likes": 30, "shares": 15, "comments": 12}
    }

    multiplier = platform_multipliers.get(post["platform"], {"likes": 25, "shares": 8, "comments": 6})

    return {
        "post_id": post_id,
        "platform": post["platform"],
        "impressions": random.randint(1000, 10000),
        "reach": random.randint(800, 8000),
        "engagement": random.randint(50, 500),
        "likes": random.randint(10, multiplier["likes"]),
        "shares": random.randint(2, multiplier["shares"]),
        "comments": random.randint(0, multiplier["comments"]),
        "clicks": random.randint(5, 100),
        "engagement_rate": round(random.uniform(0.01, 0.08), 3),
        "last_updated": datetime.utcnow().isoformat()
    }

# Content Management Endpoints
@app.get("/api/v1/content")
async def list_content(
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List content with filtering and pagination"""

    content_list = list(mock_content.values())

    # Apply filters
    if content_type:
        content_list = [c for c in content_list if c.get("content_type") == content_type]

    if status:
        content_list = [c for c in content_list if c.get("status") == status]

    # Apply pagination
    paginated_content = content_list[offset:offset + limit]

    return {
        "content": paginated_content,
        "total": len(content_list),
        "limit": limit,
        "offset": offset,
        "filters": {
            "content_type": content_type,
            "status": status
        }
    }

# Webhook Endpoints
@app.post("/api/v1/webhooks/content")
async def handle_content_webhook(request: WebhookRequest):
    """Handle content update webhooks"""

    logger.info(f"Mock webhook received: {request.event_type} for {request.content_id}")

    # Simulate webhook processing
    if request.event_type == "content.published":
        # Update content status if exists
        if request.content_id in mock_content:
            mock_content[request.content_id]["status"] = "published"
            mock_content[request.content_id]["published_at"] = datetime.utcnow()

    elif request.event_type == "content.updated":
        # Update content metadata
        if request.content_id in mock_content:
            mock_content[request.content_id]["updated_at"] = datetime.utcnow()

    return {"status": "success", "message": "Webhook processed"}

# Administrative Endpoints
@app.get("/api/v1/stats")
async def get_service_stats():
    """Get mock service statistics"""
    return {
        "service": "mock-platform",
        "uptime": "healthy",
        "content_published": len(mock_content),
        "social_posts": len(mock_social_posts),
        "total_requests": len(mock_content) + len(mock_social_posts),
        "content_by_type": {
            "web_update": len([c for c in mock_content.values() if c.get("content_type") == "web_update"]),
            "blog_post": len([c for c in mock_content.values() if c.get("content_type") == "blog_post"]),
            "newsletter": len([c for c in mock_content.values() if c.get("content_type") == "newsletter"]),
            "social_post": len([c for c in mock_content.values() if c.get("content_type") == "social_post"])
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.delete("/api/v1/test-data")
async def clear_test_data():
    """Clear all mock test data"""
    global mock_content, mock_social_posts, mock_analytics

    mock_content.clear()
    mock_social_posts.clear()
    mock_analytics.clear()

    logger.info("All mock test data cleared")
    return {"status": "success", "message": "All test data cleared"}

if __name__ == "__main__":
    logger.info("Starting Mock Platform Service on port 8002")
    uvicorn.run(
        "platform_service:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )