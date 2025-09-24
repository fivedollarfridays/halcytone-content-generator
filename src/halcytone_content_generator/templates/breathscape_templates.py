"""
Breathscape-specific templates for breathing, wellness, and mindfulness content
"""

BREATHSCAPE_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.7;
            color: #2C3E50;
            background: linear-gradient(135deg, #E8F5E8 0%, #B8E6B8 50%, #A8D8EA 100%);
            padding: 20px 0;
        }
        .wrapper {
            max-width: 680px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 80px rgba(46, 204, 113, 0.15);
        }
        .header {
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 50%, #16A085 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            position: relative;
        }
        .header::before {
            content: '🌱';
            font-size: 48px;
            display: block;
            margin-bottom: 15px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
        }
        .logo {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        .tagline {
            font-size: 16px;
            opacity: 0.9;
            font-weight: 300;
        }
        .content {
            padding: 45px 40px;
        }
        .greeting {
            font-size: 18px;
            color: #2ECC71;
            margin-bottom: 25px;
            font-weight: 500;
        }
        .intro {
            font-size: 16px;
            color: #34495E;
            margin-bottom: 35px;
            line-height: 1.8;
        }

        .section {
            margin-bottom: 40px;
            border-left: 4px solid #2ECC71;
            padding-left: 20px;
            background: linear-gradient(90deg, rgba(46, 204, 113, 0.05) 0%, transparent 100%);
            border-radius: 0 8px 8px 0;
            padding: 20px;
            margin-left: -20px;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #2ECC71;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .section-title::before {
            content: '💨';
            margin-right: 10px;
            font-size: 24px;
        }
        .breathscape-section .section-title::before { content: '🌬️'; }
        .hardware-section .section-title::before { content: '⚡'; }
        .tips-section .section-title::before { content: '💡'; }
        .vision-section .section-title::before { content: '🎯'; }

        .item {
            margin-bottom: 25px;
            padding: 20px;
            background: #F8FFFE;
            border-radius: 12px;
            border: 1px solid #E8F6F3;
        }
        .item-title {
            font-size: 16px;
            font-weight: 600;
            color: #2C3E50;
            margin-bottom: 10px;
        }
        .item-content {
            font-size: 14px;
            color: #5D6D7E;
            line-height: 1.7;
        }

        .breathing-exercise {
            background: linear-gradient(135deg, #E8F8F5 0%, #D5F3ED 100%);
            border: 2px solid #2ECC71;
            border-radius: 16px;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
        }
        .breathing-title {
            font-size: 18px;
            font-weight: 600;
            color: #2ECC71;
            margin-bottom: 15px;
        }
        .breathing-steps {
            font-size: 14px;
            color: #2C3E50;
            line-height: 1.8;
        }

        .stats {
            display: flex;
            justify-content: space-around;
            background: #F7F9FC;
            padding: 25px;
            border-radius: 12px;
            margin: 30px 0;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #2ECC71;
        }
        .stat-label {
            font-size: 12px;
            color: #7F8C8D;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .cta {
            text-align: center;
            margin: 40px 0;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
            color: white;
            padding: 16px 32px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(46, 204, 113, 0.3);
        }
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(46, 204, 113, 0.4);
        }

        .footer {
            background: #2C3E50;
            color: #BDC3C7;
            padding: 30px 40px;
            text-align: center;
            font-size: 14px;
        }
        .footer-links {
            margin-bottom: 20px;
        }
        .footer-links a {
            color: #3498DB;
            text-decoration: none;
            margin: 0 15px;
        }
        .footer-note {
            font-size: 12px;
            opacity: 0.8;
            line-height: 1.6;
        }

        @media (max-width: 640px) {
            .wrapper { margin: 10px; border-radius: 12px; }
            .header, .content { padding: 25px 20px; }
            .section { margin-left: -10px; padding: 15px; }
            .stats { flex-direction: column; gap: 20px; }
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="header">
            <div class="logo">Halcytone</div>
            <div class="tagline">Your Journey to Mindful Breathing</div>
        </div>

        <div class="content">
            <div class="greeting">Hello, Breathing Explorer! 🌿</div>
            <div class="intro">
                Welcome to your {{ month_year }} breathing journey update. Discover new techniques,
                insights, and ways to enhance your mindful breathing practice.
            </div>

            {% if breathscape_updates %}
            <div class="section breathscape-section">
                <div class="section-title">Breathscape Updates</div>
                {% for item in breathscape_updates %}
                <div class="item">
                    <div class="item-title">{{ item.title }}</div>
                    <div class="item-content">{{ item.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <div class="breathing-exercise">
                <div class="breathing-title">🧘‍♀️ Quick Breathing Exercise</div>
                <div class="breathing-steps">
                    <strong>4-7-8 Technique:</strong><br>
                    Inhale for 4 counts → Hold for 7 counts → Exhale for 8 counts<br>
                    <em>Repeat 3-4 times for instant calm</em>
                </div>
            </div>

            {% if hardware_updates %}
            <div class="section hardware-section">
                <div class="section-title">Tech & Innovation</div>
                {% for item in hardware_updates %}
                <div class="item">
                    <div class="item-title">{{ item.title }}</div>
                    <div class="item-content">{{ item.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if tips %}
            <div class="section tips-section">
                <div class="section-title">Mindful Moments</div>
                {% for tip in tips %}
                <div class="item">
                    <div class="item-title">{{ tip.title }}</div>
                    <div class="item-content">{{ tip.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if stats %}
            <div class="stats">
                {% for stat in stats %}
                <div class="stat">
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if vision %}
            <div class="section vision-section">
                <div class="section-title">Our Shared Vision</div>
                <div class="item">
                    <div class="item-content">{{ vision }}</div>
                </div>
            </div>
            {% endif %}

            {% if call_to_action %}
            <div class="cta">
                <a href="{{ call_to_action.link }}" class="cta-button">
                    {{ call_to_action.button_text }}
                </a>
                <div style="margin-top: 15px; font-size: 14px; color: #7F8C8D;">
                    {{ call_to_action.text }}
                </div>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <div class="footer-links">
                <a href="{{ website_url }}">Visit Website</a>
                <a href="{{ website_url }}/app">Download App</a>
                <a href="{{ website_url }}/community">Join Community</a>
            </div>
            <div class="footer-note">
                You're receiving this because you're part of our breathing community.<br>
                <a href="#" style="color: #3498DB;">Unsubscribe</a> |
                <a href="#" style="color: #3498DB;">Update Preferences</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

BREATHSCAPE_WEB_TEMPLATE = """
# {{ title }}

*Published {{ published_at | default('today') }} • {{ reading_time | default(5) }} min read*

{{ excerpt }}

---

## 🌬️ Breathing Into Wellness

{{ intro_content }}

{% if breathscape_updates %}
## 🌱 Latest in Breathscape Technology

{% for update in breathscape_updates %}
### {{ update.title }}

{{ update.content }}

{% if update.benefits %}
**Key Benefits:**
{% for benefit in update.benefits %}
- {{ benefit }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if hardware_updates %}
## ⚡ Hardware & Innovation Updates

{% for update in hardware_updates %}
### {{ update.title }}

{{ update.content }}

{% if update.technical_specs %}
**Technical Highlights:**
{% for spec in update.technical_specs %}
- {{ spec }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if tips_and_techniques %}
## 💡 Mindful Breathing Techniques

{% for tip in tips_and_techniques %}
### {{ tip.title }}

{{ tip.content }}

{% if tip.steps %}
**How to Practice:**
{% for step in tip.steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
{% endif %}

> 💭 **Remember:** Consistency is more important than perfection. Start with just 2-3 minutes daily.

---
{% endfor %}
{% endif %}

## 🧘‍♀️ Community Spotlight

{% if community_stories %}
{% for story in community_stories %}
> *"{{ story.quote }}"*
>
> — {{ story.author }}, {{ story.location }}

{% endfor %}
{% endif %}

## 📊 This Month's Breathing Stats

{% if stats %}
<div class="stats-grid">
{% for stat in stats %}
<div class="stat-card">
  <h3>{{ stat.value }}</h3>
  <p>{{ stat.label }}</p>
</div>
{% endfor %}
</div>
{% endif %}

---

## 🎯 Looking Ahead

{{ vision_content | default("Together, we're building a world where mindful breathing is accessible to everyone. Every breath is a step toward better health, reduced stress, and enhanced well-being.") }}

### Join Our Growing Community

- **Download the Halcytone App**: Track your breathing patterns and progress
- **Join our Discord**: Connect with fellow breathing enthusiasts
- **Follow our Research**: Stay updated on the latest breathing science

---

*Want to dive deeper? Explore our [complete breathing guide]({{ website_url }}/guide) or [join our next virtual breathing session]({{ website_url }}/sessions).*

**Tags:** {{ tags | join(', ') | default('breathing, wellness, mindfulness, health') }}
"""

BREATHSCAPE_SOCIAL_TEMPLATES = {
    'twitter': {
        'breathing_tip': "🌬️ Breathe Better Today:\n\n{{ tip }}\n\nTry it for 2 minutes and feel the difference! #Breathscape #Mindfulness #Wellness",
        'tech_update': "⚡ Exciting update in breathing tech:\n\n{{ update }}\n\nThe future of wellness is here! 🚀 #BreathingTech #Innovation #Halcytone",
        'community': "💚 Amazing feedback from our community:\n\n\"{{ quote }}\"\n\nYour breathing journey matters! Share yours below 👇 #BreathingCommunity",
        'science': "🧬 Breathing Science:\n\n{{ fact }}\n\nYour breath is more powerful than you think! #BreathingScience #Wellness"
    },
    'linkedin': {
        'professional': "The Impact of Mindful Breathing in the Workplace\n\n{{ content }}\n\nReady to bring wellness to your team? Learn more about our corporate breathing programs.\n\n#WorkplaceWellness #Mindfulness #CorporateHealth #Productivity",
        'research': "Latest Research in Breathing Technology\n\n{{ findings }}\n\nAt Halcytone, we're committed to evidence-based wellness solutions.\n\n#HealthTech #Research #Innovation #DigitalHealth",
        'thought_leadership': "Rethinking Wellness: Why Breathing is the Foundation\n\n{{ insights }}\n\nWhat's your take on integrating breathing practices in daily life?\n\n#WellnessLeadership #HealthInnovation #Mindfulness"
    },
    'instagram': {
        'visual_guide': "✨ Today's Breathing Guide ✨\n\n{{ exercise_name }}\n\n{{ steps }}\n\n💫 Tag a friend who needs this calm moment!\n\n#Breathscape #MindfulBreathing #SelfCare #WellnessJourney #Mindfulness #InnerPeace",
        'behind_scenes': "Behind the scenes at Halcytone 🌿\n\n{{ story }}\n\n#TeamHalcytone #BreathingTech #WellnessInnovation #StartupLife",
        'user_spotlight': "Community Spotlight 🌟\n\n{{ user_story }}\n\nTag us in your breathing journey! We love seeing your progress 💚\n\n#BreathingCommunity #Transformation #WellnessWins"
    },
    'facebook': {
        'educational': "Understanding the Science of Breathing 🧬\n\n{{ educational_content }}\n\nDid you know that controlled breathing can:\n{{ benefits }}\n\nShare this with someone who might benefit from better breathing!\n\n#BreathingScience #Wellness #HealthEducation",
        'community_event': "Join Our Virtual Breathing Session! 🧘‍♀️\n\n{{ event_details }}\n\nFree for all community members. Bring a friend!\n\nWho's ready to breathe better together?\n\n#CommunityEvent #MindfulBreathing #WellnessCommunity"
    }
}

def get_breathscape_template_for_content(content_type, theme=None):
    """
    Get appropriate Breathscape template based on content type and theme

    Args:
        content_type: 'email', 'web', or 'social'
        theme: Optional theme for social content

    Returns:
        Template string or template dict for social
    """
    if content_type == 'email':
        return BREATHSCAPE_EMAIL_TEMPLATE
    elif content_type == 'web':
        return BREATHSCAPE_WEB_TEMPLATE
    elif content_type == 'social':
        return BREATHSCAPE_SOCIAL_TEMPLATES
    else:
        return None

# Sprint 3: Session Summary Templates for Halcytone Live Support

BREATHING_SESSION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ session_title }} - Session Summary</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #2C3E50;
            background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
            padding: 20px 0;
        }
        .session-wrapper {
            max-width: 720px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(66, 165, 245, 0.2);
            overflow: hidden;
        }
        .session-header {
            background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .session-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 20px;
        }
        .session-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .session-meta {
            font-size: 16px;
            opacity: 0.95;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #F8F9FA;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: #1E88E5;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 12px;
            text-transform: uppercase;
            color: #7F8C8D;
            letter-spacing: 0.5px;
        }
        .techniques-section {
            padding: 30px;
            background: white;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #2C3E50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #E3F2FD;
        }
        .technique-item {
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #F8F9FA;
            border-radius: 8px;
            transition: transform 0.2s;
        }
        .technique-item:hover {
            transform: translateX(5px);
            background: #E3F2FD;
        }
        .technique-icon {
            font-size: 24px;
            margin-right: 15px;
        }
        .technique-name {
            font-weight: 500;
            color: #2C3E50;
        }
        .achievements-section {
            padding: 30px;
            background: #FFF8E1;
        }
        .achievement-item {
            display: flex;
            align-items: start;
            margin: 15px 0;
        }
        .achievement-icon {
            font-size: 20px;
            margin-right: 12px;
            color: #FFA726;
        }
        .achievement-text {
            flex: 1;
            color: #5D4037;
            font-size: 15px;
        }
        .hrv-chart {
            padding: 30px;
            background: white;
            text-align: center;
        }
        .hrv-improvement {
            font-size: 48px;
            font-weight: 700;
            color: #4CAF50;
            margin: 20px 0;
        }
        .hrv-label {
            font-size: 14px;
            color: #7F8C8D;
            margin-bottom: 20px;
        }
        .participant-feedback {
            padding: 30px;
            background: #F3E5F5;
        }
        .feedback-quote {
            font-style: italic;
            font-size: 16px;
            color: #6A1B9A;
            padding: 20px;
            border-left: 4px solid #9C27B0;
            margin: 15px 0;
            background: white;
            border-radius: 0 8px 8px 0;
        }
        .session-footer {
            background: #263238;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .next-session {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .cta-button {
            display: inline-block;
            background: #42A5F5;
            color: white;
            padding: 14px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            margin: 20px 0;
            transition: background 0.3s;
        }
        .cta-button:hover {
            background: #1E88E5;
        }
    </style>
</head>
<body>
    <div class="session-wrapper">
        <div class="session-header">
            <div class="session-badge">{{ session_type | upper }} SESSION</div>
            <div class="session-title">{{ session_title }}</div>
            <div class="session-meta">
                {{ session_date }} • {{ duration_minutes }} minutes • {{ participant_count }} participants{% if instructor_name %} • Led by {{ instructor_name }}{% endif %}
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ participant_count }}</div>
                <div class="metric-label">Participants</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ duration_minutes }}</div>
                <div class="metric-label">Minutes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ techniques_count }}</div>
                <div class="metric-label">Techniques</div>
            </div>
            {% if quality_score %}
            <div class="metric-card">
                <div class="metric-value">{{ quality_score }}/5</div>
                <div class="metric-label">Quality Score</div>
            </div>
            {% endif %}
        </div>

        {% if breathing_techniques %}
        <div class="techniques-section">
            <div class="section-title">🌬️ Breathing Techniques Practiced</div>
            {% for technique in breathing_techniques %}
            <div class="technique-item">
                <div class="technique-icon">{{ technique.icon | default('🧘') }}</div>
                <div class="technique-name">{{ technique.name }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if average_hrv_improvement %}
        <div class="hrv-chart">
            <div class="section-title">💗 HRV Performance</div>
            <div class="hrv-improvement">+{{ average_hrv_improvement }}%</div>
            <div class="hrv-label">Average HRV Improvement</div>
            <p style="color: #7F8C8D; font-size: 14px;">
                Excellent progress! Your heart rate variability shows improved autonomic balance.
            </p>
        </div>
        {% endif %}

        {% if key_achievements %}
        <div class="achievements-section">
            <div class="section-title">🏆 Session Achievements</div>
            {% for achievement in key_achievements %}
            <div class="achievement-item">
                <div class="achievement-icon">⭐</div>
                <div class="achievement-text">{{ achievement }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if participant_feedback %}
        <div class="participant-feedback">
            <div class="section-title">💬 Participant Highlights</div>
            {% for feedback in participant_feedback %}
            <div class="feedback-quote">
                "{{ feedback.quote }}"
                <div style="text-align: right; margin-top: 10px; font-size: 14px; font-style: normal;">
                    — {{ feedback.author | default('Anonymous') }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="session-footer">
            {% if next_session %}
            <div class="next-session">
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 10px;">
                    📅 Next Session
                </div>
                <div style="font-size: 16px; opacity: 0.9;">
                    {{ next_session.title }}<br>
                    {{ next_session.date }} at {{ next_session.time }}
                </div>
            </div>
            {% endif %}

            <a href="{{ join_link | default('#') }}" class="cta-button">
                Join Next Session
            </a>

            <div style="margin-top: 30px; font-size: 14px; opacity: 0.8;">
                Thank you for being part of our breathing community!<br>
                Together, we're creating moments of mindfulness.
            </div>
        </div>
    </div>
</body>
</html>
"""

BREATHING_SESSION_WEB_TEMPLATE = """
<article class="session-summary">
    <header class="session-header">
        <span class="session-type-badge">{{ session_type }}</span>
        <h1>{{ session_title }}</h1>
        <div class="session-meta">
            <time datetime="{{ session_date }}">{{ session_date }}</time>
            <span class="separator">•</span>
            <span class="duration">{{ duration_minutes }} minutes</span>
            <span class="separator">•</span>
            <span class="participants">{{ participant_count }} participants</span>
            {% if instructor_name %}
            <span class="separator">•</span>
            <span class="instructor">Led by {{ instructor_name }}</span>
            {% endif %}
        </div>
    </header>

    <section class="session-metrics">
        <h2>Session Overview</h2>
        <div class="metrics-grid">
            <div class="metric">
                <span class="metric-value">{{ participant_count }}</span>
                <span class="metric-label">Total Participants</span>
            </div>
            <div class="metric">
                <span class="metric-value">{{ duration_minutes }}min</span>
                <span class="metric-label">Session Duration</span>
            </div>
            {% if average_hrv_improvement %}
            <div class="metric highlight">
                <span class="metric-value">+{{ average_hrv_improvement }}%</span>
                <span class="metric-label">Avg HRV Improvement</span>
            </div>
            {% endif %}
            {% if quality_score %}
            <div class="metric">
                <span class="metric-value">{{ quality_score }}/5</span>
                <span class="metric-label">Quality Score</span>
            </div>
            {% endif %}
        </div>
    </section>

    {% if breathing_techniques %}
    <section class="techniques-practiced">
        <h2>Breathing Techniques</h2>
        <ul class="techniques-list">
            {% for technique in breathing_techniques %}
            <li class="technique">
                <span class="technique-name">{{ technique }}</span>
            </li>
            {% endfor %}
        </ul>
    </section>
    {% endif %}

    {% if key_achievements %}
    <section class="achievements">
        <h2>Key Achievements</h2>
        <ul class="achievements-list">
            {% for achievement in key_achievements %}
            <li class="achievement-item">{{ achievement }}</li>
            {% endfor %}
        </ul>
    </section>
    {% endif %}

    {% if participant_feedback %}
    <section class="feedback">
        <h2>What Participants Said</h2>
        <div class="feedback-grid">
            {% for feedback in participant_feedback %}
            <blockquote class="feedback-item">
                <p>{{ feedback.quote }}</p>
                <cite>— {{ feedback.author | default('Participant') }}</cite>
            </blockquote>
            {% endfor %}
        </div>
    </section>
    {% endif %}

    <footer class="session-footer">
        <div class="next-steps">
            <h3>Continue Your Journey</h3>
            <p>Join our next session to continue improving your breathing practice and wellness.</p>
            <a href="{{ join_link }}" class="cta-button">Join Next Session</a>
        </div>
    </footer>
</article>
"""

BREATHING_SESSION_SOCIAL_TEMPLATES = {
    'twitter': """🧘 Session Complete: {{ session_title }}

✅ {{ participant_count }} breathers joined
📈 Avg HRV improved by {{ average_hrv_improvement }}%
⏱️ {{ duration_minutes }} minutes of mindful breathing

{% if key_achievements %}{{ key_achievements[0] }}{% endif %}

Join us next time! #Breathwork #Mindfulness #Wellness""",

    'linkedin': """🌟 Breathing Session Summary: {{ session_title }}

Today's {{ session_type }} session brought together {{ participant_count }} participants for {{ duration_minutes }} minutes of guided breathing practice.

Key Metrics:
• Average HRV Improvement: +{{ average_hrv_improvement }}%
• Techniques Practiced: {% for t in breathing_techniques %}{{ t }}{% if not loop.last %}, {% endif %}{% endfor %}
• Session Quality Score: {{ quality_score }}/5

{% if key_achievements %}
Notable Achievements:
{% for achievement in key_achievements[:3] %}
• {{ achievement }}
{% endfor %}
{% endif %}

The power of conscious breathing continues to transform lives. Join our next session to experience the benefits yourself.

#BreathingTechniques #CorporateWellness #Mindfulness #StressManagement #Wellness""",

    'facebook': """🧘‍♀️ Today's Breathing Session Was Amazing!

We just completed "{{ session_title }}" with {{ participant_count }} wonderful participants!

📊 Session Highlights:
• Duration: {{ duration_minutes }} minutes
• Average HRV Improvement: +{{ average_hrv_improvement }}%
• Techniques: {% for t in breathing_techniques %}{{ t }}{% if not loop.last %}, {% endif %}{% endfor %}

{% if key_achievements %}
🏆 What We Achieved Together:
{% for achievement in key_achievements %}
✨ {{ achievement }}
{% endfor %}
{% endif %}

{% if participant_feedback %}
💬 "{{ participant_feedback[0].quote }}" - {{ participant_feedback[0].author }}
{% endif %}

Every breath counts, and together we're building a healthier, more mindful community.

Ready to join us? Our next session is coming soon! Click below to reserve your spot.

#BreathingCommunity #Mindfulness #HealthyLiving #Wellness"""
}


def get_breathscape_content_themes():
    """Get available content themes for Breathscape"""
    return {
        'breathing_techniques': {
            'name': 'Breathing Techniques',
            'description': 'Practical breathing exercises and methods',
            'emojis': ['🌬️', '🧘‍♀️', '💨', '🌀']
        },
        'technology_updates': {
            'name': 'Technology Updates',
            'description': 'Latest in breathing technology and innovation',
            'emojis': ['⚡', '🔬', '📱', '🚀']
        },
        'wellness_science': {
            'name': 'Wellness Science',
            'description': 'Research and science behind breathing wellness',
            'emojis': ['🧬', '📊', '🔍', '📚']
        },
        'community_stories': {
            'name': 'Community Stories',
            'description': 'User experiences and community highlights',
            'emojis': ['💚', '🌟', '🤝', '💬']
        },
        'mindfulness_moments': {
            'name': 'Mindfulness Moments',
            'description': 'Daily mindfulness and meditation content',
            'emojis': ['🧘', '☮️', '🌸', '✨']
        }
    }