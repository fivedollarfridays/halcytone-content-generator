"""
Email analytics and tracking service
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailMetrics:
    """Email campaign metrics"""
    campaign_id: str
    total_sent: int = 0
    total_delivered: int = 0
    total_bounced: int = 0
    total_opened: int = 0
    unique_opens: int = 0
    total_clicked: int = 0
    unique_clicks: int = 0
    total_unsubscribed: int = 0
    total_complaints: int = 0

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate"""
        if self.total_sent == 0:
            return 0
        return (self.total_delivered / self.total_sent) * 100

    @property
    def open_rate(self) -> float:
        """Calculate open rate"""
        if self.total_delivered == 0:
            return 0
        return (self.unique_opens / self.total_delivered) * 100

    @property
    def click_rate(self) -> float:
        """Calculate click-through rate"""
        if self.unique_opens == 0:
            return 0
        return (self.unique_clicks / self.unique_opens) * 100

    @property
    def click_to_open_rate(self) -> float:
        """Calculate click-to-open rate (CTOR)"""
        if self.unique_opens == 0:
            return 0
        return (self.unique_clicks / self.unique_opens) * 100

    @property
    def unsubscribe_rate(self) -> float:
        """Calculate unsubscribe rate"""
        if self.total_delivered == 0:
            return 0
        return (self.total_unsubscribed / self.total_delivered) * 100

    @property
    def complaint_rate(self) -> float:
        """Calculate complaint rate"""
        if self.total_delivered == 0:
            return 0
        return (self.total_complaints / self.total_delivered) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary with calculated metrics"""
        return {
            'campaign_id': self.campaign_id,
            'total_sent': self.total_sent,
            'total_delivered': self.total_delivered,
            'total_bounced': self.total_bounced,
            'total_opened': self.total_opened,
            'unique_opens': self.unique_opens,
            'total_clicked': self.total_clicked,
            'unique_clicks': self.unique_clicks,
            'total_unsubscribed': self.total_unsubscribed,
            'total_complaints': self.total_complaints,
            'delivery_rate': round(self.delivery_rate, 2),
            'open_rate': round(self.open_rate, 2),
            'click_rate': round(self.click_rate, 2),
            'click_to_open_rate': round(self.click_to_open_rate, 2),
            'unsubscribe_rate': round(self.unsubscribe_rate, 2),
            'complaint_rate': round(self.complaint_rate, 2)
        }


@dataclass
class EmailEvent:
    """Individual email event"""
    event_type: str
    email: str
    campaign_id: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class RecipientEngagement:
    """Track individual recipient engagement"""
    email: str
    campaigns_received: int = 0
    campaigns_opened: int = 0
    campaigns_clicked: int = 0
    last_open: Optional[datetime] = None
    last_click: Optional[datetime] = None
    engagement_score: float = 0.0
    status: str = "active"  # active, inactive, unsubscribed

    def calculate_engagement_score(self) -> float:
        """Calculate engagement score (0-100)"""
        if self.campaigns_received == 0:
            return 0

        # Base score from open rate (40% weight)
        open_score = (self.campaigns_opened / self.campaigns_received) * 40

        # Click score (40% weight)
        click_score = (self.campaigns_clicked / self.campaigns_received) * 40

        # Recency score (20% weight)
        recency_score = 0
        if self.last_open:
            days_since_open = (datetime.now() - self.last_open).days
            if days_since_open < 7:
                recency_score = 20
            elif days_since_open < 30:
                recency_score = 15
            elif days_since_open < 90:
                recency_score = 10
            else:
                recency_score = 5

        self.engagement_score = round(open_score + click_score + recency_score, 2)
        return self.engagement_score


class EmailAnalyticsService:
    """
    Service for tracking and analyzing email metrics
    """

    def __init__(self):
        """Initialize analytics service"""
        # In production, this would use a database
        self.metrics: Dict[str, EmailMetrics] = {}
        self.events: List[EmailEvent] = []
        self.recipients: Dict[str, RecipientEngagement] = {}
        self.link_clicks: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def track_send(self, campaign_id: str, recipients: List[str]):
        """
        Track email send event

        Args:
            campaign_id: Campaign identifier
            recipients: List of recipient emails
        """
        if campaign_id not in self.metrics:
            self.metrics[campaign_id] = EmailMetrics(campaign_id)

        self.metrics[campaign_id].total_sent += len(recipients)

        for email in recipients:
            self.events.append(EmailEvent(
                event_type="sent",
                email=email,
                campaign_id=campaign_id,
                timestamp=datetime.now()
            ))

            if email not in self.recipients:
                self.recipients[email] = RecipientEngagement(email=email)
            self.recipients[email].campaigns_received += 1

    def track_delivery(self, campaign_id: str, email: str):
        """Track successful delivery"""
        if campaign_id in self.metrics:
            self.metrics[campaign_id].total_delivered += 1

        self.events.append(EmailEvent(
            event_type="delivered",
            email=email,
            campaign_id=campaign_id,
            timestamp=datetime.now()
        ))

    def track_bounce(self, campaign_id: str, email: str, bounce_type: str = "hard"):
        """Track email bounce"""
        if campaign_id in self.metrics:
            self.metrics[campaign_id].total_bounced += 1

        self.events.append(EmailEvent(
            event_type="bounced",
            email=email,
            campaign_id=campaign_id,
            timestamp=datetime.now(),
            metadata={"bounce_type": bounce_type}
        ))

        # Mark recipient as inactive for hard bounces
        if bounce_type == "hard" and email in self.recipients:
            self.recipients[email].status = "bounced"

    def track_open(
        self,
        campaign_id: str,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Track email open"""
        if campaign_id in self.metrics:
            self.metrics[campaign_id].total_opened += 1

            # Check if unique open
            unique_opens = set()
            for event in self.events:
                if (event.campaign_id == campaign_id and
                    event.event_type == "opened" and
                    event.email == email):
                    unique_opens.add(event.email)

            if email not in unique_opens:
                self.metrics[campaign_id].unique_opens += 1

        self.events.append(EmailEvent(
            event_type="opened",
            email=email,
            campaign_id=campaign_id,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        ))

        # Update recipient engagement
        if email in self.recipients:
            self.recipients[email].campaigns_opened += 1
            self.recipients[email].last_open = datetime.now()

    def track_click(
        self,
        campaign_id: str,
        email: str,
        url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Track link click"""
        if campaign_id in self.metrics:
            self.metrics[campaign_id].total_clicked += 1

            # Check if unique click
            unique_clicks = set()
            for event in self.events:
                if (event.campaign_id == campaign_id and
                    event.event_type == "clicked" and
                    event.email == email):
                    unique_clicks.add(event.email)

            if email not in unique_clicks:
                self.metrics[campaign_id].unique_clicks += 1

        self.events.append(EmailEvent(
            event_type="clicked",
            email=email,
            campaign_id=campaign_id,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            url=url
        ))

        # Track link popularity
        self.link_clicks[campaign_id][url] += 1

        # Update recipient engagement
        if email in self.recipients:
            self.recipients[email].campaigns_clicked += 1
            self.recipients[email].last_click = datetime.now()

    def track_unsubscribe(self, campaign_id: str, email: str):
        """Track unsubscribe"""
        if campaign_id in self.metrics:
            self.metrics[campaign_id].total_unsubscribed += 1

        self.events.append(EmailEvent(
            event_type="unsubscribed",
            email=email,
            campaign_id=campaign_id,
            timestamp=datetime.now()
        ))

        # Update recipient status
        if email in self.recipients:
            self.recipients[email].status = "unsubscribed"

    def track_complaint(self, campaign_id: str, email: str):
        """Track spam complaint"""
        if campaign_id in self.metrics:
            self.metrics[campaign_id].total_complaints += 1

        self.events.append(EmailEvent(
            event_type="complaint",
            email=email,
            campaign_id=campaign_id,
            timestamp=datetime.now()
        ))

        # Update recipient status
        if email in self.recipients:
            self.recipients[email].status = "complained"

    def get_campaign_metrics(self, campaign_id: str) -> Optional[Dict]:
        """
        Get metrics for a specific campaign

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign metrics or None
        """
        if campaign_id in self.metrics:
            metrics = self.metrics[campaign_id].to_dict()

            # Add link click data
            if campaign_id in self.link_clicks:
                metrics['popular_links'] = sorted(
                    self.link_clicks[campaign_id].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5 links

            return metrics
        return None

    def get_recipient_engagement(self, email: str) -> Optional[Dict]:
        """
        Get engagement data for a recipient

        Args:
            email: Recipient email

        Returns:
            Engagement data or None
        """
        if email in self.recipients:
            recipient = self.recipients[email]
            recipient.calculate_engagement_score()

            return {
                'email': recipient.email,
                'campaigns_received': recipient.campaigns_received,
                'campaigns_opened': recipient.campaigns_opened,
                'campaigns_clicked': recipient.campaigns_clicked,
                'last_open': recipient.last_open.isoformat() if recipient.last_open else None,
                'last_click': recipient.last_click.isoformat() if recipient.last_click else None,
                'engagement_score': recipient.engagement_score,
                'status': recipient.status
            }
        return None

    def get_aggregate_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get aggregate metrics across all campaigns

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Aggregate metrics
        """
        # Filter campaigns by date if provided
        campaigns = self.metrics.values()

        total_metrics = {
            'total_campaigns': len(campaigns),
            'total_sent': sum(c.total_sent for c in campaigns),
            'total_delivered': sum(c.total_delivered for c in campaigns),
            'total_opened': sum(c.total_opened for c in campaigns),
            'total_clicked': sum(c.total_clicked for c in campaigns),
            'total_unsubscribed': sum(c.total_unsubscribed for c in campaigns),
            'avg_delivery_rate': 0,
            'avg_open_rate': 0,
            'avg_click_rate': 0
        }

        if campaigns:
            total_metrics['avg_delivery_rate'] = round(
                sum(c.delivery_rate for c in campaigns) / len(campaigns), 2
            )
            total_metrics['avg_open_rate'] = round(
                sum(c.open_rate for c in campaigns) / len(campaigns), 2
            )
            total_metrics['avg_click_rate'] = round(
                sum(c.click_rate for c in campaigns) / len(campaigns), 2
            )

        # Engagement segments
        segments = {
            'highly_engaged': 0,  # score > 70
            'engaged': 0,  # score 40-70
            'at_risk': 0,  # score 20-40
            'inactive': 0  # score < 20
        }

        for recipient in self.recipients.values():
            recipient.calculate_engagement_score()
            if recipient.engagement_score > 70:
                segments['highly_engaged'] += 1
            elif recipient.engagement_score > 40:
                segments['engaged'] += 1
            elif recipient.engagement_score > 20:
                segments['at_risk'] += 1
            else:
                segments['inactive'] += 1

        total_metrics['engagement_segments'] = segments

        return total_metrics

    def get_time_based_metrics(
        self,
        campaign_id: str,
        interval: str = "hourly"
    ) -> List[Dict]:
        """
        Get time-based metrics for a campaign

        Args:
            campaign_id: Campaign identifier
            interval: Time interval (hourly, daily)

        Returns:
            Time-based metrics
        """
        campaign_events = [
            e for e in self.events
            if e.campaign_id == campaign_id
        ]

        if interval == "hourly":
            buckets = defaultdict(lambda: {
                'opens': 0,
                'clicks': 0,
                'unsubscribes': 0
            })

            for event in campaign_events:
                hour = event.timestamp.strftime("%Y-%m-%d %H:00")
                if event.event_type == "opened":
                    buckets[hour]['opens'] += 1
                elif event.event_type == "clicked":
                    buckets[hour]['clicks'] += 1
                elif event.event_type == "unsubscribed":
                    buckets[hour]['unsubscribes'] += 1

            return [
                {'time': k, **v}
                for k, v in sorted(buckets.items())
            ]

        return []

    def export_metrics(self, campaign_id: Optional[str] = None) -> str:
        """
        Export metrics as JSON

        Args:
            campaign_id: Optional specific campaign

        Returns:
            JSON string of metrics
        """
        if campaign_id:
            data = {
                'campaign': self.get_campaign_metrics(campaign_id),
                'time_series': self.get_time_based_metrics(campaign_id)
            }
        else:
            data = {
                'aggregate': self.get_aggregate_metrics(),
                'campaigns': [
                    m.to_dict() for m in self.metrics.values()
                ]
            }

        return json.dumps(data, indent=2, default=str)


# Global analytics instance for demo
analytics_service = EmailAnalyticsService()