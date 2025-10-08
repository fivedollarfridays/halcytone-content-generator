"""
Comprehensive test suite for email_analytics service
Coverage target: 75%+
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from halcytone_content_generator.services.email_analytics import (
    EmailMetrics,
    EmailEvent,
    RecipientEngagement,
    EmailAnalyticsService,
    analytics_service
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def analytics():
    """Create fresh analytics service for each test"""
    return EmailAnalyticsService()


@pytest.fixture
def sample_campaign_id():
    """Sample campaign ID"""
    return "campaign_001"


@pytest.fixture
def sample_recipients():
    """Sample recipient list"""
    return [
        "user1@example.com",
        "user2@example.com",
        "user3@example.com",
        "user4@example.com",
        "user5@example.com"
    ]


# ============================================================================
# EmailMetrics Tests
# ============================================================================

class TestEmailMetrics:
    """Test EmailMetrics dataclass and calculated properties"""

    def test_email_metrics_initialization(self):
        """Test EmailMetrics initialization with defaults"""
        metrics = EmailMetrics(campaign_id="test_campaign")

        assert metrics.campaign_id == "test_campaign"
        assert metrics.total_sent == 0
        assert metrics.total_delivered == 0
        assert metrics.total_bounced == 0
        assert metrics.total_opened == 0
        assert metrics.unique_opens == 0
        assert metrics.total_clicked == 0
        assert metrics.unique_clicks == 0
        assert metrics.total_unsubscribed == 0
        assert metrics.total_complaints == 0

    def test_delivery_rate_calculation(self):
        """Test delivery rate calculation"""
        metrics = EmailMetrics(
            campaign_id="test",
            total_sent=100,
            total_delivered=95
        )
        assert metrics.delivery_rate == 95.0

    def test_delivery_rate_zero_sent(self):
        """Test delivery rate when no emails sent"""
        metrics = EmailMetrics(campaign_id="test", total_sent=0)
        assert metrics.delivery_rate == 0

    def test_open_rate_calculation(self):
        """Test open rate calculation"""
        metrics = EmailMetrics(
            campaign_id="test",
            total_delivered=100,
            unique_opens=30
        )
        assert metrics.open_rate == 30.0

    def test_open_rate_zero_delivered(self):
        """Test open rate when no emails delivered"""
        metrics = EmailMetrics(campaign_id="test", total_delivered=0)
        assert metrics.open_rate == 0

    def test_click_rate_calculation(self):
        """Test click-through rate calculation"""
        metrics = EmailMetrics(
            campaign_id="test",
            unique_opens=100,
            unique_clicks=25
        )
        assert metrics.click_rate == 25.0

    def test_click_rate_zero_opens(self):
        """Test click rate when no emails opened"""
        metrics = EmailMetrics(campaign_id="test", unique_opens=0)
        assert metrics.click_rate == 0

    def test_click_to_open_rate(self):
        """Test click-to-open rate (CTOR) calculation"""
        metrics = EmailMetrics(
            campaign_id="test",
            unique_opens=100,
            unique_clicks=30
        )
        assert metrics.click_to_open_rate == 30.0

    def test_unsubscribe_rate_calculation(self):
        """Test unsubscribe rate calculation"""
        metrics = EmailMetrics(
            campaign_id="test",
            total_delivered=1000,
            total_unsubscribed=5
        )
        assert metrics.unsubscribe_rate == 0.5

    def test_complaint_rate_calculation(self):
        """Test complaint rate calculation"""
        metrics = EmailMetrics(
            campaign_id="test",
            total_delivered=1000,
            total_complaints=2
        )
        assert metrics.complaint_rate == 0.2

    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all metrics and calculated rates"""
        metrics = EmailMetrics(
            campaign_id="test",
            total_sent=100,
            total_delivered=95,
            unique_opens=50,
            unique_clicks=20
        )

        result = metrics.to_dict()

        assert result['campaign_id'] == "test"
        assert result['total_sent'] == 100
        assert result['total_delivered'] == 95
        assert result['delivery_rate'] == 95.0
        assert result['open_rate'] == round((50/95)*100, 2)
        assert result['click_rate'] == round((20/50)*100, 2)
        assert 'unsubscribe_rate' in result
        assert 'complaint_rate' in result

    def test_to_dict_rounds_to_two_decimals(self):
        """Test that to_dict rounds rates to 2 decimal places"""
        metrics = EmailMetrics(
            campaign_id="test",
            total_sent=3,
            total_delivered=3,
            unique_opens=1
        )

        result = metrics.to_dict()
        # 1/3 * 100 = 33.333...
        assert result['open_rate'] == 33.33


# ============================================================================
# EmailEvent Tests
# ============================================================================

class TestEmailEvent:
    """Test EmailEvent dataclass"""

    def test_email_event_initialization(self):
        """Test EmailEvent initialization"""
        timestamp = datetime.now()
        event = EmailEvent(
            event_type="opened",
            email="test@example.com",
            campaign_id="campaign_001",
            timestamp=timestamp
        )

        assert event.event_type == "opened"
        assert event.email == "test@example.com"
        assert event.campaign_id == "campaign_001"
        assert event.timestamp == timestamp
        assert event.ip_address is None
        assert event.user_agent is None
        assert event.url is None
        assert event.metadata == {}

    def test_email_event_with_optional_fields(self):
        """Test EmailEvent with all optional fields"""
        timestamp = datetime.now()
        event = EmailEvent(
            event_type="clicked",
            email="test@example.com",
            campaign_id="campaign_001",
            timestamp=timestamp,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            url="https://example.com/link",
            metadata={"custom": "data"}
        )

        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"
        assert event.url == "https://example.com/link"
        assert event.metadata == {"custom": "data"}


# ============================================================================
# RecipientEngagement Tests
# ============================================================================

class TestRecipientEngagement:
    """Test RecipientEngagement dataclass and engagement scoring"""

    def test_recipient_engagement_initialization(self):
        """Test RecipientEngagement initialization"""
        recipient = RecipientEngagement(email="test@example.com")

        assert recipient.email == "test@example.com"
        assert recipient.campaigns_received == 0
        assert recipient.campaigns_opened == 0
        assert recipient.campaigns_clicked == 0
        assert recipient.last_open is None
        assert recipient.last_click is None
        assert recipient.engagement_score == 0.0
        assert recipient.status == "active"

    @patch('halcytone_content_generator.services.email_analytics.datetime')
    def test_engagement_score_calculation_high_engagement(self, mock_datetime):
        """Test engagement score for highly engaged recipient"""
        # Mock current time as 2025-10-07 12:00:00
        mock_now = datetime(2025, 10, 7, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        last_open = datetime(2025, 10, 5, 12, 0, 0)  # 2 days ago
        recipient = RecipientEngagement(
            email="test@example.com",
            campaigns_received=10,
            campaigns_opened=9,
            campaigns_clicked=7,
            last_open=last_open
        )

        score = recipient.calculate_engagement_score()

        # Open score: (9/10) * 40 = 36
        # Click score: (7/10) * 40 = 28
        # Recency score: < 7 days = 20
        # Total: 84
        assert score == 84.0
        assert recipient.engagement_score == 84.0

    @patch('halcytone_content_generator.services.email_analytics.datetime')
    def test_engagement_score_calculation_medium_engagement(self, mock_datetime):
        """Test engagement score for moderately engaged recipient"""
        # Mock current time as 2025-10-07 12:00:00
        mock_now = datetime(2025, 10, 7, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        last_open = datetime(2025, 9, 25, 12, 0, 0)  # 12 days ago
        recipient = RecipientEngagement(
            email="test@example.com",
            campaigns_received=10,
            campaigns_opened=5,
            campaigns_clicked=2,
            last_open=last_open
        )

        score = recipient.calculate_engagement_score()

        # Open score: (5/10) * 40 = 20
        # Click score: (2/10) * 40 = 8
        # Recency score: < 30 days = 15
        # Total: 43
        assert score == 43.0

    @patch('halcytone_content_generator.services.email_analytics.datetime')
    def test_engagement_score_calculation_low_engagement(self, mock_datetime):
        """Test engagement score for low engagement recipient"""
        # Mock current time as 2025-10-07 12:00:00
        mock_now = datetime(2025, 10, 7, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        last_open = datetime(2025, 7, 1, 12, 0, 0)  # 98 days ago
        recipient = RecipientEngagement(
            email="test@example.com",
            campaigns_received=10,
            campaigns_opened=1,
            campaigns_clicked=0,
            last_open=last_open
        )

        score = recipient.calculate_engagement_score()

        # Open score: (1/10) * 40 = 4
        # Click score: (0/10) * 40 = 0
        # Recency score: < 90 days = 5
        # Total: 9
        assert score == 9.0

    def test_engagement_score_zero_campaigns(self):
        """Test engagement score when no campaigns received"""
        recipient = RecipientEngagement(email="test@example.com")
        score = recipient.calculate_engagement_score()
        assert score == 0.0

    def test_engagement_score_no_recent_open(self):
        """Test engagement score with no recent opens"""
        recipient = RecipientEngagement(
            email="test@example.com",
            campaigns_received=10,
            campaigns_opened=5,
            campaigns_clicked=2,
            last_open=None  # No open tracked
        )

        score = recipient.calculate_engagement_score()

        # Open score: (5/10) * 40 = 20
        # Click score: (2/10) * 40 = 8
        # Recency score: no open = 0
        # Total: 28
        assert score == 28.0


# ============================================================================
# EmailAnalyticsService - Event Tracking Tests
# ============================================================================

class TestEmailAnalyticsServiceTracking:
    """Test event tracking methods"""

    def test_track_send_creates_metrics(self, analytics, sample_campaign_id, sample_recipients):
        """Test tracking email sends creates campaign metrics"""
        analytics.track_send(sample_campaign_id, sample_recipients)

        assert sample_campaign_id in analytics.metrics
        assert analytics.metrics[sample_campaign_id].total_sent == 5
        assert len(analytics.events) == 5

    def test_track_send_updates_recipient_engagement(self, analytics, sample_campaign_id):
        """Test tracking sends updates recipient engagement"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)

        assert "test@example.com" in analytics.recipients
        assert analytics.recipients["test@example.com"].campaigns_received == 1

    def test_track_send_increments_existing_campaign(self, analytics, sample_campaign_id):
        """Test tracking sends to existing campaign increments count"""
        analytics.track_send(sample_campaign_id, ["user1@example.com"])
        analytics.track_send(sample_campaign_id, ["user2@example.com"])

        assert analytics.metrics[sample_campaign_id].total_sent == 2

    def test_track_delivery(self, analytics, sample_campaign_id):
        """Test tracking email delivery"""
        analytics.track_send(sample_campaign_id, ["test@example.com"])
        analytics.track_delivery(sample_campaign_id, "test@example.com")

        assert analytics.metrics[sample_campaign_id].total_delivered == 1
        delivery_events = [e for e in analytics.events if e.event_type == "delivered"]
        assert len(delivery_events) == 1

    def test_track_bounce_hard(self, analytics, sample_campaign_id):
        """Test tracking hard bounce"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_bounce(sample_campaign_id, "test@example.com", "hard")

        assert analytics.metrics[sample_campaign_id].total_bounced == 1
        assert analytics.recipients["test@example.com"].status == "bounced"

    def test_track_bounce_soft(self, analytics, sample_campaign_id):
        """Test tracking soft bounce doesn't change status"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_bounce(sample_campaign_id, "test@example.com", "soft")

        assert analytics.metrics[sample_campaign_id].total_bounced == 1
        assert analytics.recipients["test@example.com"].status == "active"

    def test_track_open_first_time(self, analytics, sample_campaign_id):
        """Test tracking first email open"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_open(
            sample_campaign_id,
            "test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert analytics.metrics[sample_campaign_id].total_opened == 1
        assert analytics.metrics[sample_campaign_id].unique_opens == 1
        assert analytics.recipients["test@example.com"].campaigns_opened == 1
        assert analytics.recipients["test@example.com"].last_open is not None

    def test_track_open_duplicate(self, analytics, sample_campaign_id):
        """Test tracking duplicate opens increments total but not unique"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_open(sample_campaign_id, "test@example.com")
        analytics.track_open(sample_campaign_id, "test@example.com")

        assert analytics.metrics[sample_campaign_id].total_opened == 2
        assert analytics.metrics[sample_campaign_id].unique_opens == 1

    def test_track_click_first_time(self, analytics, sample_campaign_id):
        """Test tracking first link click"""
        recipients = ["test@example.com"]
        url = "https://example.com/article"
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_click(
            sample_campaign_id,
            "test@example.com",
            url,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert analytics.metrics[sample_campaign_id].total_clicked == 1
        assert analytics.metrics[sample_campaign_id].unique_clicks == 1
        assert analytics.link_clicks[sample_campaign_id][url] == 1
        assert analytics.recipients["test@example.com"].campaigns_clicked == 1
        assert analytics.recipients["test@example.com"].last_click is not None

    def test_track_click_duplicate(self, analytics, sample_campaign_id):
        """Test tracking duplicate clicks increments total but not unique"""
        recipients = ["test@example.com"]
        url = "https://example.com/article"
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_click(sample_campaign_id, "test@example.com", url)
        analytics.track_click(sample_campaign_id, "test@example.com", url)

        assert analytics.metrics[sample_campaign_id].total_clicked == 2
        assert analytics.metrics[sample_campaign_id].unique_clicks == 1
        assert analytics.link_clicks[sample_campaign_id][url] == 2

    def test_track_unsubscribe(self, analytics, sample_campaign_id):
        """Test tracking unsubscribe"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_unsubscribe(sample_campaign_id, "test@example.com")

        assert analytics.metrics[sample_campaign_id].total_unsubscribed == 1
        assert analytics.recipients["test@example.com"].status == "unsubscribed"

    def test_track_complaint(self, analytics, sample_campaign_id):
        """Test tracking spam complaint"""
        recipients = ["test@example.com"]
        analytics.track_send(sample_campaign_id, recipients)
        analytics.track_complaint(sample_campaign_id, "test@example.com")

        assert analytics.metrics[sample_campaign_id].total_complaints == 1
        assert analytics.recipients["test@example.com"].status == "complained"


# ============================================================================
# EmailAnalyticsService - Metrics Retrieval Tests
# ============================================================================

class TestEmailAnalyticsServiceMetrics:
    """Test metrics retrieval methods"""

    def test_get_campaign_metrics_existing(self, analytics, sample_campaign_id):
        """Test getting metrics for existing campaign"""
        analytics.track_send(sample_campaign_id, ["test@example.com"])
        analytics.track_delivery(sample_campaign_id, "test@example.com")
        analytics.track_open(sample_campaign_id, "test@example.com")

        metrics = analytics.get_campaign_metrics(sample_campaign_id)

        assert metrics is not None
        assert metrics['campaign_id'] == sample_campaign_id
        assert metrics['total_sent'] == 1
        assert metrics['total_delivered'] == 1
        assert metrics['total_opened'] == 1

    def test_get_campaign_metrics_with_popular_links(self, analytics, sample_campaign_id):
        """Test campaign metrics includes popular links"""
        analytics.track_send(sample_campaign_id, ["test@example.com"])
        analytics.track_click(sample_campaign_id, "test@example.com", "https://example.com/1")
        analytics.track_click(sample_campaign_id, "test@example.com", "https://example.com/1")
        analytics.track_click(sample_campaign_id, "test@example.com", "https://example.com/2")

        metrics = analytics.get_campaign_metrics(sample_campaign_id)

        assert 'popular_links' in metrics
        assert len(metrics['popular_links']) == 2
        assert metrics['popular_links'][0][0] == "https://example.com/1"
        assert metrics['popular_links'][0][1] == 2

    def test_get_campaign_metrics_nonexistent(self, analytics):
        """Test getting metrics for nonexistent campaign returns None"""
        metrics = analytics.get_campaign_metrics("nonexistent")
        assert metrics is None

    def test_get_recipient_engagement_existing(self, analytics, sample_campaign_id):
        """Test getting engagement data for existing recipient"""
        analytics.track_send(sample_campaign_id, ["test@example.com"])
        analytics.track_open(sample_campaign_id, "test@example.com")

        engagement = analytics.get_recipient_engagement("test@example.com")

        assert engagement is not None
        assert engagement['email'] == "test@example.com"
        assert engagement['campaigns_received'] == 1
        assert engagement['campaigns_opened'] == 1
        assert 'engagement_score' in engagement
        assert engagement['status'] == "active"

    def test_get_recipient_engagement_nonexistent(self, analytics):
        """Test getting engagement for nonexistent recipient returns None"""
        engagement = analytics.get_recipient_engagement("nonexistent@example.com")
        assert engagement is None

    def test_get_aggregate_metrics_multiple_campaigns(self, analytics):
        """Test aggregate metrics across multiple campaigns"""
        # Campaign 1
        analytics.track_send("campaign_1", ["user1@example.com", "user2@example.com"])
        analytics.track_delivery("campaign_1", "user1@example.com")
        analytics.track_delivery("campaign_1", "user2@example.com")
        analytics.track_open("campaign_1", "user1@example.com")

        # Campaign 2
        analytics.track_send("campaign_2", ["user3@example.com"])
        analytics.track_delivery("campaign_2", "user3@example.com")
        analytics.track_open("campaign_2", "user3@example.com")
        analytics.track_click("campaign_2", "user3@example.com", "https://example.com")

        aggregate = analytics.get_aggregate_metrics()

        assert aggregate['total_campaigns'] == 2
        assert aggregate['total_sent'] == 3
        assert aggregate['total_delivered'] == 3
        assert aggregate['total_opened'] == 2
        assert aggregate['total_clicked'] == 1
        assert 'avg_delivery_rate' in aggregate
        assert 'avg_open_rate' in aggregate

    def test_get_aggregate_metrics_engagement_segments(self, analytics):
        """Test aggregate metrics includes engagement segments"""
        # Create recipients with different engagement levels
        # Highly engaged
        analytics.track_send("c1", ["highly@example.com"])
        for _ in range(10):
            analytics.track_open("c1", "highly@example.com")
            analytics.track_click("c1", "highly@example.com", "https://example.com")

        # Inactive
        analytics.track_send("c2", ["inactive@example.com"])

        aggregate = analytics.get_aggregate_metrics()

        assert 'engagement_segments' in aggregate
        assert 'highly_engaged' in aggregate['engagement_segments']
        assert 'engaged' in aggregate['engagement_segments']
        assert 'at_risk' in aggregate['engagement_segments']
        assert 'inactive' in aggregate['engagement_segments']

    def test_get_aggregate_metrics_empty(self, analytics):
        """Test aggregate metrics with no campaigns"""
        aggregate = analytics.get_aggregate_metrics()

        assert aggregate['total_campaigns'] == 0
        assert aggregate['total_sent'] == 0
        assert aggregate['avg_delivery_rate'] == 0

    @patch('halcytone_content_generator.services.email_analytics.datetime')
    def test_get_time_based_metrics_hourly(self, mock_datetime, analytics, sample_campaign_id):
        """Test time-based metrics with hourly interval"""
        # First set of events at 10:00
        mock_now_10 = datetime(2025, 10, 7, 10, 0, 0)
        mock_datetime.now.return_value = mock_now_10

        analytics.track_send(sample_campaign_id, ["test@example.com"])
        analytics.track_open(sample_campaign_id, "test@example.com")
        analytics.track_click(sample_campaign_id, "test@example.com", "https://example.com")

        # Second set of events at 11:00
        mock_now_11 = datetime(2025, 10, 7, 11, 0, 0)
        mock_datetime.now.return_value = mock_now_11

        analytics.track_open(sample_campaign_id, "test@example.com")

        time_metrics = analytics.get_time_based_metrics(sample_campaign_id, "hourly")

        assert len(time_metrics) == 2
        assert time_metrics[0]['time'] == "2025-10-07 10:00"
        assert time_metrics[0]['opens'] == 1
        assert time_metrics[0]['clicks'] == 1
        assert time_metrics[1]['time'] == "2025-10-07 11:00"
        assert time_metrics[1]['opens'] == 1

    def test_get_time_based_metrics_invalid_interval(self, analytics, sample_campaign_id):
        """Test time-based metrics with invalid interval returns empty"""
        time_metrics = analytics.get_time_based_metrics(sample_campaign_id, "invalid")
        assert time_metrics == []


# ============================================================================
# EmailAnalyticsService - Export Tests
# ============================================================================

class TestEmailAnalyticsServiceExport:
    """Test metrics export functionality"""

    def test_export_metrics_specific_campaign(self, analytics, sample_campaign_id):
        """Test exporting metrics for specific campaign"""
        analytics.track_send(sample_campaign_id, ["test@example.com"])
        analytics.track_delivery(sample_campaign_id, "test@example.com")
        analytics.track_open(sample_campaign_id, "test@example.com")

        export_json = analytics.export_metrics(sample_campaign_id)

        import json
        data = json.loads(export_json)

        assert 'campaign' in data
        assert 'time_series' in data
        assert data['campaign']['campaign_id'] == sample_campaign_id

    def test_export_metrics_all_campaigns(self, analytics):
        """Test exporting all campaigns"""
        analytics.track_send("campaign_1", ["user1@example.com"])
        analytics.track_send("campaign_2", ["user2@example.com"])

        export_json = analytics.export_metrics()

        import json
        data = json.loads(export_json)

        assert 'aggregate' in data
        assert 'campaigns' in data
        assert len(data['campaigns']) == 2

    def test_export_metrics_empty(self, analytics):
        """Test exporting when no data exists"""
        export_json = analytics.export_metrics()

        import json
        data = json.loads(export_json)

        assert data['aggregate']['total_campaigns'] == 0
        assert data['campaigns'] == []


# ============================================================================
# Global Instance Test
# ============================================================================

def test_global_analytics_instance():
    """Test that global analytics_service instance exists"""
    assert analytics_service is not None
    assert isinstance(analytics_service, EmailAnalyticsService)


# ============================================================================
# Integration Tests
# ============================================================================

class TestEmailAnalyticsIntegration:
    """Integration tests for complete workflows"""

    def test_complete_campaign_workflow(self, analytics):
        """Test complete email campaign tracking workflow"""
        campaign_id = "newsletter_001"
        recipients = [
            "engaged@example.com",
            "clicker@example.com",
            "bounced@example.com",
            "unsubscriber@example.com"
        ]

        # Send campaign
        analytics.track_send(campaign_id, recipients)

        # Track deliveries
        analytics.track_delivery(campaign_id, "engaged@example.com")
        analytics.track_delivery(campaign_id, "clicker@example.com")
        analytics.track_delivery(campaign_id, "unsubscriber@example.com")

        # Track bounce
        analytics.track_bounce(campaign_id, "bounced@example.com", "hard")

        # Track opens
        analytics.track_open(campaign_id, "engaged@example.com")
        analytics.track_open(campaign_id, "clicker@example.com")

        # Track clicks
        analytics.track_click(campaign_id, "clicker@example.com", "https://example.com/article")

        # Track unsubscribe
        analytics.track_unsubscribe(campaign_id, "unsubscriber@example.com")

        # Verify metrics
        metrics = analytics.get_campaign_metrics(campaign_id)
        assert metrics['total_sent'] == 4
        assert metrics['total_delivered'] == 3
        assert metrics['total_bounced'] == 1
        assert metrics['unique_opens'] == 2
        assert metrics['unique_clicks'] == 1
        assert metrics['total_unsubscribed'] == 1

        # Verify recipient statuses
        assert analytics.recipients["bounced@example.com"].status == "bounced"
        assert analytics.recipients["unsubscriber@example.com"].status == "unsubscribed"
        assert analytics.recipients["engaged@example.com"].status == "active"

    def test_multi_campaign_recipient_tracking(self, analytics):
        """Test tracking recipient across multiple campaigns"""
        recipient = "loyal@example.com"

        # Campaign 1
        analytics.track_send("campaign_1", [recipient])
        analytics.track_delivery("campaign_1", recipient)
        analytics.track_open("campaign_1", recipient)

        # Campaign 2
        analytics.track_send("campaign_2", [recipient])
        analytics.track_delivery("campaign_2", recipient)
        analytics.track_open("campaign_2", recipient)
        analytics.track_click("campaign_2", recipient, "https://example.com")

        # Campaign 3
        analytics.track_send("campaign_3", [recipient])
        analytics.track_delivery("campaign_3", recipient)
        analytics.track_open("campaign_3", recipient)
        analytics.track_click("campaign_3", recipient, "https://example.com")

        engagement = analytics.get_recipient_engagement(recipient)
        assert engagement['campaigns_received'] == 3
        assert engagement['campaigns_opened'] == 3
        assert engagement['campaigns_clicked'] == 2
        assert engagement['engagement_score'] > 70  # Should be highly engaged
