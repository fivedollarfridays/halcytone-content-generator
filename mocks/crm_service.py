#!/usr/bin/env python3
"""
Mock CRM Service for Halcytone Content Generator
Simulates CRM API for dry run testing without external dependencies
Port: 8001
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-crm")

app = FastAPI(
    title="Mock CRM Service",
    version="1.0.0",
    description="Mock CRM API for Halcytone Content Generator dry run testing",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request/Response Models
class EmailRequest(BaseModel):
    subject: str
    html_content: str
    text_content: Optional[str] = None
    recipients: Optional[List[str]] = None
    campaign_id: Optional[str] = None
    sender_email: Optional[str] = "noreply@halcytone.com"
    metadata: Optional[Dict[str, Any]] = {}

class EmailResponse(BaseModel):
    message_id: str
    status: str
    recipients_count: int
    timestamp: datetime
    campaign_id: Optional[str] = None

class ContactRequest(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class ContactResponse(BaseModel):
    contact_id: str
    email: str
    status: str
    created_at: datetime

class CampaignRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class CampaignResponse(BaseModel):
    campaign_id: str
    name: str
    status: str
    created_at: datetime

# Mock Database
mock_emails = []
mock_contacts = {}
mock_campaigns = {}

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()

    # Log request
    logger.info(f"Mock CRM Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Mock CRM Response: {response.status_code} - {process_time:.3f}s")

    return response

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mock-crm",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# Email Endpoints
@app.post("/api/v1/email/send", response_model=EmailResponse)
async def send_email(request: EmailRequest):
    """Simulate email sending with various test scenarios"""

    # Simulate error scenarios
    if "error" in request.subject.lower():
        raise HTTPException(status_code=500, detail="Simulated CRM error: Email sending failed")

    if "timeout" in request.subject.lower():
        raise HTTPException(status_code=408, detail="Simulated timeout error")

    if "invalid" in request.subject.lower():
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Simulate slow response
    if "slow" in request.subject.lower():
        await asyncio.sleep(2)

    # Generate mock response
    message_id = str(uuid.uuid4())
    recipients_count = len(request.recipients) if request.recipients else 100

    # Store email for reporting
    email_record = {
        "message_id": message_id,
        "subject": request.subject,
        "recipients_count": recipients_count,
        "campaign_id": request.campaign_id,
        "timestamp": datetime.utcnow(),
        "status": "sent"
    }
    mock_emails.append(email_record)

    logger.info(f"Mock email sent: {message_id} to {recipients_count} recipients")

    return EmailResponse(
        message_id=message_id,
        status="sent",
        recipients_count=recipients_count,
        timestamp=datetime.utcnow(),
        campaign_id=request.campaign_id
    )

@app.get("/api/v1/email/{message_id}/status")
async def get_email_status(message_id: str):
    """Get email delivery status"""

    # Find email in mock database
    email = next((e for e in mock_emails if e["message_id"] == message_id), None)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Simulate delivery status progression
    statuses = ["sent", "delivered", "opened", "clicked"]
    import random
    status = random.choice(statuses)

    return {
        "message_id": message_id,
        "status": status,
        "timestamp": email["timestamp"],
        "events": [
            {"event": "sent", "timestamp": email["timestamp"]},
            {"event": "delivered", "timestamp": email["timestamp"]},
        ]
    }

# Contact Management Endpoints
@app.post("/api/v1/contacts", response_model=ContactResponse)
async def create_contact(request: ContactRequest):
    """Create a new contact"""

    contact_id = str(uuid.uuid4())
    contact = {
        "contact_id": contact_id,
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "tags": request.tags or [],
        "metadata": request.metadata or {},
        "created_at": datetime.utcnow(),
        "status": "active"
    }

    mock_contacts[contact_id] = contact
    logger.info(f"Mock contact created: {contact_id} - {request.email}")

    return ContactResponse(
        contact_id=contact_id,
        email=request.email,
        status="active",
        created_at=datetime.utcnow()
    )

@app.get("/api/v1/contacts/count")
async def get_contact_count():
    """Get total contact statistics"""
    return {
        "total": 5432,
        "active": 4821,
        "unsubscribed": 611,
        "bounced": 89,
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/contacts")
async def list_contacts(limit: int = 100, offset: int = 0):
    """List contacts with pagination"""
    contacts_list = list(mock_contacts.values())[offset:offset+limit]
    return {
        "contacts": contacts_list,
        "total": len(mock_contacts),
        "limit": limit,
        "offset": offset
    }

# Campaign Management Endpoints
@app.post("/api/v1/campaigns", response_model=CampaignResponse)
async def create_campaign(request: CampaignRequest):
    """Create a new email campaign"""

    campaign_id = str(uuid.uuid4())
    campaign = {
        "campaign_id": campaign_id,
        "name": request.name,
        "description": request.description,
        "tags": request.tags or [],
        "metadata": request.metadata or {},
        "created_at": datetime.utcnow(),
        "status": "draft"
    }

    mock_campaigns[campaign_id] = campaign
    logger.info(f"Mock campaign created: {campaign_id} - {request.name}")

    return CampaignResponse(
        campaign_id=campaign_id,
        name=request.name,
        status="draft",
        created_at=datetime.utcnow()
    )

@app.get("/api/v1/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(campaign_id: str):
    """Get campaign performance analytics"""

    if campaign_id not in mock_campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Generate mock analytics
    import random
    return {
        "campaign_id": campaign_id,
        "sent": random.randint(1000, 5000),
        "delivered": random.randint(900, 4500),
        "opened": random.randint(200, 2000),
        "clicked": random.randint(50, 500),
        "unsubscribed": random.randint(1, 50),
        "bounced": random.randint(10, 100),
        "open_rate": round(random.uniform(0.15, 0.45), 3),
        "click_rate": round(random.uniform(0.02, 0.15), 3),
        "last_updated": datetime.utcnow().isoformat()
    }

# Reporting Endpoints
@app.get("/api/v1/reports/emails")
async def get_email_reports(days: int = 7):
    """Get email sending reports for last N days"""
    return {
        "period_days": days,
        "total_emails": len(mock_emails),
        "emails_by_day": [
            {"date": "2025-01-24", "sent": 1250, "delivered": 1180, "opened": 520},
            {"date": "2025-01-23", "sent": 890, "delivered": 845, "opened": 380},
            {"date": "2025-01-22", "sent": 1100, "delivered": 1050, "opened": 470},
        ],
        "top_subjects": [
            {"subject": "Weekly Breathscape Update", "sent": 500, "open_rate": 0.42},
            {"subject": "New Meditation Techniques", "sent": 350, "open_rate": 0.38},
        ]
    }

# Administrative Endpoints
@app.get("/api/v1/stats")
async def get_service_stats():
    """Get mock service statistics"""
    return {
        "service": "mock-crm",
        "uptime": "healthy",
        "requests_handled": len(mock_emails) + len(mock_contacts) + len(mock_campaigns),
        "emails_sent": len(mock_emails),
        "contacts_created": len(mock_contacts),
        "campaigns_created": len(mock_campaigns),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.delete("/api/v1/test-data")
async def clear_test_data():
    """Clear all mock test data"""
    global mock_emails, mock_contacts, mock_campaigns

    mock_emails.clear()
    mock_contacts.clear()
    mock_campaigns.clear()

    logger.info("All mock test data cleared")
    return {"status": "success", "message": "All test data cleared"}

if __name__ == "__main__":
    logger.info("Starting Mock CRM Service on port 8001")
    uvicorn.run(
        "crm_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )