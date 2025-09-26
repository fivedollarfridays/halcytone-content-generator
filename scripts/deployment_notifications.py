#!/usr/bin/env python
"""
Deployment notification and monitoring script
Sends notifications to various channels about deployment status
"""
import argparse
import json
import os
import sys
from typing import Dict, List, Optional
import asyncio
import aiohttp
from datetime import datetime
from enum import Enum


class NotificationChannel(Enum):
    """Supported notification channels"""
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"
    DATADOG = "datadog"
    PAGERDUTY = "pagerduty"


class DeploymentStatus(Enum):
    """Deployment status types"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    WARNING = "warning"


class DeploymentNotifier:
    """Handle deployment notifications across multiple channels"""

    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.datadog_api_key = os.getenv("DATADOG_API_KEY")
        self.pagerduty_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
        self.email_webhook = os.getenv("EMAIL_NOTIFICATION_WEBHOOK")
        self.custom_webhook = os.getenv("CUSTOM_NOTIFICATION_WEBHOOK")

    async def notify(
        self,
        status: DeploymentStatus,
        environment: str,
        version: str,
        message: str,
        details: Optional[Dict] = None,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """Send notifications to specified channels"""
        if channels is None:
            channels = self._get_default_channels(status)

        tasks = []
        for channel in channels:
            if channel == NotificationChannel.SLACK and self.slack_webhook:
                tasks.append(self.notify_slack(status, environment, version, message, details))
            elif channel == NotificationChannel.DATADOG and self.datadog_api_key:
                tasks.append(self.notify_datadog(status, environment, version, message, details))
            elif channel == NotificationChannel.PAGERDUTY and self.pagerduty_key:
                tasks.append(self.notify_pagerduty(status, environment, version, message, details))
            elif channel == NotificationChannel.EMAIL and self.email_webhook:
                tasks.append(self.notify_email(status, environment, version, message, details))
            elif channel == NotificationChannel.WEBHOOK and self.custom_webhook:
                tasks.append(self.notify_webhook(status, environment, version, message, details))

        if tasks:
            async with aiohttp.ClientSession() as session:
                results = await asyncio.gather(*[task(session) for task in tasks], return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"Warning: Failed to send notification to {channels[i]}: {result}")

    def _get_default_channels(self, status: DeploymentStatus) -> List[NotificationChannel]:
        """Get default notification channels based on status"""
        if status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]:
            # Critical failures notify all channels
            return [
                NotificationChannel.SLACK,
                NotificationChannel.PAGERDUTY,
                NotificationChannel.EMAIL,
                NotificationChannel.DATADOG
            ]
        elif status == DeploymentStatus.WARNING:
            return [NotificationChannel.SLACK, NotificationChannel.DATADOG]
        else:
            return [NotificationChannel.SLACK, NotificationChannel.DATADOG]

    async def notify_slack(self, status, environment, version, message, details):
        """Send Slack notification"""
        async def _send(session):
            color = self._get_slack_color(status)
            emoji = self._get_status_emoji(status)

            fields = [
                {"title": "Environment", "value": environment, "short": True},
                {"title": "Version", "value": version, "short": True},
                {"title": "Status", "value": status.value.title(), "short": True},
                {"title": "Time", "value": datetime.utcnow().isoformat(), "short": True}
            ]

            if details:
                for key, value in details.items():
                    fields.append({"title": key, "value": str(value), "short": True})

            payload = {
                "text": f"{emoji} Deployment {status.value}: {message}",
                "attachments": [{
                    "color": color,
                    "fields": fields,
                    "footer": "Halcytone Deployment System",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
                }]
            }

            async with session.post(self.slack_webhook, json=payload) as response:
                response.raise_for_status()
                return await response.text()

        return _send

    async def notify_datadog(self, status, environment, version, message, details):
        """Send Datadog event"""
        async def _send(session):
            alert_type = self._get_datadog_alert_type(status)

            event = {
                "title": f"Deployment {status.value}: {environment}",
                "text": message,
                "alert_type": alert_type,
                "tags": [
                    f"environment:{environment}",
                    f"version:{version}",
                    f"status:{status.value}",
                    "service:halcytone-content-generator"
                ]
            }

            if details:
                event["text"] += f"\n\nDetails:\n{json.dumps(details, indent=2)}"

            headers = {
                "DD-API-KEY": self.datadog_api_key,
                "Content-Type": "application/json"
            }

            async with session.post(
                "https://api.datadoghq.com/api/v1/events",
                json=event,
                headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()

        return _send

    async def notify_pagerduty(self, status, environment, version, message, details):
        """Send PagerDuty event (for critical failures)"""
        async def _send(session):
            if status not in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]:
                return  # Only send critical alerts to PagerDuty

            event = {
                "routing_key": self.pagerduty_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"Deployment {status.value}: {environment} - {message}",
                    "severity": "error",
                    "source": f"halcytone-{environment}",
                    "custom_details": {
                        "version": version,
                        "environment": environment,
                        "status": status.value,
                        "timestamp": datetime.utcnow().isoformat(),
                        **(details or {})
                    }
                }
            }

            async with session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=event
            ) as response:
                response.raise_for_status()
                return await response.json()

        return _send

    async def notify_email(self, status, environment, version, message, details):
        """Send email notification via webhook"""
        async def _send(session):
            payload = {
                "subject": f"Deployment {status.value}: {environment} v{version}",
                "body": self._format_email_body(status, environment, version, message, details),
                "priority": "high" if status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK] else "normal",
                "recipients": os.getenv("DEPLOYMENT_EMAIL_RECIPIENTS", "").split(",")
            }

            async with session.post(self.email_webhook, json=payload) as response:
                response.raise_for_status()
                return await response.text()

        return _send

    async def notify_webhook(self, status, environment, version, message, details):
        """Send notification to custom webhook"""
        async def _send(session):
            payload = {
                "event": "deployment",
                "status": status.value,
                "environment": environment,
                "version": version,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }

            async with session.post(self.custom_webhook, json=payload) as response:
                response.raise_for_status()
                return await response.text()

        return _send

    def _get_slack_color(self, status: DeploymentStatus) -> str:
        """Get Slack attachment color based on status"""
        return {
            DeploymentStatus.SUCCESS: "good",
            DeploymentStatus.FAILED: "danger",
            DeploymentStatus.ROLLED_BACK: "danger",
            DeploymentStatus.WARNING: "warning",
            DeploymentStatus.STARTED: "#3AA3E3",
            DeploymentStatus.IN_PROGRESS: "#3AA3E3"
        }.get(status, "#808080")

    def _get_status_emoji(self, status: DeploymentStatus) -> str:
        """Get emoji for status"""
        return {
            DeploymentStatus.SUCCESS: "✅",
            DeploymentStatus.FAILED: "❌",
            DeploymentStatus.ROLLED_BACK: "↩️",
            DeploymentStatus.WARNING: "⚠️",
            DeploymentStatus.STARTED: "🚀",
            DeploymentStatus.IN_PROGRESS: "⏳"
        }.get(status, "📦")

    def _get_datadog_alert_type(self, status: DeploymentStatus) -> str:
        """Get Datadog alert type based on status"""
        return {
            DeploymentStatus.SUCCESS: "success",
            DeploymentStatus.FAILED: "error",
            DeploymentStatus.ROLLED_BACK: "error",
            DeploymentStatus.WARNING: "warning",
            DeploymentStatus.STARTED: "info",
            DeploymentStatus.IN_PROGRESS: "info"
        }.get(status, "info")

    def _format_email_body(self, status, environment, version, message, details) -> str:
        """Format email body"""
        body = f"""
Deployment Notification
======================

Status: {status.value.title()}
Environment: {environment}
Version: {version}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{message}
"""
        if details:
            body += f"\n\nDetails:\n{json.dumps(details, indent=2)}"

        return body


class MetricsCollector:
    """Collect and send deployment metrics"""

    def __init__(self):
        self.datadog_api_key = os.getenv("DATADOG_API_KEY")
        self.metrics_webhook = os.getenv("METRICS_WEBHOOK_URL")

    async def send_metrics(self, metrics: Dict):
        """Send deployment metrics"""
        tasks = []

        if self.datadog_api_key:
            tasks.append(self._send_to_datadog(metrics))

        if self.metrics_webhook:
            tasks.append(self._send_to_webhook(metrics))

        if tasks:
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_datadog(self, metrics: Dict):
        """Send metrics to Datadog"""
        async with aiohttp.ClientSession() as session:
            series = []
            timestamp = int(datetime.utcnow().timestamp())

            for metric_name, value in metrics.items():
                series.append({
                    "metric": f"deployment.{metric_name}",
                    "points": [[timestamp, value]],
                    "type": "gauge",
                    "tags": [
                        f"environment:{metrics.get('environment', 'unknown')}",
                        f"version:{metrics.get('version', 'unknown')}",
                        "service:halcytone-content-generator"
                    ]
                })

            payload = {"series": series}
            headers = {
                "DD-API-KEY": self.datadog_api_key,
                "Content-Type": "application/json"
            }

            async with session.post(
                "https://api.datadoghq.com/api/v1/series",
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()

    async def _send_to_webhook(self, metrics: Dict):
        """Send metrics to custom webhook"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "type": "deployment_metrics",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics
            }

            async with session.post(self.metrics_webhook, json=payload) as response:
                response.raise_for_status()


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Deployment notification system")
    parser.add_argument("--status", type=str, required=True,
                       choices=[s.value for s in DeploymentStatus],
                       help="Deployment status")
    parser.add_argument("--environment", type=str, required=True,
                       help="Deployment environment")
    parser.add_argument("--version", type=str, required=True,
                       help="Deployment version")
    parser.add_argument("--message", type=str, required=True,
                       help="Notification message")
    parser.add_argument("--details", type=json.loads, default={},
                       help="Additional details (JSON)")
    parser.add_argument("--channels", nargs="+",
                       choices=[c.value for c in NotificationChannel],
                       help="Notification channels")
    parser.add_argument("--metrics", type=json.loads,
                       help="Deployment metrics (JSON)")

    args = parser.parse_args()

    # Send notifications
    notifier = DeploymentNotifier()
    channels = [NotificationChannel(c) for c in args.channels] if args.channels else None

    await notifier.notify(
        DeploymentStatus(args.status),
        args.environment,
        args.version,
        args.message,
        args.details,
        channels
    )

    # Send metrics if provided
    if args.metrics:
        collector = MetricsCollector()
        await collector.send_metrics(args.metrics)

    print(f"Notifications sent for {args.status} deployment of v{args.version} to {args.environment}")


if __name__ == "__main__":
    asyncio.run(main())