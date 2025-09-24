# Example Session Templates
**Sprint 3: Halcytone Live Support**

Practical examples and templates for creating engaging breathing session content.

## Table of Contents

1. [Session Types](#session-types)
2. [Content Examples](#content-examples)
3. [Integration Examples](#integration-examples)
4. [Testing Examples](#testing-examples)

## Session Types

### 1. Morning Energizer Session

```python
# Morning energizer session example
morning_session = {
    "title": "Morning Energy Boost",
    "content": "Start your day with invigorating breathing techniques for mental clarity",
    "session_id": "morning-energizer-001",
    "session_duration": 900,  # 15 minutes
    "participant_count": 15,
    "breathing_techniques": [
        "Bellows Breathing",
        "Energizing Breath",
        "Sun Salutation Breathing"
    ],
    "average_hrv_improvement": 8.5,
    "key_achievements": [
        "Everyone completed the full session",
        "Group energy level increased by 40%"
    ],
    "session_type": "guided",
    "session_date": "2024-03-21T06:30:00Z",
    "metrics_summary": {
        "energy_level_before": 3.2,
        "energy_level_after": 7.8,
        "focus_improvement": 65
    },
    "published": True
}
```

### 2. Lunch Break Relaxation

```python
# Quick lunch break session
lunch_session = {
    "title": "Midday Reset",
    "content": "Quick stress relief session for busy professionals",
    "session_id": "lunch-break-002",
    "session_duration": 600,  # 10 minutes
    "participant_count": 30,
    "breathing_techniques": [
        "Box Breathing",
        "4-7-8 Breathing"
    ],
    "average_hrv_improvement": 6.2,
    "key_achievements": [
        "Reduced stress levels by 30%",
        "Perfect for busy schedules"
    ],
    "session_type": "practice",
    "session_date": "2024-03-21T12:15:00Z",
    "published": True
}
```

### 3. Evening Wind-Down Workshop

```python
# Evening workshop session
evening_workshop = {
    "title": "Sleep Preparation Workshop",
    "content": "Learn breathing techniques for better sleep quality",
    "session_id": "evening-workshop-003",
    "session_duration": 3600,  # 60 minutes
    "participant_count": 45,
    "breathing_techniques": [
        "Progressive Muscle Relaxation Breathing",
        "Alternate Nostril Breathing",
        "Moon Breathing",
        "Body Scan Breathing"
    ],
    "average_hrv_improvement": 15.5,
    "key_achievements": [
        "Learned 4 new techniques",
        "92% reported feeling more relaxed",
        "Created personalized sleep routines"
    ],
    "session_type": "workshop",
    "instructor_name": "Dr. Emily Watson",
    "session_date": "2024-03-21T19:00:00Z",
    "participant_feedback": {
        "average_rating": 4.8,
        "items": [
            {"participant_name": "Alex M.", "comment": "Best sleep I've had in months!"},
            {"participant_name": "Jordan K.", "comment": "The techniques really work"}
        ]
    },
    "published": True
}
```

### 4. Corporate Team Building

```python
# Corporate team session
corporate_session = {
    "title": "Team Synchronization Session",
    "content": "Build team cohesion through synchronized breathing exercises",
    "session_id": "corporate-team-004",
    "session_duration": 2400,  # 40 minutes
    "participant_count": 25,
    "breathing_techniques": [
        "Coherent Breathing",
        "Group Box Breathing",
        "Partner Breathing"
    ],
    "average_hrv_improvement": 11.0,
    "key_achievements": [
        "Achieved 95% group synchronization",
        "Improved team communication scores",
        "Created shared mindfulness experience"
    ],
    "session_type": "live",
    "instructor_name": "Michael Chen",
    "session_date": "2024-03-21T14:00:00Z",
    "metrics_summary": {
        "team_cohesion_score": 8.5,
        "synchronization_rate": 0.95,
        "participant_satisfaction": 4.7
    },
    "published": True
}
```

## Content Examples

### Email Template Output

```python
# Example generated email content
email_output = {
    "subject": "🌟 Your Morning Energy Boost Session Summary",
    "html": """
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2c3e50;">Morning Energy Boost</h1>

        <div style="background: #ecf0f1; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h2>Session Highlights</h2>
            <ul>
                <li>Duration: 15 minutes</li>
                <li>Participants: 15</li>
                <li>HRV Improvement: +8.5%</li>
                <li>Energy Level: 3.2 → 7.8</li>
            </ul>
        </div>

        <div style="margin: 20px 0;">
            <h3>Techniques Practiced</h3>
            <ol>
                <li><strong>Bellows Breathing</strong> - Rapid energizing breaths</li>
                <li><strong>Energizing Breath</strong> - Stimulating morning routine</li>
                <li><strong>Sun Salutation Breathing</strong> - Flowing energy activation</li>
            </ol>
        </div>

        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>🏆 Achievements Unlocked</h3>
            <p>✓ Everyone completed the full session</p>
            <p>✓ Group energy level increased by 40%</p>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <a href="https://app.halcytone.com/sessions/morning-energizer-001"
               style="background: #3498db; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 5px;">
                View Full Session Details
            </a>
        </div>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <p style="color: #7f8c8d; font-size: 14px;">
                Keep up the great work! Your consistency is building lasting wellness habits.
            </p>
        </div>
    </body>
    </html>
    """,
    "text": """
Morning Energy Boost - Session Summary

Session Highlights:
- Duration: 15 minutes
- Participants: 15
- HRV Improvement: +8.5%
- Energy Level: 3.2 → 7.8

Techniques Practiced:
1. Bellows Breathing - Rapid energizing breaths
2. Energizing Breath - Stimulating morning routine
3. Sun Salutation Breathing - Flowing energy activation

Achievements Unlocked:
✓ Everyone completed the full session
✓ Group energy level increased by 40%

View full details: https://app.halcytone.com/sessions/morning-energizer-001

Keep up the great work! Your consistency is building lasting wellness habits.
"""
}
```

### Social Media Posts

```python
# Twitter/X post example
twitter_post = {
    "content": "Just wrapped up an amazing Morning Energy Boost session! 🌅 15 participants achieved an 8.5% HRV improvement in just 15 minutes. Energy levels soared from 3.2 to 7.8! 💪 #Breathwork #MorningRoutine #Wellness #HRV",
    "media": ["session_photo.jpg"],
    "thread": [
        "The techniques we practiced: Bellows Breathing for quick energy, Energizing Breath for mental clarity, and Sun Salutation Breathing for full-body activation. 🧘‍♀️",
        "Big achievement: 100% completion rate! When the whole group stays engaged, the energy is contagious. This is the power of community wellness. 🤝"
    ]
}

# LinkedIn post example
linkedin_post = {
    "content": """
Exciting session results from this morning's Energy Boost breathing workshop!

Key Metrics:
• 15 participants
• 15-minute focused session
• 8.5% average HRV improvement
• Energy levels increased from 3.2 to 7.8 (140% improvement)

What made this session special was the 100% completion rate - a testament to the power of guided group breathing exercises in the workplace.

Corporate wellness isn't just a buzzword; it's measurable improvement in employee vitality and focus.

Interested in bringing breathing workshops to your team? Let's connect!

#CorporateWellness #EmployeeWellbeing #Breathwork #HRV #WorkplaceHealth
""",
    "media": ["session_metrics_graph.png"]
}

# Facebook post example
facebook_post = {
    "content": """
🌟 Morning Energy Boost Session Complete! 🌟

What an incredible start to the day! Our community came together for 15 minutes of energizing breathing exercises, and the results speak for themselves:

✨ 15 wonderful participants
✨ 8.5% HRV improvement
✨ Energy levels jumped from 3.2 to 7.8
✨ 100% of participants completed the full session

We practiced three powerful techniques:
1️⃣ Bellows Breathing - for instant energy
2️⃣ Energizing Breath - for mental clarity
3️⃣ Sun Salutation Breathing - for full-body activation

The best part? Everyone stayed until the end! When we breathe together, we thrive together. 💙

Join us for tomorrow's session at 6:30 AM. Your morning routine will never be the same!

👉 Sign up: [Link to registration]

#BreathingCommunity #MorningMotivation #HealthyHabits #Mindfulness
""",
    "media": ["group_photo.jpg", "energy_chart.png"],
    "call_to_action": {
        "text": "Join Next Session",
        "url": "https://app.halcytone.com/sessions/register"
    }
}
```

### Web Content Format

```html
<!-- Example web article format -->
<article class="session-summary">
    <header>
        <h1>Morning Energy Boost: Session Recap</h1>
        <div class="session-meta">
            <span class="date">March 21, 2024</span>
            <span class="duration">15 minutes</span>
            <span class="participants">15 participants</span>
        </div>
    </header>

    <section class="key-metrics">
        <h2>Session Impact</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <span class="metric-value">8.5%</span>
                <span class="metric-label">HRV Improvement</span>
            </div>
            <div class="metric-card">
                <span class="metric-value">140%</span>
                <span class="metric-label">Energy Increase</span>
            </div>
            <div class="metric-card">
                <span class="metric-value">100%</span>
                <span class="metric-label">Completion Rate</span>
            </div>
        </div>
    </section>

    <section class="techniques">
        <h2>Breathing Techniques Practiced</h2>
        <div class="technique-list">
            <div class="technique">
                <h3>Bellows Breathing</h3>
                <p>Rapid diaphragmatic breathing for instant energy boost</p>
            </div>
            <div class="technique">
                <h3>Energizing Breath</h3>
                <p>Structured breathing pattern for mental clarity</p>
            </div>
            <div class="technique">
                <h3>Sun Salutation Breathing</h3>
                <p>Flowing breath work synchronized with gentle movement</p>
            </div>
        </div>
    </section>

    <section class="achievements">
        <h2>Session Achievements</h2>
        <ul class="achievement-list">
            <li class="achievement achieved">
                <span class="icon">✓</span>
                Everyone completed the full session
            </li>
            <li class="achievement achieved">
                <span class="icon">✓</span>
                Group energy level increased by 40%
            </li>
        </ul>
    </section>

    <section class="next-steps">
        <h2>Continue Your Journey</h2>
        <div class="cta-buttons">
            <a href="/sessions/schedule" class="btn-primary">Join Next Session</a>
            <a href="/techniques/morning" class="btn-secondary">Learn These Techniques</a>
        </div>
    </section>
</article>
```

## Integration Examples

### Python Integration Script

```python
#!/usr/bin/env python3
"""
Example script for generating session summaries
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, List

class SessionContentGenerator:
    """Generate and distribute session content"""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    async def create_session_summary(self, session_data: Dict) -> Dict:
        """Generate session summary content"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v2/session-summary",
                headers=self.headers,
                json=session_data
            )
            response.raise_for_status()
            return response.json()

    async def broadcast_announcement(
        self,
        session_id: str,
        announcement_type: str,
        message: str
    ) -> Dict:
        """Send live announcement to session"""

        announcement = {
            "announcement": {
                "type": announcement_type,
                "title": f"Session Update: {session_id}",
                "message": message,
                "action_url": f"/sessions/join/{session_id}"
            },
            "session_id": session_id
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v2/live-announce",
                headers=self.headers,
                json=announcement
            )
            response.raise_for_status()
            return response.json()

    async def get_session_metrics(
        self,
        session_id: str,
        include_replay: bool = False
    ) -> Dict:
        """Fetch session metrics and content"""

        params = {
            "include_metrics": "true",
            "include_replay": str(include_replay).lower()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v2/session/{session_id}/content",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()


# Example usage
async def main():
    # Initialize generator
    generator = SessionContentGenerator("your-api-key")

    # Create morning session data
    morning_session = {
        "title": "Morning Energy Boost",
        "content": "Energizing breathing session to start your day",
        "session_id": f"morning-{datetime.now().strftime('%Y%m%d')}",
        "session_duration": 900,
        "participant_count": 20,
        "breathing_techniques": ["Bellows Breathing", "Energizing Breath"],
        "average_hrv_improvement": 9.2,
        "key_achievements": [
            "Perfect attendance",
            "45% energy increase"
        ],
        "session_type": "guided",
        "session_date": datetime.now(timezone.utc).isoformat(),
        "published": True,
        "channels": ["email", "web", "social"]
    }

    # Generate summary
    print("Generating session summary...")
    summary = await generator.create_session_summary(morning_session)
    print(f"Summary created: {summary['content_id']}")

    # Send announcement
    print("Broadcasting session starting announcement...")
    announcement = await generator.broadcast_announcement(
        morning_session["session_id"],
        "session_starting",
        "Morning Energy Boost starts in 5 minutes!"
    )
    print(f"Announced to {announcement['participant_count']} participants")

    # Get metrics
    print("Fetching session metrics...")
    metrics = await generator.get_session_metrics(morning_session["session_id"])
    print(f"Average HRV improvement: {metrics['metrics']['average_hrv']}%")


if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/React Component

```jsx
// SessionSummaryComponent.jsx
import React, { useState, useEffect } from 'react';
import { useSessionWebSocket } from './hooks/useSessionWebSocket';

const SessionSummaryCard = ({ session }) => {
    const [metrics, setMetrics] = useState(null);
    const [isLive, setIsLive] = useState(false);

    // Connect to WebSocket for live updates
    const { lastMessage, isConnected } = useSessionWebSocket({
        sessionId: session.session_id,
        clientId: `viewer-${Date.now()}`,
        role: 'observer',
        onMessage: (msg) => {
            if (msg.type === 'metrics_update') {
                setMetrics(msg.content);
            }
        }
    });

    useEffect(() => {
        // Fetch initial session data
        fetchSessionContent();
    }, [session.session_id]);

    const fetchSessionContent = async () => {
        try {
            const response = await fetch(
                `/api/v2/session/${session.session_id}/content?include_metrics=true`
            );
            const data = await response.json();
            setMetrics(data.metrics);
            setIsLive(data.active);
        } catch (error) {
            console.error('Failed to fetch session content:', error);
        }
    };

    return (
        <div className="session-card">
            <div className="session-header">
                <h2>{session.title}</h2>
                {isLive && <span className="live-badge">LIVE</span>}
                {isConnected && <span className="connected-badge">Connected</span>}
            </div>

            <div className="session-info">
                <p>{session.content}</p>
                <div className="meta-info">
                    <span>Duration: {session.session_duration / 60} minutes</span>
                    <span>Participants: {session.participant_count}</span>
                    <span>Type: {session.session_type}</span>
                </div>
            </div>

            {metrics && (
                <div className="metrics-display">
                    <h3>Session Metrics</h3>
                    <div className="metrics-grid">
                        <div className="metric">
                            <span className="value">
                                {metrics.average_hrv || session.average_hrv_improvement}%
                            </span>
                            <span className="label">HRV Improvement</span>
                        </div>
                        <div className="metric">
                            <span className="value">
                                {metrics.completion_rate ?
                                    `${(metrics.completion_rate * 100).toFixed(0)}%` :
                                    'N/A'}
                            </span>
                            <span className="label">Completion Rate</span>
                        </div>
                        <div className="metric">
                            <span className="value">
                                {metrics.quality_score || 'N/A'}
                            </span>
                            <span className="label">Quality Score</span>
                        </div>
                    </div>
                </div>
            )}

            <div className="techniques-list">
                <h3>Breathing Techniques</h3>
                <ul>
                    {session.breathing_techniques.map((technique, idx) => (
                        <li key={idx}>{technique}</li>
                    ))}
                </ul>
            </div>

            {session.key_achievements && session.key_achievements.length > 0 && (
                <div className="achievements">
                    <h3>Achievements</h3>
                    <ul>
                        {session.key_achievements.map((achievement, idx) => (
                            <li key={idx} className="achievement">
                                ✓ {achievement}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="actions">
                <button
                    className="btn-primary"
                    onClick={() => window.location.href = `/sessions/${session.session_id}`}
                >
                    View Full Details
                </button>
                {isLive && (
                    <button
                        className="btn-secondary"
                        onClick={() => window.location.href = `/sessions/join/${session.session_id}`}
                    >
                        Join Session
                    </button>
                )}
            </div>
        </div>
    );
};

// Usage in parent component
const SessionDashboard = () => {
    const [sessions, setSessions] = useState([]);

    useEffect(() => {
        // Fetch recent sessions
        fetchRecentSessions();
    }, []);

    const fetchRecentSessions = async () => {
        const response = await fetch('/api/v2/sessions/recent');
        const data = await response.json();
        setSessions(data.sessions);
    };

    return (
        <div className="session-dashboard">
            <h1>Recent Breathing Sessions</h1>
            <div className="sessions-grid">
                {sessions.map(session => (
                    <SessionSummaryCard
                        key={session.session_id}
                        session={session}
                    />
                ))}
            </div>
        </div>
    );
};

export default SessionDashboard;
```

## Testing Examples

### Unit Test for Session Validation

```python
# test_session_examples.py
import pytest
from datetime import datetime, timezone, timedelta
from src.halcytone_content_generator.schemas.content_types import SessionContentStrict

class TestSessionExamples:
    """Test session content examples"""

    def test_morning_energizer_session(self):
        """Test morning energizer session creation"""
        session = SessionContentStrict(
            title="Morning Energy Boost",
            content="Start your day with invigorating breathing",
            session_id="morning-test-001",
            session_duration=900,
            participant_count=15,
            breathing_techniques=["Bellows Breathing", "Energizing Breath"],
            average_hrv_improvement=8.5,
            key_achievements=["Full participation", "40% energy increase"],
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert session.session_duration == 900
        assert session.participant_count == 15
        assert len(session.breathing_techniques) == 2
        assert session.average_hrv_improvement == 8.5

    def test_workshop_session_validation(self):
        """Test workshop session with instructor requirement"""
        session = SessionContentStrict(
            title="Evening Workshop",
            content="Comprehensive breathing technique workshop",
            session_id="workshop-test-001",
            session_duration=3600,
            participant_count=45,  # Workshops need min 5 participants
            breathing_techniques=[
                "Progressive Relaxation",
                "Alternate Nostril",
                "Moon Breathing"
            ],
            session_type="workshop",
            instructor_name="Dr. Smith",  # Required for workshops
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert session.session_type == "workshop"
        assert session.participant_count >= 5
        assert session.instructor_name is not None

    def test_corporate_session_metrics(self):
        """Test corporate session with custom metrics"""
        session = SessionContentStrict(
            title="Team Building Session",
            content="Corporate breathing and mindfulness session",
            session_id="corporate-test-001",
            session_duration=2400,
            participant_count=25,
            breathing_techniques=["Coherent Breathing", "Group Box Breathing"],
            average_hrv_improvement=11.0,
            session_type="live",
            instructor_name="Michael Chen",
            session_date=datetime.now(timezone.utc),
            metrics_summary={
                "team_cohesion_score": 8.5,
                "synchronization_rate": 0.95,
                "participant_satisfaction": 4.7
            },
            published=True
        )

        assert session.metrics_summary["team_cohesion_score"] == 8.5
        assert session.metrics_summary["synchronization_rate"] == 0.95
        assert "participant_satisfaction" in session.metrics_summary
```

### Integration Test

```python
# test_session_integration.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_full_session_workflow(test_client: TestClient):
    """Test complete session content workflow"""

    # 1. Create session data
    session_data = {
        "title": "Integration Test Session",
        "content": "Testing full session workflow integration",
        "session_id": "test-integration-001",
        "session_duration": 1200,
        "participant_count": 10,
        "breathing_techniques": ["Test Breathing"],
        "average_hrv_improvement": 7.5,
        "session_type": "guided",
        "session_date": datetime.now(timezone.utc).isoformat(),
        "published": True,
        "channels": ["email", "web"]
    }

    # 2. Generate session summary
    response = test_client.post(
        "/api/v2/session-summary",
        json=session_data
    )
    assert response.status_code == 200
    summary = response.json()
    assert "content_id" in summary
    assert "newsletter" in summary
    assert "web_update" in summary

    # 3. Send live announcement
    announcement_response = test_client.post(
        "/api/v2/live-announce",
        json={
            "announcement": {
                "type": "session_starting",
                "title": "Test Session Starting",
                "message": "Join our test session"
            },
            "session_id": "test-integration-001"
        }
    )
    assert announcement_response.status_code == 200

    # 4. Get session content
    content_response = test_client.get(
        f"/api/v2/session/{session_data['session_id']}/content",
        params={"include_metrics": "true"}
    )
    assert content_response.status_code == 200
    content = content_response.json()
    assert content["session_id"] == session_data["session_id"]
```

---

These examples provide practical templates and code snippets for implementing breathing session content in the Halcytone platform. Use them as starting points and customize based on your specific needs.