"""
Content Generator API Client Examples
Demonstrates common usage patterns for the API client
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from .content_generator import ContentGeneratorClient
from ..api import APIError


# ========== Configuration ==========

def get_client() -> ContentGeneratorClient:
    """Create configured API client"""
    return ContentGeneratorClient(
        base_url=os.getenv("CONTENT_GENERATOR_API_URL", "http://localhost:8000"),
        api_key=os.getenv("CONTENT_GENERATOR_API_KEY"),
        timeout=60.0,
        max_retries=3
    )


# ========== Example 1: Health Check ==========

async def example_health_check():
    """Check API health and readiness"""
    print("\n=== Health Check Example ===")

    client = get_client()

    try:
        # Check health
        health = await client.health_check()
        print(f"✅ Health: {health.data}")

        # Check readiness
        ready = await client.readiness_check()
        print(f"✅ Readiness: {ready.data}")

        # Get metrics
        metrics = await client.metrics()
        print(f"📊 Metrics: {metrics.data}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 2: Simple Content Generation ==========

async def example_simple_generation():
    """Generate and send content using V1 API"""
    print("\n=== Simple Content Generation ===")

    client = get_client()

    try:
        # Generate and send email
        response = await client.generate_content(
            send_email=True,
            publish_web=False,
            document_id="gdocs:your-document-id",
            dry_run=False
        )

        if response.is_success():
            print("✅ Content generated successfully!")
            print(f"Response: {response.data}")
        else:
            print(f"❌ Generation failed: {response.error}")

    except APIError as e:
        print(f"❌ API Error: {e.message} (Status: {e.status_code})")


# ========== Example 3: Multi-Channel Sync ==========

async def example_multi_channel_sync():
    """Sync content across multiple channels using V2 API"""
    print("\n=== Multi-Channel Sync ===")

    client = get_client()
    correlation_id = client.generate_correlation_id()

    try:
        # Start sync job
        response = await client.sync_content(
            document_id="gdocs:your-doc-id",
            channels=["email", "website", "social_twitter", "social_linkedin"],
            dry_run=False,
            metadata={"source": "weekly_update", "author": "content_team"},
            correlation_id=correlation_id
        )

        job_id = response.data["job_id"]
        print(f"✅ Sync job created: {job_id}")
        print(f"🔗 Correlation ID: {correlation_id}")

        # Wait a moment for processing
        await asyncio.sleep(2)

        # Check job status
        status_response = await client.get_sync_job(job_id, correlation_id=correlation_id)
        job_status = status_response.data

        print(f"📊 Job Status: {job_status['status']}")
        print(f"📝 Results: {job_status.get('results', {})}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 4: Scheduled Content ==========

async def example_scheduled_content():
    """Schedule content for future publication"""
    print("\n=== Scheduled Content ===")

    client = get_client()

    try:
        # Schedule for tomorrow at 9 AM
        tomorrow_9am = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=1)

        response = await client.sync_content(
            document_id="gdocs:newsletter-doc",
            channels=["email"],
            schedule_time=tomorrow_9am,
            dry_run=False
        )

        print(f"✅ Content scheduled for: {tomorrow_9am}")
        print(f"📧 Job ID: {response.data['job_id']}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 5: Content Validation ==========

async def example_content_validation():
    """Validate content before publishing"""
    print("\n=== Content Validation ===")

    client = get_client()

    content_data = {
        "type": "update",
        "title": "Weekly Progress Update - March 2024",
        "content": "This week we achieved significant milestones...",
        "published": True,
        "featured": False,
        "tags": ["progress", "weekly", "development"],
        "excerpt": "Summary of this week's achievements"
    }

    try:
        # Validate content
        validation = await client.validate_content(
            content=content_data,
            content_type="update",
            strict=True
        )

        result = validation.data

        if result["is_valid"]:
            print("✅ Content is valid!")
            print(f"📊 Metadata: {result.get('enhanced_metadata', {})}")
        else:
            print("❌ Content has validation issues:")
            for issue in result["issues"]:
                print(f"  - {issue}")

        if result.get("warnings"):
            print("⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 6: Batch Generation ==========

async def example_batch_generation():
    """Generate multiple content items in batch"""
    print("\n=== Batch Generation ===")

    client = get_client()

    batch_requests = [
        {
            "document_id": "gdocs:doc1",
            "channels": ["email"],
            "dry_run": False
        },
        {
            "document_id": "gdocs:doc2",
            "channels": ["website", "social_linkedin"],
            "dry_run": False
        },
        {
            "document_id": "notion:page3",
            "channels": ["email", "website"],
            "dry_run": False
        }
    ]

    try:
        response = await client.batch_generate(
            requests=batch_requests,
            parallel=True,
            fail_fast=False
        )

        results = response.data["results"]

        print(f"✅ Successful: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"📊 Total: {results['total']}")

        if results.get("errors"):
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 7: Cache Management ==========

async def example_cache_management():
    """Manage content caches"""
    print("\n=== Cache Management ===")

    client = get_client()

    try:
        # Get cache statistics
        stats = await client.get_cache_stats()
        print(f"📊 Cache Stats:")
        print(f"  - Hit Rate: {stats.data.get('hit_rate', 'N/A')}")
        print(f"  - Total Keys: {stats.data.get('total_keys', 0)}")

        # Invalidate specific caches
        await client.invalidate_cache(
            cache_keys=["content:123", "content:456"]
        )
        print("✅ Invalidated specific cache keys")

        # Invalidate by pattern
        await client.invalidate_cache(
            pattern="content:blog:*"
        )
        print("✅ Invalidated cache by pattern")

        # Invalidate by tags
        await client.invalidate_cache(
            tags=["blog", "update"]
        )
        print("✅ Invalidated cache by tags")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 8: Analytics ==========

async def example_analytics():
    """Get content and email analytics"""
    print("\n=== Analytics ===")

    client = get_client()

    try:
        # Content analytics for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        analytics = await client.get_content_analytics(
            start_date=start_date,
            end_date=end_date,
            channels=["email", "website"]
        )

        print(f"📊 Content Analytics (Last 30 days):")
        data = analytics.data
        print(f"  - Total Views: {data.get('total_views', 0)}")
        print(f"  - Engagement Rate: {data.get('engagement_rate', 0)}%")

        # Email analytics
        email_stats = await client.get_email_analytics()
        email_data = email_stats.data

        print(f"\n📧 Email Analytics:")
        print(f"  - Open Rate: {email_data.get('open_rate', 0)}%")
        print(f"  - Click Rate: {email_data.get('click_rate', 0)}%")
        print(f"  - Total Sent: {email_data.get('total_sent', 0)}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Example 9: Error Handling ==========

async def example_error_handling():
    """Demonstrate error handling patterns"""
    print("\n=== Error Handling ===")

    client = get_client()

    try:
        # This will likely fail with authentication error
        await client.generate_content(send_email=True)

    except APIError as e:
        print(f"❌ API Error: {e.message}")

        # Handle specific HTTP status codes
        if e.status_code == 401:
            print("🔒 Authentication failed - check API key")
        elif e.status_code == 403:
            print("🚫 Forbidden - insufficient permissions")
        elif e.status_code == 429:
            print("⏳ Rate limit exceeded - retry later")
        elif e.status_code and e.status_code >= 500:
            print("🔥 Server error - service may be down")
        else:
            print(f"⚠️  Other error (code: {e.status_code})")

        # Access response details
        if e.response:
            print(f"Response details: {e.response}")


# ========== Example 10: Connection Test ==========

async def example_connection_test():
    """Test API connectivity"""
    print("\n=== Connection Test ===")

    client = get_client()

    if await client.test_connection():
        print("✅ API connection successful")
        print(f"🌐 Connected to: {client.base_url}")
    else:
        print("❌ API connection failed")
        print("Check:")
        print("  - Base URL is correct")
        print("  - API service is running")
        print("  - Network connectivity")


# ========== Example 11: Job Management ==========

async def example_job_management():
    """Manage sync jobs"""
    print("\n=== Job Management ===")

    client = get_client()

    try:
        # List all jobs
        jobs = await client.list_sync_jobs(limit=10)
        print(f"📋 Total Jobs: {len(jobs.data.get('jobs', []))}")

        # List pending jobs
        pending = await client.list_sync_jobs(status="pending", limit=10)
        print(f"⏳ Pending Jobs: {len(pending.data.get('jobs', []))}")

        # List completed jobs
        completed = await client.list_sync_jobs(status="completed", limit=10)
        print(f"✅ Completed Jobs: {len(completed.data.get('jobs', []))}")

        # Cancel a job (example)
        # job_id = "some-job-id"
        # await client.cancel_sync_job(job_id)
        # print(f"❌ Cancelled job: {job_id}")

    except APIError as e:
        print(f"❌ Error: {e.message}")


# ========== Main Runner ==========

async def run_all_examples():
    """Run all examples"""
    examples = [
        ("Health Check", example_health_check),
        ("Simple Generation", example_simple_generation),
        ("Multi-Channel Sync", example_multi_channel_sync),
        ("Scheduled Content", example_scheduled_content),
        ("Content Validation", example_content_validation),
        ("Batch Generation", example_batch_generation),
        ("Cache Management", example_cache_management),
        ("Analytics", example_analytics),
        ("Error Handling", example_error_handling),
        ("Connection Test", example_connection_test),
        ("Job Management", example_job_management),
    ]

    print("=" * 60)
    print("Content Generator API Client - Examples")
    print("=" * 60)

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())

    # Or run a specific example:
    # asyncio.run(example_health_check())
    # asyncio.run(example_multi_channel_sync())
